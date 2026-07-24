from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

SCHEMA_VERSION: Literal["1.0"] = "1.0"
Money = Annotated[Decimal, Field(ge=0, decimal_places=2)]


def now_utc() -> datetime:
    return datetime.now(UTC)


class VersionedModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0"] = SCHEMA_VERSION


class ModifierChoice(VersionedModel):
    id: str
    name: str
    price_delta: Money = Decimal("0.00")


class ModifierGroup(VersionedModel):
    id: str
    name: str
    min_selections: int = Field(default=0, ge=0)
    max_selections: int = Field(default=1, ge=1)
    choices: list[ModifierChoice]

    @field_validator("max_selections")
    @classmethod
    def valid_range(cls, value: int, info: object) -> int:
        data = getattr(info, "data", {})
        if value < data.get("min_selections", 0):
            raise ValueError("max_selections must be >= min_selections")
        return value


class MenuItem(VersionedModel):
    id: str
    name: str
    description: str = ""
    base_price: Money
    available: bool = True
    modifier_groups: list[ModifierGroup] = Field(default_factory=list)


class Menu(VersionedModel):
    id: str
    name: str
    currency: str = "USD"
    items: list[MenuItem]
    updated_at: datetime = Field(default_factory=now_utc)


class SelectedModifier(VersionedModel):
    group_id: str
    choice_id: str


class OrderLineInput(VersionedModel):
    item_id: str
    quantity: int = Field(default=1, ge=1, le=99)
    modifiers: list[SelectedModifier] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=500)


class OrderLine(OrderLineInput):
    id: UUID = Field(default_factory=uuid4)
    item_name: str
    unit_price: Money
    line_total: Money


class OrderStatus(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    SUBMITTED = "submitted"
    FAILED = "failed"


class Order(VersionedModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    status: OrderStatus = OrderStatus.DRAFT
    currency: str = "USD"
    lines: list[OrderLine] = Field(default_factory=list)
    subtotal: Money = Decimal("0.00")
    tax: Money = Decimal("0.00")
    total: Money = Decimal("0.00")
    revision: int = 0
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class SessionStatus(StrEnum):
    ACTIVE = "active"
    CONFIRMED = "confirmed"
    HUMAN_HELP = "human_help"
    CLOSED = "closed"


class ConversationSession(VersionedModel):
    id: UUID = Field(default_factory=uuid4)
    lifecycle_id: UUID = Field(default_factory=uuid4)
    generation_id: int = 0
    status: SessionStatus = SessionStatus.ACTIVE
    order_id: UUID
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class TurnRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Turn(VersionedModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    generation_id: int
    role: TurnRole
    text: str
    created_at: datetime = Field(default_factory=now_utc)


class TranscriptSegment(VersionedModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    generation_id: int
    speaker: TurnRole
    text: str
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    is_final: bool = True


class EventType(StrEnum):
    ORDER = "order"
    TOOL = "tool"
    PROVIDER_FAILURE = "provider_failure"
    LATENCY = "latency"
    INTERRUPTED = "interrupted"
    HANDOFF = "handoff"


class BaseEvent(VersionedModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    generation_id: int
    sequence: int = Field(default=0, ge=0)
    event_type: EventType
    created_at: datetime = Field(default_factory=now_utc)


class OrderEvent(BaseEvent):
    event_type: Literal[EventType.ORDER] = EventType.ORDER
    operation: str
    order: Order


class ToolEvent(BaseEvent):
    event_type: Literal[EventType.TOOL] = EventType.TOOL
    tool_name: str
    arguments: dict[str, object] = Field(default_factory=dict)
    success: bool


class ProviderFailure(BaseEvent):
    event_type: Literal[EventType.PROVIDER_FAILURE] = EventType.PROVIDER_FAILURE
    provider: str
    operation: str
    error_code: str
    retryable: bool
    redacted_message: str


class LatencySpan(BaseEvent):
    event_type: Literal[EventType.LATENCY] = EventType.LATENCY
    operation: str
    provider: str | None = None
    duration_ms: float = Field(ge=0)
    success: bool = True


class InterruptedEvent(BaseEvent):
    event_type: Literal[EventType.INTERRUPTED] = EventType.INTERRUPTED
    previous_generation_id: int


class HandoffEvent(BaseEvent):
    event_type: Literal[EventType.HANDOFF] = EventType.HANDOFF
    reason: str


DomainEvent = Annotated[
    OrderEvent | ToolEvent | ProviderFailure | LatencySpan | InterruptedEvent | HandoffEvent,
    Field(discriminator="event_type"),
]


class StartSessionResponse(VersionedModel):
    session: ConversationSession
    order: Order


class TextTurnRequest(VersionedModel):
    text: str = Field(min_length=1, max_length=2000)


class TextTurnResponse(VersionedModel):
    session_id: UUID
    generation_id: int
    reply: str
    order: Order


class PosReceipt(VersionedModel):
    idempotency_key: str
    pos_order_id: str
    order_id: UUID
    total: Money
    accepted_at: datetime = Field(default_factory=now_utc)


class HealthResponse(VersionedModel):
    status: Literal["ok", "degraded"]
    mode: str
    pipecat_available: bool


class WebRTCOffer(VersionedModel):
    sdp: str = Field(min_length=1)
    type: Literal["offer"] = "offer"
    session_id: UUID | None = None


class WebRTCAnswer(VersionedModel):
    sdp: str
    type: str
    pc_id: str
    session_id: UUID


class SessionSnapshot(VersionedModel):
    session: ConversationSession
    order: Order
    events: list[dict[str, object]] = Field(default_factory=list)
    latest_sequence: int = Field(default=0, ge=0)


class HandoffRequest(VersionedModel):
    reason: str = Field(default="operator_request", min_length=1, max_length=200)
