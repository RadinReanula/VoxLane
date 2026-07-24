# Graphify workflow

Graphify is part of the engineering loop, not a one-time diagram generator.

## Bootstrap

After the first source files exist:

```powershell
graphify extract . --code-only
graphify query "How does a customer turn become a confirmed POS order?"
```

The code-only extraction is local and does not require an LLM API. Generated
graph artifacts live in `graphify-out/`.

## Before changing code

Ask a scoped architecture question before reading broadly:

```powershell
graphify query "Which components own interruption and stale audio handling?"
graphify explain "ConversationOrchestrator"
graphify path "LaneDisplay" "OrderService"
```

For refactors, inspect reverse impact:

```powershell
graphify affected "SessionEvent" --depth 3
```

Use direct file and symbol inspection only after the graph has identified the
relevant area.

## After changing code

Refresh the AST graph and check it before concluding a task:

```powershell
graphify update .
graphify check-update .
```

After large deletions or renames, review the graph and use `--force` only when
the lower node count is expected:

```powershell
graphify update . --force
```

## Review checklist

- Query the intended flow before implementation.
- Use `path` to verify cross-language/UI-to-API dependencies.
- Use `affected` before changing a shared contract.
- Refresh after code modifications.
- Record corrected or especially useful query results with `save-result`.
- Do not store secrets, transcripts, raw audio, or customer identifiers in
  Graphify memory.
