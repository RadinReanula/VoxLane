from __future__ import annotations

import asyncio
import re
import time
from collections import defaultdict
from decimal import Decimal
from uuid import UUID

import structlog
from opentelemetry import trace

from voice_agent.domain import DomainValidationError, add_line, remove_line, replace_line
from voice_agent.models import (
    ConversationSession,
    HandoffEvent,
    InterruptedEvent,
    LatencySpan,
    Menu,
    Order,
    OrderEvent,
    OrderLineInput,
    ProviderFailure,
    SelectedModifier,
    SessionStatus,
    TextTurnResponse,
    ToolEvent,
    Turn,
    TurnRole,
)
from voice_agent.providers import LanguageProvider, ProviderError, redact
from voice_agent.repository import Repository

log = structlog.get_logger()
tracer = trace.get_tracer(__name__)


class StaleGenerationError(RuntimeError):
    pass


class ConversationOrchestrator:
    def __init__(
        self,
        repository: Repository,
        language: LanguageProvider,
        tax_rate: Decimal,
        redact_transcripts: bool,
    ) -> None:
        self.repository = repository
        self.language = language
        self.tax_rate = tax_rate
        self.redact_transcripts = redact_transcripts
        self._locks: defaultdict[UUID, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._active_tasks: dict[UUID, asyncio.Task[str]] = {}

    async def start_session(self) -> tuple[ConversationSession, Order]:
        order = Order(session_id=UUID(int=0))
        session = ConversationSession(order_id=order.id)
        order = order.model_copy(update={"session_id": session.id})
        await self.repository.save_order(order)
        await self.repository.save_session(session)
        return session, order

    async def interrupt(self, session_id: UUID) -> ConversationSession:
        async with self._locks[session_id]:
            session = await self.repository.get_session(session_id)
            previous = session.generation_id
            session = session.model_copy(
                update={"generation_id": previous + 1, "updated_at": session.updated_at}
            )
            task = self._active_tasks.pop(session_id, None)
            await self.repository.save_session(session)
            await self.repository.append_event(
                InterruptedEvent(
                    session_id=session_id,
                    generation_id=session.generation_id,
                    previous_generation_id=previous,
                )
            )
            if task and not task.done():
                task.cancel()
            return session

    async def request_human(
        self,
        session_id: UUID,
        reason: str = "guest_request",
    ) -> ConversationSession:
        async with self._locks[session_id]:
            session = await self.repository.get_session(session_id)
            if session.status is SessionStatus.CLOSED:
                raise DomainValidationError("Session is closed")
            task = self._active_tasks.pop(session_id, None)
            session = session.model_copy(
                update={
                    "status": SessionStatus.HUMAN_HELP,
                    "generation_id": session.generation_id + 1,
                }
            )
            await self.repository.save_session(session)
            await self.repository.append_event(
                HandoffEvent(
                    session_id=session_id,
                    generation_id=session.generation_id,
                    reason=reason,
                )
            )
            if task and not task.done():
                task.cancel()
            return session

    async def _mark_human_help(
        self,
        session_id: UUID,
        generation: int,
        reason: str,
    ) -> None:
        async with self._locks[session_id]:
            session = await self.repository.get_session(session_id)
            session = session.model_copy(update={"status": SessionStatus.HUMAN_HELP})
            await self.repository.save_session(session)
            await self.repository.append_event(
                HandoffEvent(
                    session_id=session_id,
                    generation_id=generation,
                    reason=reason,
                )
            )

    async def resume(self, session_id: UUID) -> ConversationSession:
        async with self._locks[session_id]:
            session = await self.repository.get_session(session_id)
            if session.status is SessionStatus.CLOSED:
                raise DomainValidationError("Session is closed")
            if session.status is SessionStatus.CONFIRMED:
                return session
            session = session.model_copy(update={"status": SessionStatus.ACTIVE})
            await self.repository.save_session(session)
            return session

    async def turn(self, session_id: UUID, raw_text: str) -> TextTurnResponse:
        async with self._locks[session_id]:
            session = await self.repository.get_session(session_id)
            if session.status is not SessionStatus.ACTIVE:
                raise DomainValidationError("Session is not active")
            generation = session.generation_id + 1
            session = session.model_copy(update={"generation_id": generation})
            await self.repository.save_session(session)

        text = redact(raw_text) if self.redact_transcripts else raw_text
        await self.repository.save_turn(
            Turn(
                session_id=session_id,
                generation_id=generation,
                role=TurnRole.USER,
                text=text,
            )
        )
        order = await self.repository.get_order(session.order_id)
        menu = await self.repository.get_menu()
        started = time.perf_counter()

        with tracer.start_as_current_span("conversation.turn"):
            try:
                reply, order = await self._dispatch(session, order, menu, raw_text, generation)
            except asyncio.CancelledError:
                latest = await self.repository.get_session(session_id)
                if latest.generation_id != generation:
                    raise StaleGenerationError(
                        "Response was cancelled by a newer generation"
                    ) from None
                raise
            except ProviderError as error:
                await self.repository.append_event(
                    ProviderFailure(
                        session_id=session_id,
                        generation_id=generation,
                        provider=error.provider,
                        operation="respond",
                        error_code=error.code,
                        retryable=error.retryable,
                        redacted_message="Provider request failed",
                    )
                )
                reply = "I’m having trouble with that request. Please try again."
            finally:
                await self.repository.append_event(
                    LatencySpan(
                        session_id=session_id,
                        generation_id=generation,
                        operation="conversation.turn",
                        provider=self.language.name,
                        duration_ms=(time.perf_counter() - started) * 1000,
                    )
                )

        latest = await self.repository.get_session(session_id)
        if latest.generation_id != generation:
            raise StaleGenerationError("Response belongs to a stale generation")
        await self.repository.save_turn(
            Turn(
                session_id=session_id,
                generation_id=generation,
                role=TurnRole.ASSISTANT,
                text=reply,
            )
        )
        return TextTurnResponse(
            session_id=session_id,
            generation_id=generation,
            reply=reply,
            order=order,
        )

    async def _dispatch(
        self,
        session: ConversationSession,
        order: Order,
        menu: Menu,
        text: str,
        generation: int,
    ) -> tuple[str, Order]:
        normalized = " ".join(text.lower().split())
        if any(
            phrase in normalized
            for phrase in (
                "human",
                "help",
                "operator",
                "speak to someone",
                "speak to a person",
                "talk to a person",
                "real person",
            )
        ):
            await self._mark_human_help(session.id, generation, reason="guest_utterance")
            return (
                "A team member is joining you now. Please stay at the speaker.",
                order,
            )

        add_match = re.match(r"(?:add|i(?:'d)? like|order)\s+(?:(\d+)\s+)?(.+)", normalized)
        if add_match:
            quantity = int(add_match.group(1) or "1")
            line_input = self._line_from_phrase(menu, add_match.group(2), quantity)
            order = add_line(order, menu, line_input, self.tax_rate)
            await self._record_order(session.id, generation, "add_line", order)
            return f"Added {quantity} {order.lines[-1].item_name}. Total is ${order.total}.", order

        remove_match = re.match(r"(?:remove|delete)\s+(.+)", normalized)
        if remove_match:
            target = remove_match.group(1)
            line = next(
                (entry for entry in reversed(order.lines) if entry.item_name.lower() in target),
                None,
            )
            if line is None:
                raise DomainValidationError(f"No matching order line for: {target}")
            order = remove_line(order, line.id, self.tax_rate)
            await self._record_order(session.id, generation, "remove_line", order)
            return f"Removed {line.item_name}. Total is ${order.total}.", order

        change_match = re.match(r"(?:change|replace)\s+(.+?)\s+(?:to|with)\s+(.+)", normalized)
        if change_match:
            target, replacement = change_match.groups()
            line = next(
                (entry for entry in reversed(order.lines) if entry.item_name.lower() in target),
                None,
            )
            if line is None:
                raise DomainValidationError(f"No matching order line for: {target}")
            replacement_input = self._line_from_phrase(menu, replacement, line.quantity)
            order = replace_line(order, menu, line.id, replacement_input, self.tax_rate)
            await self._record_order(session.id, generation, "replace_line", order)
            return f"Changed the order to {replacement}. Total is ${order.total}.", order

        task = asyncio.create_task(self.language.respond(text))
        self._active_tasks[session.id] = task
        try:
            return await task, order
        finally:
            if self._active_tasks.get(session.id) is task:
                self._active_tasks.pop(session.id, None)

    def _line_from_phrase(self, menu: Menu, phrase: str, quantity: int) -> OrderLineInput:
        item = next((item for item in menu.items if item.name.lower() in phrase), None)
        if item is None:
            raise DomainValidationError(f"No menu item found in: {phrase}")
        modifiers: list[SelectedModifier] = []
        for group in item.modifier_groups:
            selected = [choice for choice in group.choices if choice.name.lower() in phrase]
            if not selected and group.min_selections == 1 and len(group.choices) == 1:
                selected = group.choices
            modifiers.extend(
                SelectedModifier(group_id=group.id, choice_id=choice.id) for choice in selected
            )
        return OrderLineInput(item_id=item.id, quantity=quantity, modifiers=modifiers)

    async def _record_order(
        self,
        session_id: UUID,
        generation: int,
        operation: str,
        order: Order,
    ) -> None:
        await self.repository.save_order(order)
        await self.repository.append_event(
            OrderEvent(
                session_id=session_id,
                generation_id=generation,
                operation=operation,
                order=order,
            )
        )
        await self.repository.append_event(
            ToolEvent(
                session_id=session_id,
                generation_id=generation,
                tool_name=operation,
                arguments={},
                success=True,
            )
        )
