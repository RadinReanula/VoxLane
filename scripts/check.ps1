$ErrorActionPreference = "Stop"

Push-Location (Join-Path $PSScriptRoot "..")
try {
    npm run lint
    npm run typecheck
    npm run test
    npm run build

    Push-Location "services/voice-agent"
    try {
        uv run ruff check .
        uv run mypy voice_agent tests main.py
        uv run pytest
    }
    finally {
        Pop-Location
    }

    graphify update .
    graphify check-update .
}
finally {
    Pop-Location
}
