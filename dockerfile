# Base Python
FROM python:3.12-slim-bookworm AS base

# Bring in uv (pin to a specific tag for reproducibility)
COPY --from=ghcr.io/astral-sh/uv:0.7.14-python3.12-bookworm-slim /uv /uvx /usr/local/bin/

# Make uv fast & deterministic in containers
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# ---- Dependencies layer (cached) ----
# Copy only lockfile & project metadata first
COPY uv.lock pyproject.toml ./
# Install project deps into a venv under /app/.venv (no dev deps, no project yet)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# ---- App layer ----
# Now copy the rest (invalidates only when source changes)
COPY . .

# Sync including your project (still no dev deps)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Create a non-root user and ensure venv is on PATH
RUN useradd -m -u 10001 app
ENV PATH="/app/.venv/bin:$PATH"

# Start script to respect $PORT (CF sets this at runtime)
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

USER app
# Do NOT set EXPOSE; CF will set PORT. If you prefer EXPOSE, use only one port in CF.
# EXPOSE 8000

# Use a tiny shell wrapper so $PORT expands
ENTRYPOINT ["/app/start.sh"]