from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Integer, String, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from voice_agent.models import ConversationSession, DomainEvent, Menu, Order, PosReceipt, Turn


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"
    kind: Mapped[str] = mapped_column(String(32), primary_key=True)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    body: Mapped[dict[str, Any]] = mapped_column(JSON)


class EventDocument(Base):
    __tablename__ = "events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    sequence: Mapped[int] = mapped_column(Integer, index=True)
    body: Mapped[dict[str, Any]] = mapped_column(JSON)


class SessionSequence(Base):
    __tablename__ = "session_sequences"
    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    next_sequence: Mapped[int] = mapped_column(Integer, default=1)


class Repository:
    def __init__(self, database_url: str) -> None:
        self.engine: AsyncEngine = create_async_engine(database_url)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def bootstrap(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        await self.engine.dispose()

    async def _put(self, kind: str, identifier: str, body: dict[str, Any]) -> None:
        async with self.sessions() as db:
            row = await db.get(Document, (kind, identifier))
            if row:
                row.body = body
            else:
                db.add(Document(kind=kind, id=identifier, body=body))
            await db.commit()

    async def _get(self, kind: str, identifier: str) -> dict[str, Any] | None:
        async with self.sessions() as db:
            row = await db.get(Document, (kind, identifier))
            return row.body if row else None

    async def save_menu(self, menu: Menu) -> None:
        await self._put("menu", menu.id, menu.model_dump(mode="json"))

    async def get_menu(self, menu_id: str = "default") -> Menu:
        body = await self._get("menu", menu_id)
        if body is None:
            raise KeyError(menu_id)
        return Menu.model_validate(body)

    async def save_session(self, session: ConversationSession) -> None:
        await self._put("session", str(session.id), session.model_dump(mode="json"))

    async def get_session(self, session_id: UUID) -> ConversationSession:
        body = await self._get("session", str(session_id))
        if body is None:
            raise KeyError(session_id)
        return ConversationSession.model_validate(body)

    async def save_order(self, order: Order) -> None:
        await self._put("order", str(order.id), order.model_dump(mode="json"))

    async def get_order(self, order_id: UUID) -> Order:
        body = await self._get("order", str(order_id))
        if body is None:
            raise KeyError(order_id)
        return Order.model_validate(body)

    async def save_turn(self, turn: Turn) -> None:
        await self._put("turn", str(turn.id), turn.model_dump(mode="json"))

    async def save_receipt(self, receipt: PosReceipt) -> None:
        await self._put("receipt", receipt.idempotency_key, receipt.model_dump(mode="json"))

    async def get_receipt(self, idempotency_key: str) -> PosReceipt | None:
        body = await self._get("receipt", idempotency_key)
        return PosReceipt.model_validate(body) if body else None

    async def append_event(self, event: DomainEvent) -> DomainEvent:
        async with self.sessions() as db:
            session_key = str(event.session_id)
            counter = await db.get(SessionSequence, session_key)
            if counter is None:
                counter = SessionSequence(session_id=session_key, next_sequence=1)
                db.add(counter)
                await db.flush()
            sequence = counter.next_sequence
            counter.next_sequence = sequence + 1
            stamped = event.model_copy(update={"sequence": sequence})
            body = stamped.model_dump(mode="json")
            db.add(
                EventDocument(
                    id=str(stamped.id),
                    session_id=session_key,
                    sequence=sequence,
                    body=body,
                )
            )
            await db.commit()
            return stamped

    async def list_events(
        self,
        session_id: UUID,
        after_sequence: int = 0,
    ) -> list[dict[str, Any]]:
        async with self.sessions() as db:
            query = (
                select(EventDocument)
                .where(EventDocument.session_id == str(session_id))
                .where(EventDocument.sequence > after_sequence)
                .order_by(EventDocument.sequence.asc())
            )
            rows = (await db.scalars(query)).all()
            return [row.body for row in rows]

    async def get_session_snapshot(self, session_id: UUID) -> dict[str, Any]:
        session = await self.get_session(session_id)
        order = await self.get_order(session.order_id)
        events = await self.list_events(session_id)
        return {
            "schema_version": "1.0",
            "session": session.model_dump(mode="json"),
            "order": order.model_dump(mode="json"),
            "events": events,
            "latest_sequence": events[-1]["sequence"] if events else 0,
        }


def sample_menu() -> Menu:
    return Menu.model_validate(
        {
            "id": "default",
            "name": "Kubernetica Drive-Thru",
            "currency": "USD",
            "items": [
                {
                    "id": "classic-burger",
                    "name": "Classic Burger",
                    "description": "Beef patty, lettuce, tomato, and house sauce",
                    "base_price": "7.50",
                    "modifier_groups": [
                        {
                            "id": "cheese",
                            "name": "Cheese",
                            "min_selections": 0,
                            "max_selections": 1,
                            "choices": [
                                {"id": "american", "name": "American", "price_delta": "0.75"},
                                {"id": "cheddar", "name": "Cheddar", "price_delta": "1.00"},
                            ],
                        }
                    ],
                },
                {
                    "id": "fries",
                    "name": "Fries",
                    "base_price": "3.00",
                    "modifier_groups": [
                        {
                            "id": "size",
                            "name": "Size",
                            "min_selections": 1,
                            "max_selections": 1,
                            "choices": [
                                {"id": "regular", "name": "Regular", "price_delta": "0.00"},
                                {"id": "large", "name": "Large", "price_delta": "1.25"},
                            ],
                        }
                    ],
                },
                {"id": "cola", "name": "Cola", "base_price": "2.25"},
            ],
        }
    )


async def seed(repository: Repository) -> None:
    try:
        await repository.get_menu()
    except KeyError:
        await repository.save_menu(sample_menu())
