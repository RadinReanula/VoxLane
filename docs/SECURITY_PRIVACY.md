# Security and privacy baseline

## Prototype defaults

- Provider credentials remain in server environment variables and never enter
  browser bundles, events, screenshots, or logs.
- Raw audio retention is off.
- Transcript persistence is off unless explicitly enabled for a consented test.
- Structured logs use identifiers and timing metadata, with customer text
  redacted.
- Mock mode is the default and never invokes a paid provider.
- Cloud failures do not trigger an unapproved fallback provider.

## Session controls

Session, turn, generation, and event identifiers are unguessable UUIDs. API
mutations validate the active session and expected version. POS submission
requires explicit confirmed state and an idempotency key. Replays return the
prior result rather than creating a second order.

Operator actions are auditable. A production operator console will require
authentication and role-based authorization; the local prototype binds to the
development environment and must not be exposed to an untrusted network.

## Retention and consent

Diagnostic recording requires visible operator activation and customer/tester
consent. Retention duration and deletion are configuration, with the shortest
useful duration preferred. Real deployments require legal review for Sri Lankan
data-protection obligations, cross-border provider processing, children's data,
payment boundaries, and restaurant policy.

## Threats to test

- prompt injection spoken as an order;
- attempts to invoke undeclared tools or alter prices;
- malformed and oversized event payloads;
- stale generation replay after barge-in;
- duplicate confirmation/POS requests;
- API-key exposure in client output and exception traces;
- transcript or audio leakage through telemetry;
- denial of service through endless speech, reconnects, or provider retries.

The LLM receives the minimum menu and order context necessary for the current
turn. It cannot execute arbitrary network, filesystem, database, or payment
operations.
