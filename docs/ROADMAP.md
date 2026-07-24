# Development roadmap

## Milestone 0 — repeatable workspace

Establish the monorepo, mock configuration, quality commands, CI, Graphify
index, architecture decisions, and a one-command local start. Exit when a new
developer can run web and API health checks without cloud credentials.

## Milestone 1 — text order engine

Load a validated sample menu, create and correct orders through typed tools,
enforce modifier rules, calculate totals, confirm explicitly, and submit once to
the mock POS. Exit when scripted conversation and domain tests pass without an
LLM.

## Milestone 2 — customer experience simulator

Drive the lane and console from versioned session events. Complete every state,
caption, cart, recovery, and handoff view before voice providers are connected.
Exit when browser E2E and accessibility checks pass.

## Milestone 3 — streamed English voice

Add SmallWebRTC, browser audio processing, Silero VAD, Smart Turn, streaming
STT, tool-calling LLM, and streamed TTS. Mock and cloud providers must implement
the same interfaces. Exit when a user can complete and correct an order by
voice.

## Milestone 4 — interruption and failure hardening

Cancel playout and in-flight generation on verified barge-in, reject stale
frames, recover from timeouts and reconnects, and provide human escalation.
Exit when replayed interruption and provider-failure scenarios are
deterministic.

## Milestone 5 — measured prototype

Create a labeled clean/noisy audio set and publish latency, order accuracy,
false interruption, and recovery results. The gate is measured evidence, not
“zero latency,” “flawless,” or an assumed 98% accuracy.

## Post-prototype

1. Bench-test and then outdoor-test an IP-rated FMCW radar adapter.
2. Run an acoustic survey with the intended microphone, speaker, enclosure, and
   mounting geometry.
3. Benchmark English/Tamil code-switching separately; build a Sinhala dataset
   and provider evaluation because Nova-3 does not currently support Sinhala.
4. Integrate one real POS through a contract test harness and restaurant-owned
   sandbox.
5. Move SQLite to PostgreSQL and add managed secrets, deployment, alerting, and
   backups.
6. Introduce LiveKit only when multi-lane or remote-media requirements are
   demonstrated.
7. Complete privacy, consent, retention, accessibility, electrical, and local
   installation reviews before a public pilot.

## Cost guardrails

Mock mode is the permanent zero-cost development path. Cloud evaluation uses
one-time credits and explicit quotas. The application never automatically
crosses into a paid provider or switches to a paid fallback. Production unit
economics must include STT/TTS/LLM usage, media transport, hosting, support,
hardware, installation, POS integration, and failed-order handling.
