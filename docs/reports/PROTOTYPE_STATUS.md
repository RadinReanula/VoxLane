# Prototype validation status

Validated on 2026-07-13 against the local zero-budget mock path.

## Integrity results

- Backend: `ruff`, `mypy`, and `pytest` — 11 passed
- Frontend: `eslint`, `tsc`, `vitest` — 4 passed
- Production build: `next build` succeeded for `/`, `/lane`, `/console`
- E2E: Playwright chromium + mobile — 4 passed, including axe WCAG tags
- Graphify: `graphify update .` rebuilt the AST graph

## Working prototype capabilities

- Simulated vehicle arrival and local session lifecycle
- Deterministic menu, modifiers, pricing, correction, and idempotent mock POS
- Interruptible generation with stale-response rejection
- Human handoff and resume
- Sequenced events and reconnectable session snapshots
- Transcript redaction and no raw-audio retention by default
- Customer lane and operator console with accessible states/captions
- Optional SmallWebRTC + Pipecat cloud voice path when Deepgram keys are set

## Explicitly deferred

- Sinhala/Tamil production accuracy
- Real POS and payments
- Outdoor FMCW/inductive-loop sensor installation
- LiveKit multi-lane SFU
- Returning-customer identity / plate recognition
- Consented outdoor acoustic latency/accuracy report against live engines and weather

See `docs/reports/PROTOTYPE_LATENCY.md`, `docs/ROADMAP.md`, and `docs/HARDWARE_PATH.md`.
