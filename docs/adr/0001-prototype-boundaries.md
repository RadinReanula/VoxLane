# ADR 0001: Prototype boundaries and core ownership

Status: accepted

## Context

The prototype must demonstrate natural, low-latency ordering on existing laptop
hardware without tying the product to one provider or allowing a probabilistic
model to control money and fulfillment.

## Decision

- Pipecat coordinates the Python streaming pipeline.
- SmallWebRTC connects the browser and local agent; LiveKit is deferred.
- WebRTC audio processing precedes Silero VAD and Smart Turn.
- The LLM selects typed tools, while deterministic domain services own menu
  validity, modifiers, totals, order transitions, and POS submission.
- SQLite implements repository interfaces that can later use PostgreSQL.
- Provider interfaces support cloud and no-key mock/local modes.
- The software prototype simulates vehicle and POS integrations.
- IP-rated FMCW radar or an inductive loop is the production sensor path.
- Raw audio retention is disabled by default.

## Consequences

The first demo can run without cloud keys, provider changes remain localized,
and order correctness is testable without conversational inference. The
prototype does not claim production acoustic accuracy, multi-lane scale, or
permanent zero operating cost.
