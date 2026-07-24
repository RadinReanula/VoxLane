# VoxLane

VoxLane is an English-first drive-thru voice ordering prototype. It combines
a deterministic menu and order domain with a low-latency, interruptible voice
pipeline and an accessible customer display.

## Prototype scope

The first milestone runs on a laptop and supports:

- simulated vehicle arrival and departure;
- typed and spoken ordering;
- live listening, processing, speaking, and recovery states;
- deterministic menu, modifier, pricing, and confirmation rules;
- barge-in with stale-response protection;
- an idempotent mock POS handoff;
- mock providers that require no API keys.

Physical sensors, real POS integrations, payments, Sinhala/Tamil, customer
recognition, and multi-lane deployment are intentionally deferred.

## Repository

- `apps/web` — Next.js customer lane display and operator console
- `services/voice-agent` — FastAPI, Pipecat, order domain, providers, and storage
- `packages/contracts` — versioned shared event contracts
- `fixtures` — sample menu and replay scenarios
- `docs` — architecture, ADRs, runbooks, UX, and Graphify workflow

## Development

Requirements: Node.js 24+, npm 11+, Python 3.13+, `uv`, and Graphify.

```powershell
npm install
npm run dev:web
```

In a second terminal:

```powershell
cd services/voice-agent
uv sync --all-groups
uv run uvicorn app.main:app --reload --port 8000
```

Copy `.env.example` to `.env` only when cloud providers are needed. Mock mode
is the default and does not make paid calls.

## Quality checks

```powershell
npm run lint
npm run typecheck
npm run test
cd services/voice-agent
uv run pytest
uv run ruff check .
uv run mypy voice_agent tests main.py
```

The project targets a median end-of-turn to first response audio below 1.2 s,
p95 below 2.0 s, and barge-in playout stop below 250 ms on the measured test
network. These are acceptance targets, not unverified product claims.

See `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, and
`docs/GRAPHIFY_WORKFLOW.md` for the full development map.
