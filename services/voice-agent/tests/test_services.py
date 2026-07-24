import asyncio
from collections.abc import AsyncIterator
from decimal import Decimal
from pathlib import Path

import pytest

from voice_agent.models import EventType, OrderLineInput
from voice_agent.orchestrator import ConversationOrchestrator, StaleGenerationError
from voice_agent.providers import MockPos, ProviderError
from voice_agent.repository import Repository, seed


@pytest.fixture
async def repository(tmp_path: Path) -> AsyncIterator[Repository]:
    repository = Repository(f"sqlite+aiosqlite:///{tmp_path}/test.db")
    await repository.bootstrap()
    await seed(repository)
    yield repository
    await repository.close()


@pytest.mark.asyncio
async def test_pos_is_idempotent(repository: Repository) -> None:
    orchestrator = ConversationOrchestrator(repository, FailingProvider(), Decimal("0"), False)
    session, order = await orchestrator.start_session()
    menu = await repository.get_menu()
    from voice_agent.domain import add_line

    order = add_line(order, menu, OrderLineInput(item_id="cola"), Decimal("0"))
    await repository.save_order(order)
    pos = MockPos(repository)

    first = await pos.submit(order, "same-request-key")
    second = await pos.submit(order, "same-request-key")

    assert first == second
    assert first.pos_order_id == second.pos_order_id
    assert session.order_id == order.id


class SlowProvider:
    name = "slow"

    async def respond(self, prompt: str) -> str:
        await asyncio.sleep(5)
        return prompt


@pytest.mark.asyncio
async def test_interruption_cancels_active_generation(repository: Repository) -> None:
    orchestrator = ConversationOrchestrator(repository, SlowProvider(), Decimal("0"), False)
    session, _ = await orchestrator.start_session()
    turn = asyncio.create_task(orchestrator.turn(session.id, "tell me something"))
    await asyncio.sleep(0.05)

    interrupted = await orchestrator.interrupt(session.id)

    with pytest.raises(StaleGenerationError):
        await turn
    assert interrupted.generation_id == 2
    events = await repository.list_events(session.id)
    assert any(event["event_type"] == EventType.INTERRUPTED for event in events)


class FailingProvider:
    name = "failing"

    async def respond(self, prompt: str) -> str:
        raise ProviderError("failing", "down", True, "secret upstream detail")


@pytest.mark.asyncio
async def test_provider_failure_is_safe_and_recorded(repository: Repository) -> None:
    orchestrator = ConversationOrchestrator(repository, FailingProvider(), Decimal("0"), False)
    session, _ = await orchestrator.start_session()

    response = await orchestrator.turn(session.id, "unknown request")

    assert "try again" in response.reply
    events = await repository.list_events(session.id)
    failure = next(event for event in events if event["event_type"] == EventType.PROVIDER_FAILURE)
    assert failure["redacted_message"] == "Provider request failed"


@pytest.mark.asyncio
async def test_human_handoff_and_resume(repository: Repository) -> None:
    orchestrator = ConversationOrchestrator(repository, FailingProvider(), Decimal("0"), False)
    session, _ = await orchestrator.start_session()

    handed = await orchestrator.request_human(session.id, reason="console")
    assert handed.status.value == "human_help"
    events = await repository.list_events(session.id)
    assert any(event["event_type"] == EventType.HANDOFF for event in events)

    resumed = await orchestrator.resume(session.id)
    assert resumed.status.value == "active"


@pytest.mark.asyncio
async def test_help_utterance_triggers_handoff(repository: Repository) -> None:
    orchestrator = ConversationOrchestrator(repository, FailingProvider(), Decimal("0"), False)
    session, _ = await orchestrator.start_session()

    response = await orchestrator.turn(session.id, "I need to speak to a person")
    latest = await repository.get_session(session.id)

    assert "team member" in response.reply.lower()
    assert latest.status.value == "human_help"


@pytest.mark.asyncio
async def test_events_are_sequenced_and_reconnectable(repository: Repository) -> None:
    orchestrator = ConversationOrchestrator(repository, FailingProvider(), Decimal("0"), False)
    session, _ = await orchestrator.start_session()
    await orchestrator.turn(session.id, "add 1 cola")
    await orchestrator.interrupt(session.id)

    events = await repository.list_events(session.id)
    sequences = [event["sequence"] for event in events]
    assert sequences == sorted(sequences)
    assert sequences == list(range(1, len(sequences) + 1))

    after_first = await repository.list_events(session.id, after_sequence=sequences[0])
    assert all(event["sequence"] > sequences[0] for event in after_first)

    snapshot = await repository.get_session_snapshot(session.id)
    assert snapshot["session"]["id"] == str(session.id)
    assert snapshot["latest_sequence"] == sequences[-1]


@pytest.mark.asyncio
async def test_transcript_redaction(repository: Repository) -> None:
    orchestrator = ConversationOrchestrator(repository, FailingProvider(), Decimal("0"), True)
    session, _ = await orchestrator.start_session()
    await orchestrator.turn(session.id, "my card is 4111 1111 1111 1111 and email test@example.com")

    turns = []
    # Document store uses kind/id; inspect via event absence of raw PAN in saved turn body.
    from sqlalchemy import select

    from voice_agent.repository import Document

    async with repository.sessions() as db:
        rows = (
            await db.scalars(select(Document).where(Document.kind == "turn"))
        ).all()
        turns = [row.body for row in rows if row.body.get("session_id") == str(session.id)]

    user_turn = next(turn for turn in turns if turn["role"] == "user")
    assert "4111" not in user_turn["text"]
    assert "test@example.com" not in user_turn["text"]
    assert "[REDACTED]" in user_turn["text"]

