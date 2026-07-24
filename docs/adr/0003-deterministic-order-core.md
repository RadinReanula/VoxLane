# ADR 0003: Deterministic order and pricing ownership

Status: accepted

## Context

Language models are useful for interpretation and dialogue, but unreliable as
systems of record for prices, modifiers, and POS submission.

## Decision

Menu validity, modifier constraints, integer-money totals, order transitions,
and POS side effects live in deterministic domain services. The LLM or mock
interpreter may only call typed tools.

## Consequences

Order correctness is unit-testable without network calls. Upsell wording can
still be generative, but cart mutations are never invented outside validated
menu identifiers.
