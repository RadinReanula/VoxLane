# Verification strategy

## Domain correctness

Unit tests cover menu availability, required and exclusive modifiers, quantity
limits, integer-money totals, correction/removal, explicit confirmation,
illegal state transitions, and idempotent POS submission. These tests do not
call an LLM.

## Conversation contracts

Scripted text scenarios assert tool calls and final order snapshots for:

- simple item and quantity;
- required size/modifier follow-up;
- ambiguous item clarification;
- correction after review;
- cancellation;
- unavailable item and safe alternative;
- explicit human-help request;
- repeated confirmation and network retry.

## Audio replay set

Keep consented diagnostic clips outside version control. Store only a manifest
with labels for speech boundaries, expected transcript, expected item intent,
noise condition, and interruption timing. Evaluate clean speech, engine idle,
engine rev, wind, rain, speaker echo, passenger speech, and long pauses.

Report word error rate as supporting evidence, but prioritize:

- item and modifier accuracy;
- complete-order accuracy;
- false accept and false reject rates;
- premature and late end-of-turn rates;
- false barge-in rate;
- recovery rate without human intervention.

## Latency

Measure with monotonic clocks at speech start/end, first/final transcript, tool
request/result, LLM first token, TTS first audio, browser playout, cancellation,
and POS acknowledgement. Report sample count, p50, p95, maximum, network, device,
provider/model, and configuration.

Prototype targets:

- end-of-turn to first response audio: p50 below 1.2 seconds;
- end-of-turn to first response audio: p95 below 2.0 seconds;
- verified barge-in to silent playout: below 250 milliseconds;
- stale output after interruption: zero accepted frames.

## Web and accessibility

Component tests cover all states and event ordering. Browser tests cover the
arrival-to-POS happy path, correction, interruption, provider recovery,
reconnect, and human handoff. Automated accessibility checks complement manual
keyboard, reduced-motion, caption, outdoor-distance, and color-contrast review.

## Exit evidence

A prototype release includes test output, a latency report, a labeled scenario
manifest, known failure modes, provider and model versions, and the exact
configuration used. Marketing accuracy and speed claims are not published
unless those artifacts support them.
