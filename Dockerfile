# Stage 1: ----- Build the React Vite frontend -----
FROM node:26.10.0-alpine3.24 AS frontend-builder

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
# Same interpreter path and patch as the runtime image so the copied venv stays valid.
FROM python:3.14.7-slim-trixie AS backend-builder
COPY --from=ghcr.io/astral-sh/uv:0.12.18 /uv /uvx /bin/

# Install the project into `/app`
WORKDIR /app

# uv configuration
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
# Copy from the cache instead of linking since it's a mounted volume
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
# Use the image interpreter in both stages; do not download another Python.
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#managing-python-interpreters
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

# Install the project's dependencies using the lockfile and settings
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-editable --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY health.py .
COPY README.md .
COPY musigree ./musigree

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-dev

# Stage 3: ----- Build the final image -----
# Runtime image has no uv binary. The venv was built against this same interpreter.
FROM python:3.14.7-slim-trixie AS final

# Optional build args. An omitted REDIS_PORT is empty here; the app treats that as unset.
ARG REDIS_HOST
ARG REDIS_PORT
ARG REDIS_USERNAME
ARG REDIS_PASSWORD
# Image metadata. Filled in by release.sh
ARG IMAGE_VERSION="1.0.88"
ARG IMAGE_CREATED="2026-09-28T16:52:56Z"
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
      org.opencontainers.image.version="${IMAGE_VERSION}" \
      org.opencontainers.image.source="https://github.com/aradburn/musigree" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.created="${IMAGE_CREATED}" \
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
COPY --from=frontend-builder --chown=nonroot:nonroot /app/frontend/public /app/frontend/public
COPY --from=frontend-builder --chown=nonroot:nonroot /app/frontend/templates /app/frontend/templates
# Copy the production built react app frontend
COPY --from=frontend-builder --chown=nonroot:nonroot /app/frontend/dist /app/frontend/dist

ENV MALLOC_ARENA_MAX=2

# RUN chmod 555 / && chmod 555 /bin /usr/bin /usr/sbin 2>/dev/null || true

# Use the non-root user to run our application
USER nonroot

# Expose the application port
EXPOSE 5000

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD ["python", "health.py"]

# Run the application with gunicorn
CMD ["gunicorn", \
     "--workers", "1", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:5000", \
     "--timeout", "60", \
     "--keep-alive", "5", \
     "--max-requests", "100000", \
     "--max-requests-jitter", "100", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "--worker-tmp-dir", "/dev/shm", \
     "musigree.app.fastapi_prod_app:app"]
