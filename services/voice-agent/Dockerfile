FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev

COPY main.py ./
COPY voice_agent ./voice_agent

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "voice_agent.app:app", "--host", "0.0.0.0", "--port", "8000"]
