###############################################
# Base stage (shared between build and final) #
###############################################

FROM python:3.13-slim AS base

###############
# Build stage #
###############

FROM base AS builder

# Install UV CLI from official container
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

COPY *.py *.md *.yaml /app/
COPY config /app/config/
COPY public /app/public/
COPY utils /app/utils/
COPY tools /app/tools/

###############
# Final image #
###############

FROM base

# Install UV in final image too
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN groupadd -r app \
  && useradd -r -d /app -g app -N app

COPY --from=builder --chown=app:app /app /app
WORKDIR /app

ENV PYTHONUNBUFFERED=1

EXPOSE 80

ENTRYPOINT ["uv", "run", "api_server.py", "--host", "0.0.0.0", "--port", "8000"]