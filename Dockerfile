# Stage 1: ----- Build the React Vite frontend -----
FROM node:26.13-alpine3.24 AS frontend-builder

WORKDIR /app/frontend

# Copy dependency files first for better layer caching
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies with cache mount. Ignore lifecycle scripts so a
# dependency cannot run code during the image build.
RUN --mount=type=cache,target=/root/.npm \
    npm ci --ignore-scripts

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
# Redis and database settings are runtime environment variables. Do not pass
# them as build args: build args and ENV are stored in the image config.
FROM python:3.14.7-slim-trixie AS final

# Image metadata. Filled in by release.sh
ARG IMAGE_VERSION="1.1.7"
ARG IMAGE_CREATED="2026-11-18T21:46:37Z"
# Keep interpreter scratch off the application tree so a read-only root
# filesystem only needs a tmpfs on /tmp. Gunicorn heartbeats use /dev/shm.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONSAFEPATH=1 \
    HOME=/tmp \
    TMPDIR=/tmp \
    XDG_CACHE_HOME=/tmp \
    XDG_CONFIG_HOME=/tmp \
    MALLOC_ARENA_MAX=2

# Add metadata labels
LABEL maintainer="Andy Radburn <andy.radburn@outlook.com>" \
      org.opencontainers.image.title="musigree" \
      org.opencontainers.image.description="Interactive visualization of the Discogs database" \
      org.opencontainers.image.version="${IMAGE_VERSION}" \
      org.opencontainers.image.source="https://github.com/aradburn/musigree" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.created="${IMAGE_CREATED}" \
      security.scan.enabled="true"

# Refresh CA certificates and apply base-image security updates in one layer.
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && \
    apt-get upgrade -y --no-install-recommends \
        -o Dpkg::Options::=--force-confdef \
        -o Dpkg::Options::=--force-confold && \
    apt-get install --no-install-recommends -y ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* /tmp/* /var/tmp/*

# Fixed uid/gid that does not collide with a typical host user (uid 1000).
# No home directory and no login shell. HOME is the tmpfs mounted at /tmp.
RUN groupadd --system --gid 65532 nonroot && \
    useradd --system --uid 65532 --gid nonroot \
        --no-create-home --home-dir /tmp --shell /usr/sbin/nologin \
        --no-log-init nonroot

WORKDIR /app

# Copy the virtual environment first (largest layer, better caching).
# mode 0555: root-owned, readable and executable, not writable by the runtime user.
COPY --from=backend-builder --chmod=555 /app/.venv /app/.venv

# Runtime source. Lockfiles and the README are not needed once the venv exists.
COPY --from=backend-builder --chmod=555 /app/health.py /app/health.py
COPY --from=backend-builder --chmod=555 /app/musigree /app/musigree

# Copy the frontend static files
COPY --from=frontend-builder --chmod=555 /app/frontend/public /app/frontend/public
COPY --from=frontend-builder --chmod=555 /app/frontend/templates /app/frontend/templates
# Copy the production built react app frontend
COPY --from=frontend-builder --chmod=555 /app/frontend/dist /app/frontend/dist

# Drop setuid/setgid from privileged binaries in the base image.
# /tmp and /var/tmp stay available as mount points; run the container with a
# read-only root and tmpfs on those paths (see docker-compose.yaml and
# docker-compose-smoketest.yaml).
RUN set -eu; \
    for dir in /bin /usr/bin /usr/sbin /usr/lib /usr/libexec; do \
        if [ -d "$dir" ]; then \
            find "$dir" -xdev -type f -perm /6000 -exec chmod a-s {} +; \
        fi; \
    done

# Use the non-root user to run our application
USER 65532:65532

# Expose the application port
EXPOSE 5000

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=3s --start-period=120s --retries=3 \
    CMD ["python", "health.py"]

# Run the application with gunicorn with four workers
CMD ["gunicorn", \
     "--workers", "4", \
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
