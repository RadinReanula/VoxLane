from __future__ import annotations

import asyncio
from importlib.util import find_spec
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from voice_agent.config import Settings
    from voice_agent.orchestrator import ConversationOrchestrator


def pipecat_available() -> bool:
    return find_spec("pipecat") is not None


def build_pipecat_pipeline(*processors: Any) -> Any:
    """Build a Pipecat pipeline while keeping heavyweight imports lazy."""
    if not pipecat_available():
        raise RuntimeError("Install the pipecat-ai extra to enable WebRTC voice pipelines")
    from pipecat.pipeline.pipeline import Pipeline

    return Pipeline(list(processors))


def create_webrtc_connection() -> Any:
    if not pipecat_available():
        raise RuntimeError("Pipecat is not installed")
    from pipecat.transports.smallwebrtc.connection import IceServer, SmallWebRTCConnection

    return SmallWebRTCConnection(
        ice_servers=[IceServer(urls=["stun:stun.l.google.com:19302"])],
        connection_timeout_secs=60,
    )


async def initialize_webrtc_offer(connection: Any, sdp: str, offer_type: str) -> dict[str, str]:
    await connection.initialize(sdp=sdp, type=offer_type)
    answer = connection.get_answer()
    return {
        "sdp": str(answer.sdp),
        "type": str(answer.type),
        "pc_id": str(connection.pc_id),
    }


async def run_voice_session(
    connection: Any,
    orchestrator: ConversationOrchestrator,
    session_id: UUID,
    settings: Settings,
) -> None:
    """Run an interruptible STT -> deterministic order core -> TTS pipeline."""
    if settings.deepgram_api_key is None:
        raise RuntimeError("Deepgram is required for the cloud voice pipeline")

    from pipecat.audio.turn.smart_turn.base_smart_turn import SmartTurnParams
    from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.audio.vad.vad_analyzer import VADParams
    from pipecat.frames.frames import (
        TextFrame,
        TranscriptionFrame,
        UserStartedSpeakingFrame,
        UserStoppedSpeakingFrame,
    )
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineParams, PipelineTask
    from pipecat.processors.aggregators.llm_context import LLMContext
    from pipecat.processors.aggregators.llm_response_universal import (
        LLMContextAggregatorPair,
        LLMUserAggregatorParams,
    )
    from pipecat.processors.frame_processor import FrameProcessor
    from pipecat.services.deepgram.stt import DeepgramSTTService
    from pipecat.services.deepgram.tts import DeepgramTTSService
    from pipecat.transports.base_transport import TransportParams
    from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
    from pipecat.turns.user_stop import TurnAnalyzerUserTurnStopStrategy
    from pipecat.turns.user_turn_strategies import UserTurnStrategies

    class OrderAgentProcessor(FrameProcessor):
        def __init__(self) -> None:
            super().__init__()
            self._transcripts: list[str] = []
            self._turn_stopped = False
            self._response_lock = asyncio.Lock()

        async def _respond(self) -> None:
            if not self._transcripts or self._response_lock.locked():
                return
            async with self._response_lock:
                transcript = " ".join(self._transcripts).strip()
                self._transcripts.clear()
                self._turn_stopped = False
                if transcript:
                    result = await orchestrator.turn(session_id, transcript)
                    await self.push_frame(TextFrame(result.reply))

        async def process_frame(self, frame: Any, direction: Any) -> None:
            await super().process_frame(frame, direction)
            if isinstance(frame, UserStartedSpeakingFrame):
                await orchestrator.interrupt(session_id)
            elif isinstance(frame, TranscriptionFrame) and frame.finalized and frame.text.strip():
                self._transcripts.append(frame.text.strip())
                if self._turn_stopped:
                    await self._respond()
            elif isinstance(frame, UserStoppedSpeakingFrame):
                self._turn_stopped = True
                await self._respond()
            await self.push_frame(frame, direction)

    api_key = settings.deepgram_api_key.get_secret_value()
    transport = SmallWebRTCTransport(
        connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            audio_in_sample_rate=16000,
            audio_out_sample_rate=24000,
        ),
    )
    stt = DeepgramSTTService(
        api_key=api_key,
        settings=DeepgramSTTService.Settings(
            model=settings.deepgram_stt_model,
            language="en",
            interim_results=True,
            punctuate=True,
            smart_format=True,
        ),
    )
    tts = DeepgramTTSService(
        api_key=api_key,
        settings=DeepgramTTSService.Settings(voice=settings.deepgram_tts_model),
    )
    context = LLMContext()
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(stop_secs=settings.vad_stop_secs),
            ),
            user_turn_strategies=UserTurnStrategies(
                stop=[
                    TurnAnalyzerUserTurnStopStrategy(
                        turn_analyzer=LocalSmartTurnAnalyzerV3(
                            params=SmartTurnParams(stop_secs=settings.turn_fallback_secs),
                        )
                    )
                ]
            ),
        ),
    )
    pipeline = build_pipecat_pipeline(
        transport.input(),
        stt,
        user_aggregator,
        OrderAgentProcessor(),
        tts,
        transport.output(),
        assistant_aggregator,
    )
    task = PipelineTask(
        pipeline,
        conversation_id=str(session_id),
        params=PipelineParams(
            audio_in_sample_rate=16000,
            audio_out_sample_rate=24000,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    @transport.event_handler("on_client_disconnected")  # type: ignore[untyped-decorator]
    async def on_client_disconnected(_transport: Any, _client: Any) -> None:
        await task.cancel(reason="WebRTC client disconnected")

    await PipelineRunner().run(task)


def webrtc_capabilities(settings: Settings | None = None) -> dict[str, object]:
    cloud_ready = bool(settings and settings.deepgram_api_key)
    return {
        "available": pipecat_available(),
        "cloud_ready": cloud_ready,
        "transport": "smallwebrtc",
        "signaling": "application-managed",
        "vad": "silero",
        "turn_detection": "local-smart-turn-v3",
        "stt": settings.deepgram_stt_model if settings else "nova-3",
        "tts": settings.deepgram_tts_model if settings else "aura-2-thalia-en",
        "note": (
            "Cloud voice is ready."
            if cloud_ready
            else "Text and simulated UI remain available without provider keys."
        ),
    }
