FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm \
    && npm install -g @openai/codex \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .
COPY data/algo_themes.json /opt/fixtures/algo_themes.json

CMD ["sh", "-c", "uv run --frozen --no-dev alembic upgrade head && uv run --frozen --no-dev uvicorn dev_server:app --host 0.0.0.0 --port 8001"]
