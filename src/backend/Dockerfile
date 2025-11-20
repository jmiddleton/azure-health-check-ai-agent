###############################################
# Base stage (shared between build and final) #
###############################################

FROM python:3.13-slim AS base

###############
# Build stage #
###############

FROM base AS builder

## Install and configure UV, see https://docs.astral.sh/uv/ for more information

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

COPY uv.lock pyproject.toml /app/
RUN uv sync \
    --frozen \
    --no-dev \
    --no-install-workspace \
    --no-editable \
    --all-packages

COPY *.py *.md *.yaml *.db /app/
COPY .chainlit /app/.chainlit/
COPY config /app/config/
COPY public /app/public/
COPY utils /app/utils/
COPY tools /app/tools/

###############
# Final image #
###############

FROM base

RUN groupadd -r app
RUN useradd -r -d /app -g app -N app

COPY --from=builder --chown=app:app /app /app
WORKDIR /app

ENV PYTHONUNBUFFERED=1

EXPOSE 80
ENTRYPOINT ["/app/.venv/bin/chainlit",  "run", "chat_server.py","--host", "0.0.0.0",  "--port", "80"]