from decimal import Decimal

import pytest

from voice_agent.domain import DomainValidationError, add_line, replace_line
from voice_agent.models import Order, OrderLineInput, SelectedModifier
from voice_agent.repository import sample_menu


def test_calculates_modifier_quantity_and_tax() -> None:
    order = Order(session_id="00000000-0000-0000-0000-000000000001")
    line = OrderLineInput(
        item_id="classic-burger",
        quantity=2,
        modifiers=[SelectedModifier(group_id="cheese", choice_id="cheddar")],
    )

    result = add_line(order, sample_menu(), line, Decimal("0.10"))

    assert result.subtotal == Decimal("17.00")
    assert result.tax == Decimal("1.70")
    assert result.total == Decimal("18.70")


def test_rejects_missing_required_modifier() -> None:
    order = Order(session_id="00000000-0000-0000-0000-000000000001")

    with pytest.raises(DomainValidationError, match="Size requires"):
        add_line(
            order,
            sample_menu(),
            OrderLineInput(item_id="fries"),
            Decimal("0"),
        )


def test_replaces_line_for_correction() -> None:
    menu = sample_menu()
    order = add_line(
        Order(session_id="00000000-0000-0000-0000-000000000001"),
        menu,
        OrderLineInput(item_id="cola"),
        Decimal("0"),
    )

    corrected = replace_line(
        order,
        menu,
        order.lines[0].id,
        OrderLineInput(
            item_id="fries",
            modifiers=[SelectedModifier(group_id="size", choice_id="large")],
        ),
        Decimal("0"),
    )

    assert corrected.lines[0].id == order.lines[0].id
    assert corrected.lines[0].item_name == "Fries"
    assert corrected.total == Decimal("4.25")
