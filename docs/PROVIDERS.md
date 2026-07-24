# Provider strategy

## Development mode

Mock STT emits scripted interim and final transcripts. Mock LLM maps fixture
utterances to typed tools. Mock TTS produces timing and caption events without
requiring an audio API. This mode exercises the complete session, order, event,
and interruption lifecycle at zero cost.

## English cloud evaluation

- STT: Deepgram Nova-3 streaming through the STT adapter.
- LLM: Groq `openai/gpt-oss-20b` as the latency baseline, benchmarked against
  `openai/gpt-oss-120b` for tool-call quality.
- TTS: Deepgram Aura-2 streaming through the TTS adapter.
- Turn detection: local Silero VAD and Pipecat Smart Turn V3, independent of
  the STT provider.

Model identifiers are configuration because hosted catalogs and deprecation
dates change. Startup validation should reject an unknown model with a useful
error rather than silently choosing another.

## Offline options

Piper is the first offline TTS experiment. Local STT and LLM options must be
benchmarked on the actual prototype laptop before being promoted from
experimental status; nominal model quality is irrelevant if they miss the
latency budget.

## Language expansion

English is the first validated language. Deepgram supports Tamil but its
Sri Lankan accent and English/Tamil code-switch accuracy still require a local
dataset. Nova-3 does not currently list Sinhala, so Sinhala needs an independent
ASR/TTS evaluation and likely a dedicated dataset. Language support is not a
configuration checkbox until order-level accuracy is measured.

## Cost and failure rules

Free credits are finite evaluation funding, not a zero-cost production model.
Each cloud adapter has an explicit enable flag, timeout, quota budget, and
circuit breaker. The system stops or requests human help at a quota boundary;
it never incurs an unapproved charge or changes vendors invisibly.
