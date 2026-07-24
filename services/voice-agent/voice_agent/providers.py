from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass
from typing import Protocol
from uuid import NAMESPACE_URL, uuid5

import httpx

from voice_agent.models import Order, PosReceipt
from voice_agent.repository import Repository


class ProviderError(RuntimeError):
    def __init__(self, provider: str, code: str, retryable: bool, message: str) -> None:
        super().__init__(message)
        self.provider = provider
        self.code = code
        self.retryable = retryable


class LanguageProvider(Protocol):
    name: str

    async def respond(self, prompt: str) -> str: ...


class SpeechToTextProvider(Protocol):
    name: str

    async def transcribe(self, audio: bytes) -> str: ...


class MockLanguageProvider:
    name = "mock"

    async def respond(self, prompt: str) -> str:
        return f"I heard: {prompt}"


class MockSpeechToTextProvider:
    name = "mock"

    async def transcribe(self, audio: bytes) -> str:
        return audio.decode("utf-8", errors="replace")


class GroqLanguageProvider:
    name = "groq"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def respond(self, prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                },
            )
        if response.status_code >= 400:
            raise ProviderError(
                "groq", str(response.status_code), response.status_code >= 500, "request failed"
            )
        return str(response.json()["choices"][0]["message"]["content"])


class DeepgramSpeechToTextProvider:
    name = "deepgram"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def transcribe(self, audio: bytes) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.deepgram.com/v1/listen?model=nova-3&smart_format=true",
                headers={"Authorization": f"Token {self.api_key}", "Content-Type": "audio/wav"},
                content=audio,
            )
        if response.status_code >= 400:
            raise ProviderError(
                "deepgram", str(response.status_code), response.status_code >= 500, "request failed"
            )
        return str(response.json()["results"]["channels"][0]["alternatives"][0]["transcript"])


@dataclass
class CircuitBreaker:
    failure_threshold: int
    reset_seconds: float
    failures: int = 0
    opened_at: float | None = None

    def allow(self) -> bool:
        if self.opened_at is None:
            return True
        if time.monotonic() - self.opened_at >= self.reset_seconds:
            self.failures = 0
            self.opened_at = None
            return True
        return False

    def success(self) -> None:
        self.failures = 0
        self.opened_at = None

    def failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.opened_at = time.monotonic()


class ResilientLanguageProvider:
    def __init__(
        self,
        provider: LanguageProvider,
        timeout_seconds: float,
        retries: int,
        breaker: CircuitBreaker,
    ) -> None:
        self.provider = provider
        self.name = provider.name
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.breaker = breaker

    async def respond(self, prompt: str) -> str:
        if not self.breaker.allow():
            raise ProviderError(self.name, "circuit_open", True, "provider temporarily unavailable")
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                result = await asyncio.wait_for(
                    self.provider.respond(prompt),
                    timeout=self.timeout_seconds,
                )
                self.breaker.success()
                return result
            except (TimeoutError, httpx.HTTPError, ProviderError) as error:
                last_error = error
                self.breaker.failure()
                retryable = not isinstance(error, ProviderError) or error.retryable
                if not retryable or attempt == self.retries:
                    break
                await asyncio.sleep(0.05 * (2**attempt))
        if isinstance(last_error, ProviderError):
            raise last_error
        raise ProviderError(self.name, "timeout", True, "provider timed out") from last_error


class MockPos:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    async def submit(self, order: Order, idempotency_key: str) -> PosReceipt:
        existing = await self.repository.get_receipt(idempotency_key)
        if existing:
            if existing.order_id != order.id:
                raise ValueError("Idempotency key already belongs to another order")
            return existing
        receipt = PosReceipt(
            idempotency_key=idempotency_key,
            pos_order_id=f"mock-{uuid5(NAMESPACE_URL, idempotency_key).hex[:12]}",
            order_id=order.id,
            total=order.total,
        )
        await self.repository.save_receipt(receipt)
        return receipt


_SENSITIVE = re.compile(
    r"\b(?:\d[ -]*?){13,19}\b|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def redact(text: str) -> str:
    return _SENSITIVE.sub("[REDACTED]", text)
