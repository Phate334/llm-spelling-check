FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=0 UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev


FROM python:3.13-slim-bookworm

RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

COPY --from=builder --chown=nonroot:nonroot /app /app
RUN mkdir -p /app/data \
    && chown nonroot:nonroot /app/data

ENV PATH="/app/.venv/bin:$PATH"
ENV SPELLING_BASE_URL="http://localhost:7072/v1"
ENV SPELLING_MODEL="gemma-4-26b-a4b"
ENV SPELLING_TIMEOUT="30"

USER nonroot

WORKDIR /app

EXPOSE 8000

CMD ["spelling-check-web", "--host", "0.0.0.0", "--port", "8000"]
