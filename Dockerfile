# Stage 1: ----- Build the React Vite frontend -----
FROM node:24-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend .
RUN npm run build

# Stage 2: ----- Build the Python backend -----
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS backend-builder

# Install uv (static binary)
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
#COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install the project into `/app`
WORKDIR /app

# uv configuration
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
# Copy from the cache instead of linking since it's a mounted volume
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#managing-python-interpreters
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_INSTALL_DIR=/opt/python

# Ensure installed tools can be executed out of the box
#ENV UV_TOOL_BIN_DIR=/usr/local/bin

#ENV UV_PROJECT_ENVIRONMENT=/app

# Install the project's dependencies using the lockfile and settings
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
#    --mount=type=bind,source=uv.lock,target=uv.lock \
#    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable --no-dev \
    # Remove old versions of pip/setuptools/wheel from the managed interpreter \
    && uv pip uninstall --break-system-packages --python "$(uv python find --managed-python --system)" pip setuptools wheel

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY wsgi.py .
COPY README.md .
COPY musigree ./musigree

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-dev

# Stage 3: ----- Build the final image -----
FROM ghcr.io/astral-sh/uv:bookworm-slim AS final

# Install packages needed for deployment
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y curl && \
    rm -rf /var/lib/apt/lists /var/cache/apt/archives

# Setup a non-root user
RUN groupadd --system --gid 1000 nonroot \
 && useradd --system --gid 1000 --uid 1000 --create-home nonroot

WORKDIR /app

# Copy managed Python + app (venv included), as non-root
COPY --from=backend-builder --chown=nonroot:nonroot --chmod=755 /opt/python /opt/python
COPY --from=backend-builder --chown=nonroot:nonroot --chmod=755 /app /app
# Copy the frontend static files
COPY --from=frontend-builder --chown=nonroot:nonroot --chmod=755 /app/frontend/public /app/frontend/public
COPY --from=frontend-builder --chown=nonroot:nonroot --chmod=755 /app/frontend/templates /app/frontend/templates
# Copy the production built react app frontend
COPY --from=frontend-builder --chown=nonroot:nonroot --chmod=755 /app/frontend/dist /app/frontend/dist

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Use the non-root user to run our application
USER nonroot

EXPOSE 5000
CMD ["uvicorn", "musigree.app.fastapi_prod_app:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "1", "--no-access-log", "--log-level", "debug"]