# =============================================================
# FinLens AI Backend — Multi-Stage Production Dockerfile
# =============================================================

# -------------------------------------------------------------
# Stage 1: Build virtual environment with uv
# -------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:0.6.5-python3.12-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation and copy mode
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies using layer cache
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy application source code and install project package
COPY app/ ./app
COPY README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# -------------------------------------------------------------
# Stage 2: Minimal, secure production runtime
# -------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

# Install curl for healthcheck and ca-certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root user and group
RUN groupadd -g 10001 finlens && \
    useradd -u 10001 -g finlens -s /bin/bash -m finlens

WORKDIR /app

# Environment configuration
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production

# Copy virtualenv and app from builder with non-root ownership
COPY --from=builder --chown=finlens:finlens /app/.venv /app/.venv
COPY --from=builder --chown=finlens:finlens /app/app /app/app

# Switch to unprivileged user
USER finlens

# Expose backend service port
EXPOSE 8000

# Native health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

# Launch uvicorn production server
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-1}"]
