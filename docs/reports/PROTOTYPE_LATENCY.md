# Prototype latency report

Date: 2026-07-13

Commit or source snapshot: local workspace before first commit

Device and operating system: Windows 11 laptop (local mock/cloud-optional)

Network and provider region: local mock mode; cloud providers not required for this run

STT, LLM, TTS, VAD, and turn models:
- Mock STT/LLM/TTS for zero-key integrity
- Cloud path configured for Deepgram Nova-3 + Aura-2 and Groq `openai/gpt-oss-20b`
- Silero VAD stop 0.20 s, Smart Turn fallback 0.65 s

Configuration: `KUBERNETICA_MODE=mock`

## Results

- Sample count: automated domain + API integrity suite (not outdoor acoustic set)
- End-of-turn to first final transcript p50 / p95 / max: N/A in mock text mode
- End-of-turn to LLM first token p50 / p95 / max: N/A in mock text mode
- End-of-turn to first TTS audio p50 / p95 / max: N/A until consented audio capture
- End-of-turn to browser playout p50 / p95 / max: N/A until consented audio capture
- Verified barge-in to silent playout p50 / p95 / max: browser adapter interrupt clears active audio immediately; cloud playout measurement pending
- Stale frames accepted after interruption: 0 in orchestrator generation tests
- Provider failure recovery rate: safe fallback reply recorded without leaking upstream details

## Accuracy

- Complete-order accuracy: deterministic menu fixtures pass unit tests
- Item accuracy: scripted add/remove/replace tools pass
- Modifier accuracy: required modifier rejection passes
- Premature end-of-turn rate: deferred to labeled audio replay set
- False barge-in rate: deferred to labeled audio replay set

## Interpretation

Software integrity for order domain, interruption cancellation, handoff,
reconnect snapshots, and UI accessibility is green in mock mode. Acoustic and
cloud latency targets remain measurement work using `fixtures/audio` once
consented clips exist.
