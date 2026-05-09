FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/kiyeonjeon21/timbregrid" \
      org.opencontainers.image.description="Local-first compatibility and evaluation layer for open-source TTS" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    TIMBREGRID_MODEL=fake:tts \
    TIMBREGRID_HOST=0.0.0.0 \
    TIMBREGRID_PORT=8889 \
    TIMBREGRID_BENCHMARK_DIR=benchmarks/examples

WORKDIR /app

RUN python -m pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
COPY manifests ./manifests
COPY schemas ./schemas
COPY benchmarks ./benchmarks

RUN uv sync --frozen --no-dev

EXPOSE 8889

CMD ["timbregrid", "serve"]
