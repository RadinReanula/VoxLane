from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from voice_agent.models import (
    Menu,
    MenuItem,
    Order,
    OrderLine,
    OrderLineInput,
    SelectedModifier,
    now_utc,
)

CENT = Decimal("0.01")


class DomainValidationError(ValueError):
    """A safe validation failure that can be returned to a caller."""


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def get_item(menu: Menu, item_id: str) -> MenuItem:
    item = next((item for item in menu.items if item.id == item_id), None)
    if item is None:
        raise DomainValidationError(f"Unknown menu item: {item_id}")
    if not item.available:
        raise DomainValidationError(f"{item.name} is unavailable")
    return item


def calculate_line(menu: Menu, line: OrderLineInput, line_id: UUID | None = None) -> OrderLine:
    item = get_item(menu, line.item_id)
    choices_by_group: dict[str, list[SelectedModifier]] = {}
    for modifier in line.modifiers:
        choices_by_group.setdefault(modifier.group_id, []).append(modifier)

    unit_price = item.base_price
    known_groups = {group.id for group in item.modifier_groups}
    unknown_groups = choices_by_group.keys() - known_groups
    if unknown_groups:
        raise DomainValidationError(f"Unknown modifier group: {sorted(unknown_groups)[0]}")

    for group in item.modifier_groups:
        selected_entries = choices_by_group.get(group.id, [])
        if not group.min_selections <= len(selected_entries) <= group.max_selections:
            raise DomainValidationError(
                f"{group.name} requires {group.min_selections}-{group.max_selections} choices"
            )
        choice_map = {choice.id: choice for choice in group.choices}
        if len({entry.choice_id for entry in selected_entries}) != len(selected_entries):
            raise DomainValidationError(f"Duplicate selection in {group.name}")
        for entry in selected_entries:
            choice = choice_map.get(entry.choice_id)
            if choice is None:
                raise DomainValidationError(f"Unknown choice {entry.choice_id} for {group.name}")
            unit_price += choice.price_delta

    unit_price = money(unit_price)
    values: dict[str, object] = {
        **line.model_dump(),
        "item_name": item.name,
        "unit_price": unit_price,
        "line_total": money(unit_price * line.quantity),
    }
    if line_id is not None:
        values["id"] = line_id
    return OrderLine.model_validate(values)


def recalculate(order: Order, tax_rate: Decimal) -> Order:
    subtotal = money(sum((line.line_total for line in order.lines), Decimal("0")))
    tax = money(subtotal * tax_rate)
    return order.model_copy(
        update={
            "subtotal": subtotal,
            "tax": tax,
            "total": money(subtotal + tax),
            "revision": order.revision + 1,
            "updated_at": now_utc(),
        }
    )


def add_line(order: Order, menu: Menu, line: OrderLineInput, tax_rate: Decimal) -> Order:
    calculated = calculate_line(menu, line)
    return recalculate(order.model_copy(update={"lines": [*order.lines, calculated]}), tax_rate)


def replace_line(
    order: Order,
    menu: Menu,
    line_id: UUID,
    replacement: OrderLineInput,
    tax_rate: Decimal,
) -> Order:
    if not any(line.id == line_id for line in order.lines):
        raise DomainValidationError(f"Unknown order line: {line_id}")
    calculated = calculate_line(menu, replacement, line_id)
    lines = [calculated if line.id == line_id else line for line in order.lines]
    return recalculate(order.model_copy(update={"lines": lines}), tax_rate)


def remove_line(order: Order, line_id: UUID, tax_rate: Decimal) -> Order:
    lines = [line for line in order.lines if line.id != line_id]
    if len(lines) == len(order.lines):
        raise DomainValidationError(f"Unknown order line: {line_id}")
    return recalculate(order.model_copy(update={"lines": lines}), tax_rate)
