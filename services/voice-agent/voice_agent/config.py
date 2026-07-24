from decimal import Decimal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KUBERNETICA_",
        env_file=".env",
        extra="ignore",
    )

    mode: str = "mock"
    database_url: str = "sqlite+aiosqlite:///./kubernetica.db"
    tax_rate: Decimal = Decimal("0.0825")
    provider_timeout_seconds: float = 8.0
    provider_retries: int = 2
    circuit_failure_threshold: int = 3
    circuit_reset_seconds: float = 30.0
    redact_transcripts: bool = True
    retain_audio: bool = False
    allowed_origins: str = "http://localhost:3000"
    vad_stop_secs: float = 0.2
    turn_fallback_secs: float = 0.65
    barge_in_debounce_ms: int = 120
    deepgram_api_key: SecretStr | None = None
    deepgram_stt_model: str = "nova-3"
    deepgram_tts_model: str = "aura-2-thalia-en"
    groq_api_key: SecretStr | None = None
    groq_model: str = "openai/gpt-oss-20b"


settings = Settings()
