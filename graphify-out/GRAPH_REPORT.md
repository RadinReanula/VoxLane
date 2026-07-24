# Graph Report - AI_Drivetru_Pilot  (2026-07-13)

## Corpus Check
- 60 files · ~13,564 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 466 nodes · 839 edges · 44 communities (36 shown, 8 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 182 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- lane-experience.tsx
- providers.py
- devDependencies
- models.py
- Repository
- compilerOptions
- DomainValidationError
- app.py
- scripts
- OptionalVoiceAdapter
- System architecture
- models.py
- layout.tsx
- eslint.config.mjs
- next.config.ts
- next-env.d.ts
- postcss.config.mjs
- voice-agent
- Development roadmap
- Verification strategy
- Provider strategy
- Graphify workflow
- Physical pilot path
- Security and privacy baseline
- Customer and operator experience
- Kubernetica
- ADR 0001: Prototype boundaries and core ownership
- Prototype latency report
- README.md
- AGENTS.md
- index.ts
- package.json
- ADR 0002: Pipecat + SmallWebRTC for the prototype voice path
- ADR 0003: Deterministic order and pricing ownership
- Prototype latency report

## God Nodes (most connected - your core abstractions)
1. `Repository` - 41 edges
2. `ConversationOrchestrator` - 40 edges
3. `StaleGenerationError` - 26 edges
4. `Order` - 23 edges
5. `DomainValidationError` - 22 edges
6. `VersionedModel` - 22 edges
7. `PosReceipt` - 21 edges
8. `Menu` - 19 edges
9. `compilerOptions` - 16 edges
10. `FailingProvider` - 16 edges

## Surprising Connections (you probably didn't know these)
- `test_mock_mode_order_flow_without_keys()` --calls--> `create_app()`  [INFERRED]
  services/voice-agent/tests/test_api.py → services/voice-agent/voice_agent/app.py
- `test_calculates_modifier_quantity_and_tax()` --calls--> `Order`  [INFERRED]
  services/voice-agent/tests/test_domain.py → services/voice-agent/voice_agent/models.py
- `test_rejects_missing_required_modifier()` --calls--> `Order`  [INFERRED]
  services/voice-agent/tests/test_domain.py → services/voice-agent/voice_agent/models.py
- `test_replaces_line_for_correction()` --calls--> `Order`  [INFERRED]
  services/voice-agent/tests/test_domain.py → services/voice-agent/voice_agent/models.py
- `repository()` --calls--> `Repository`  [INFERRED]
  services/voice-agent/tests/test_services.py → services/voice-agent/voice_agent/repository.py

## Import Cycles
- None detected.

## Communities (44 total, 8 thin omitted)

### Community 0 - "lane-experience.tsx"
Cohesion: 0.10
Nodes (27): CarIcon(), CheckIcon(), HeadsetIcon(), MicIcon(), SparkIcon(), client, LaneExperience(), MENU (+19 more)

### Community 1 - "providers.py"
Cohesion: 0.09
Nodes (22): dependencies, next, @pipecat-ai/client-js, @pipecat-ai/small-webrtc-transport, react, react-dom, name, private (+14 more)

### Community 2 - "devDependencies"
Cohesion: 0.06
Nodes (33): devDependencies, @axe-core/playwright, eslint, eslint-config-next, jsdom, @playwright/test, tailwindcss, @tailwindcss/postcss (+25 more)

### Community 3 - "models.py"
Cohesion: 0.13
Nodes (28): FailingProvider, Path, repository(), SlowProvider, test_events_are_sequenced_and_reconnectable(), test_help_utterance_triggers_handoff(), test_human_handoff_and_resume(), test_interruption_cancels_active_generation() (+20 more)

### Community 4 - "Repository"
Cohesion: 0.08
Nodes (25): DeclarativeBase, DomainEvent, Protocol, Order, PosReceipt, Turn, CircuitBreaker, DeepgramSpeechToTextProvider (+17 more)

### Community 5 - "compilerOptions"
Cohesion: 0.06
Nodes (30): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+22 more)

### Community 6 - "DomainValidationError"
Cohesion: 0.28
Nodes (20): test_calculates_modifier_quantity_and_tax(), test_rejects_missing_required_modifier(), test_replaces_line_for_correction(), add_line(), calculate_line(), DomainValidationError, get_item(), money() (+12 more)

### Community 7 - "app.py"
Cohesion: 0.15
Nodes (16): BaseSettings, FastAPI, Path, test_mock_mode_order_flow_without_keys(), Settings, Kubernetica voice-agent backend., build_pipecat_pipeline(), create_webrtc_connection() (+8 more)

### Community 8 - "scripts"
Cohesion: 0.12
Nodes (16): engines, node, npm, name, private, scripts, build, dev:web (+8 more)

### Community 10 - "System architecture"
Cohesion: 0.20
Nodes (9): Audio and turn pipeline, Barge-in protocol, Conversation and order boundary, Data model, Design principles, Failure and privacy policy, Runtime topology, System architecture (+1 more)

### Community 11 - "models.py"
Cohesion: 0.14
Nodes (23): BaseModel, datetime, create_app(), HandoffRequest, HealthResponse, MenuItem, ModifierChoice, ModifierGroup (+15 more)

### Community 21 - "Development roadmap"
Cohesion: 0.20
Nodes (9): Cost guardrails, Development roadmap, Milestone 0 — repeatable workspace, Milestone 1 — text order engine, Milestone 2 — customer experience simulator, Milestone 3 — streamed English voice, Milestone 4 — interruption and failure hardening, Milestone 5 — measured prototype (+1 more)

### Community 22 - "Verification strategy"
Cohesion: 0.25
Nodes (7): Audio replay set, Conversation contracts, Domain correctness, Exit evidence, Latency, Verification strategy, Web and accessibility

### Community 23 - "Provider strategy"
Cohesion: 0.29
Nodes (6): Cost and failure rules, Development mode, English cloud evaluation, Language expansion, Offline options, Provider strategy

### Community 24 - "Graphify workflow"
Cohesion: 0.33
Nodes (5): After changing code, Before changing code, Bootstrap, Graphify workflow, Review checklist

### Community 25 - "Physical pilot path"
Cohesion: 0.33
Nodes (5): Acoustic station, Physical pilot path, Presence sensor, Prototype, Sensor acceptance tests

### Community 26 - "Security and privacy baseline"
Cohesion: 0.33
Nodes (5): Prototype defaults, Retention and consent, Security and privacy baseline, Session controls, Threats to test

### Community 27 - "Customer and operator experience"
Cohesion: 0.33
Nodes (5): Customer and operator experience, Customer lane display, Operator console, Responsive targets, Visual system

### Community 28 - "Kubernetica"
Cohesion: 0.33
Nodes (5): Development, Kubernetica, Prototype scope, Quality checks, Repository

### Community 29 - "ADR 0001: Prototype boundaries and core ownership"
Cohesion: 0.40
Nodes (4): ADR 0001: Prototype boundaries and core ownership, Consequences, Context, Decision

### Community 30 - "Prototype latency report"
Cohesion: 0.40
Nodes (4): Accuracy, Interpretation, Prototype latency report, Results

### Community 31 - "README.md"
Cohesion: 0.50
Nodes (3): Deploy on Vercel, Getting Started, Learn More

### Community 39 - "index.ts"
Cohesion: 0.18
Nodes (10): BackendSessionSnapshot, Caption, CONTRACT_VERSION, DriveThruSession, Order, OrderItem, SessionCommand, SessionDiagnostics (+2 more)

### Community 40 - "package.json"
Cohesion: 0.25
Nodes (7): exports, main, name, private, type, types, version

### Community 41 - "ADR 0002: Pipecat + SmallWebRTC for the prototype voice path"
Cohesion: 0.40
Nodes (4): ADR 0002: Pipecat + SmallWebRTC for the prototype voice path, Consequences, Context, Decision

### Community 42 - "ADR 0003: Deterministic order and pricing ownership"
Cohesion: 0.40
Nodes (4): ADR 0003: Deterministic order and pricing ownership, Consequences, Context, Decision

### Community 43 - "Prototype latency report"
Cohesion: 0.40
Nodes (4): Accuracy, Interpretation, Prototype latency report, Results

## Knowledge Gaps
- **165 isolated node(s):** `eslintConfig`, `workspaceRoot`, `nextConfig`, `name`, `version` (+160 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Repository` connect `Repository` to `models.py`, `DomainValidationError`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Why does `ConversationOrchestrator` connect `models.py` to `models.py`, `Repository`, `DomainValidationError`, `app.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `devDependencies` connect `devDependencies` to `providers.py`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `Repository` (e.g. with `FailingProvider` and `repository()`) actually correct?**
  _`Repository` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `ConversationOrchestrator` (e.g. with `FailingProvider` and `SlowProvider`) actually correct?**
  _`ConversationOrchestrator` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `StaleGenerationError` (e.g. with `FailingProvider` and `SlowProvider`) actually correct?**
  _`StaleGenerationError` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `Order` (e.g. with `test_calculates_modifier_quantity_and_tax()` and `test_rejects_missing_required_modifier()`) actually correct?**
  _`Order` has 21 INFERRED edges - model-reasoned connections that need verification._