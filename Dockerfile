# Stage 1: Build the React Vite frontend
FROM node:24-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend .
RUN npm run build

# Stage 2: Build the Python backend
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot \
 && useradd --system --gid 999 --uid 999 --create-home nonroot

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
#ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
#ENV UV_LINK_MODE=copy

# Ensure installed tools can be executed out of the box
#ENV UV_TOOL_BIN_DIR=/usr/local/bin

#ENV UV_PROJECT_ENVIRONMENT=/app

# Install the project's dependencies using the lockfile and settings
#RUN --mount=type=cache,target=/root/.cache/uv \
#    --mount=type=bind,source=uv.lock,target=uv.lock \
#    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
#    uv sync --locked --no-install-project --no-dev

#RUN uv sync --locked --no-install-project --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching

COPY pyproject.toml .
COPY uv.lock .
COPY wsgi.py .
COPY README.md .
COPY musigree ./musigree

# Copy the built frontend static files into the "static" directory
COPY frontend/public ./frontend/public
COPY frontend/templates ./frontend/templates

# Copy the production built react app frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

#RUN --mount=type=cache,target=/root/.cache/uv \
#    uv sync --locked --no-dev
RUN uv cache clean
RUN uv sync --locked

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Use the non-root user to run our application
USER nonroot

EXPOSE 8080
CMD ["uvicorn", "musigree.app.fastapi_prod_app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--no-access-log", "--log-level", "debug"]