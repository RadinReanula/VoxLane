from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from voice_agent.config import Settings
from voice_agent.domain import DomainValidationError
from voice_agent.models import (
    HandoffRequest,
    HealthResponse,
    Order,
    OrderStatus,
    PosReceipt,
    SessionSnapshot,
    SessionStatus,
    StartSessionResponse,
    TextTurnRequest,
    TextTurnResponse,
    WebRTCAnswer,
    WebRTCOffer,
)
from voice_agent.orchestrator import ConversationOrchestrator, StaleGenerationError
from voice_agent.providers import (
    CircuitBreaker,
    DeepgramSpeechToTextProvider,
    GroqLanguageProvider,
    LanguageProvider,
    MockLanguageProvider,
    MockPos,
    MockSpeechToTextProvider,
    ResilientLanguageProvider,
)
from voice_agent.repository import Repository, seed
from voice_agent.voice import (
    create_webrtc_connection,
    initialize_webrtc_offer,
    pipecat_available,
    run_voice_session,
    webrtc_capabilities,
)

log = structlog.get_logger()


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        repository = Repository(config.database_url)
        await repository.bootstrap()
        await seed(repository)
        language: LanguageProvider = MockLanguageProvider()
        if config.mode == "cloud":
            if config.groq_api_key is None:
                raise RuntimeError("KUBERNETICA_GROQ_API_KEY is required in cloud mode")
            language = GroqLanguageProvider(
                config.groq_api_key.get_secret_value(),
                config.groq_model,
            )
        resilient = ResilientLanguageProvider(
            language,
            config.provider_timeout_seconds,
            config.provider_retries,
            CircuitBreaker(
                config.circuit_failure_threshold,
                config.circuit_reset_seconds,
            ),
        )
        app.state.settings = config
        app.state.repository = repository
        app.state.orchestrator = ConversationOrchestrator(
            repository,
            resilient,
            config.tax_rate,
            config.redact_transcripts,
        )
        app.state.speech = (
            DeepgramSpeechToTextProvider(config.deepgram_api_key.get_secret_value())
            if config.deepgram_api_key
            else MockSpeechToTextProvider()
        )
        app.state.pos = MockPos(repository)
        app.state.voice_tasks = set()
        log.info("service_started", mode=config.mode)
        yield
        for task in app.state.voice_tasks:
            task.cancel()
        if app.state.voice_tasks:
            await asyncio.gather(*app.state.voice_tasks, return_exceptions=True)
        await repository.close()

    app = FastAPI(
        title="Kubernetica Voice Agent",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in config.allowed_origins.split(",")],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Idempotency-Key"],
    )

    @app.exception_handler(KeyError)
    async def not_found(_request: Request, error: KeyError) -> object:
        return _http_error(404, f"Resource not found: {error.args[0]}")

    @app.exception_handler(DomainValidationError)
    async def invalid(_request: Request, error: DomainValidationError) -> object:
        return _http_error(422, str(error))

    @app.exception_handler(StaleGenerationError)
    async def stale(_request: Request, error: StaleGenerationError) -> object:
        return _http_error(409, str(error))

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            mode=config.mode,
            pipecat_available=pipecat_available(),
        )

    @app.get("/v1/menu")
    async def get_menu(request: Request) -> object:
        return await request.app.state.repository.get_menu()

    @app.post("/v1/sessions", response_model=StartSessionResponse, status_code=201)
    async def start_session(request: Request) -> StartSessionResponse:
        session, order = await request.app.state.orchestrator.start_session()
        return StartSessionResponse(session=session, order=order)

    @app.post("/v1/sessions/{session_id}/turns", response_model=TextTurnResponse)
    async def text_turn(
        session_id: UUID,
        body: TextTurnRequest,
        request: Request,
    ) -> TextTurnResponse:
        orchestrator: ConversationOrchestrator = request.app.state.orchestrator
        return await orchestrator.turn(session_id, body.text)

    @app.post("/v1/sessions/{session_id}/interrupt")
    async def interrupt(session_id: UUID, request: Request) -> object:
        return await request.app.state.orchestrator.interrupt(session_id)

    @app.post("/v1/sessions/{session_id}/handoff")
    async def handoff(
        session_id: UUID,
        request: Request,
        body: HandoffRequest | None = None,
    ) -> object:
        reason = body.reason if body else "operator_request"
        return await request.app.state.orchestrator.request_human(session_id, reason)

    @app.post("/v1/sessions/{session_id}/resume")
    async def resume(session_id: UUID, request: Request) -> object:
        return await request.app.state.orchestrator.resume(session_id)

    @app.get("/v1/sessions/{session_id}", response_model=SessionSnapshot)
    async def session_snapshot(session_id: UUID, request: Request) -> SessionSnapshot:
        snapshot = await request.app.state.repository.get_session_snapshot(session_id)
        return SessionSnapshot.model_validate(snapshot)

    @app.post("/v1/sessions/{session_id}/confirm", response_model=PosReceipt)
    async def confirm(
        session_id: UUID,
        request: Request,
        idempotency_key: Annotated[str, Header(min_length=8, max_length=128)],
    ) -> PosReceipt:
        repository: Repository = request.app.state.repository
        session = await repository.get_session(session_id)
        order: Order = await repository.get_order(session.order_id)
        if not order.lines:
            raise DomainValidationError("Cannot confirm an empty order")
        pos: MockPos = request.app.state.pos
        receipt = await pos.submit(order, idempotency_key)
        order = order.model_copy(update={"status": OrderStatus.SUBMITTED})
        session = session.model_copy(update={"status": SessionStatus.CONFIRMED})
        await repository.save_order(order)
        await repository.save_session(session)
        return receipt

    @app.get("/v1/sessions/{session_id}/events")
    async def events(
        session_id: UUID,
        request: Request,
        after: int = 0,
    ) -> StreamingResponse:
        await request.app.state.repository.get_session(session_id)

        async def stream() -> AsyncIterator[str]:
            cursor = after
            while True:
                rows = await request.app.state.repository.list_events(
                    session_id,
                    after_sequence=cursor,
                )
                for row in rows:
                    cursor = max(cursor, int(row.get("sequence", 0)))
                    event_id = str(row["id"])
                    event_type = row["event_type"]
                    data = json.dumps(row)
                    yield f"id: {event_id}\nevent: {event_type}\ndata: {data}\n\n"
                if await request.is_disconnected():
                    return
                yield ": keepalive\n\n"
                await asyncio.sleep(1)

        return StreamingResponse(stream(), media_type="text/event-stream")

    @app.get("/v1/webrtc/capabilities")
    async def webrtc() -> dict[str, object]:
        return webrtc_capabilities(config)

    @app.post("/api/offer", response_model=WebRTCAnswer)
    @app.post("/v1/webrtc/offer", response_model=WebRTCAnswer)
    async def webrtc_offer(body: WebRTCOffer, request: Request) -> WebRTCAnswer:
        if not pipecat_available() or config.deepgram_api_key is None:
            raise HTTPException(
                status_code=503,
                detail="Cloud voice requires Pipecat and an explicit Deepgram API key",
            )
        orchestrator: ConversationOrchestrator = request.app.state.orchestrator
        if body.session_id is None:
            session, _order = await orchestrator.start_session()
        else:
            session = await request.app.state.repository.get_session(body.session_id)
        connection = create_webrtc_connection()
        answer = await initialize_webrtc_offer(connection, body.sdp, body.type)
        task = asyncio.create_task(
            run_voice_session(connection, orchestrator, session.id, config),
            name=f"voice-session-{session.id}",
        )
        request.app.state.voice_tasks.add(task)

        def cleanup(done: asyncio.Task[None]) -> None:
            request.app.state.voice_tasks.discard(done)
            if not done.cancelled() and (error := done.exception()) is not None:
                log.error("voice_session_failed", session_id=str(session.id), error=str(error))

        task.add_done_callback(cleanup)
        return WebRTCAnswer(**answer, session_id=session.id)

    return app


def _http_error(status_code: int, detail: str) -> object:
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=status_code, content={"detail": detail})


app = create_app()
