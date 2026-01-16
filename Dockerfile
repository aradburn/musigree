# Stage 1: ----- Build the React Vite frontend -----
FROM node:24-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy dependency files first for better layer caching
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies with cache mount
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Copy frontend source code
COPY frontend .

# Build the frontend
RUN npm run build

# Stage 2: ----- Build the Python backend -----
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS backend-builder

# Install the project into `/app`
WORKDIR /app

# uv configuration
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
# Copy from the cache instead of linking since it's a mounted volume
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#managing-python-interpreters
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-editable --no-dev \
    # Remove old versions of pip/setuptools/wheel from the managed interpreter \
    && uv pip uninstall --break-system-packages --python "$(uv python find --managed-python --system)" pip setuptools wheel

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY health.py .
COPY README.md .
COPY musigree ./musigree

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-dev

RUN find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /app -type f -name "*.pyc" -delete && \
    find /app -type f -name "*.pyo" -delete && \
    rm -rf /root/.cache/uv /tmp/* /var/tmp/*

# Stage 3: ----- Build the final image -----
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS final

# Re-declare build arguments for this stage
ENV NODE_ENV=production
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1
ENV REDIS_HOST=${REDIS_HOST}
ENV REDIS_PORT=${REDIS_PORT}
ENV REDIS_USERNAME=${REDIS_USERNAME}
ENV REDIS_PASSWORD=${REDIS_PASSWORD}

# Add metadata labels
LABEL maintainer="Andy Radburn <andy.radburn@outlook.com>" \
      org.opencontainers.image.title="musigree" \
      org.opencontainers.image.description="Interactive visualization of the Discogs database" \
      org.opencontainers.image.version="1.0.55" \
      org.opencontainers.image.source="https://github.com/aradburn/musigree" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.created="2026-01-16T01:58:21Z" \
      org.opencontainers.image.revision="" \
      security.scan.enabled="true"

# Install packages needed for deployment
# Combine commands and clean up in single layer to reduce image size
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* /tmp/* /var/tmp/*

# Setup a non-root user
RUN groupadd --system --gid 1000 nonroot && \
    useradd --system --gid 1000 --uid 1000 --create-home nonroot

WORKDIR /app

# Create app directory with proper ownership
# Note: chown happens during COPY with --chown flag, but we ensure directory exists
RUN mkdir -p /app && chown -R nonroot:nonroot /app

# Copy the virtual environment first (largest layer, better caching)
COPY --from=backend-builder --chown=nonroot:nonroot /app/.venv /app/.venv

# Copy source code and lock files
COPY --from=backend-builder --chown=nonroot:nonroot /app/pyproject.toml /app/pyproject.toml
COPY --from=backend-builder --chown=nonroot:nonroot /app/uv.lock /app/uv.lock
COPY --from=backend-builder --chown=nonroot:nonroot /app/README.md /app/README.md
COPY --from=backend-builder --chown=nonroot:nonroot /app/health.py /app/health.py
COPY --from=backend-builder --chown=nonroot:nonroot /app/musigree /app/musigree

# Copy the frontend static files
COPY --from=frontend-builder --chown=nonroot:nonroot --chmod=755 /app/frontend/public /app/frontend/public
COPY --from=frontend-builder --chown=nonroot:nonroot --chmod=755 /app/frontend/templates /app/frontend/templates
# Copy the production built react app frontend
COPY --from=frontend-builder --chown=nonroot:nonroot --chmod=755 /app/frontend/dist /app/frontend/dist

# Place executables in the environment at the front of the path
# The venv contains Python and all dependencies
ENV PATH="/app/.venv/bin:$PATH"

# RUN chmod 555 / && chmod 555 /bin /usr/bin /usr/sbin 2>/dev/null || true

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Use the non-root user to run our application
USER nonroot

# Expose the application port
EXPOSE 5000

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD ["python", "health.py"]

# Run the application with gunicorn
CMD ["gunicorn", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:5000", \
     "--worker-connections", "1000", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "musigree.app.fastapi_prod_app:app"]
