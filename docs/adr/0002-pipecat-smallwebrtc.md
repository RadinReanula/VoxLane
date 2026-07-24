# ADR 0002: Pipecat + SmallWebRTC for the prototype voice path

Status: accepted

## Context

The drive-thru prototype needs barge-in, VAD, turn detection, streaming STT/TTS,
and a browser client on a zero-budget laptop.

## Decision

Use Pipecat as the streaming orchestration framework and SmallWebRTC as the
browser transport. Defer LiveKit until multi-lane, SIP, remote operators, or
managed SFU requirements appear.

Silero VAD and Local Smart Turn V3 run locally. Deepgram and Groq are optional
cloud adapters behind interfaces; mock mode remains the default.

## Consequences

The team avoids SFU operational cost during the prototype while keeping a clear
upgrade path. Voice quality still depends on microphone geometry and measured
tuning of VAD/turn thresholds.
