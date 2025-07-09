# Use a full image with uv pre-installed as builder
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder

# Install build tools needed for some packages
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libboost-all-dev \
    libeigen3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Copy the application files into the container
COPY . /app

# Install the dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --extra cpu --extra frontend

# Use slim image as runner
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim@sha256:235c2e8419851c1d539e2b19033d56aaf82670bfaaa155e20ac6b21260dc0be9 AS runner

# Metadata for the image
ARG IMAGE_CREATED="unknown"
ARG IMAGE_REVISION="unknown"
ARG IMAGE_VERSION="unknown"
LABEL org.opencontainers.image.authors='Fabian Reinold <contact@freinold.eu>' \
    org.opencontainers.image.vendor='Fabian Reinold' \
    org.opencontainers.image.created="$IMAGE_CREATED" \
    org.opencontainers.image.revision="$IMAGE_REVISION" \
    org.opencontainers.image.version="$IMAGE_VERSION" \
    org.opencontainers.image.url='https://github.com/freinold/gliner-api/pkgs/container/gliner-api' \
    org.opencontainers.image.documentation='https://github.com/freinold/gliner-api/README.md' \
    org.opencontainers.image.source='https://github.com/freinold/gliner-api' \
    org.opencontainers.image.licenses='MIT' \
    org.opencontainers.image.title='gliner-api' \
    org.opencontainers.image.description='A minimal FastAPI app serving GLiNER models; this image is built for CPU only.'

# Install the project into `/app`
WORKDIR /app

# Create a non-root user and group with UID/GID 1000
RUN groupadd -g 1000 appuser && \
    useradd -m -u 1000 -g appuser appuser

# Set cache directory for Huggingface Models and set ownership to appuser
RUN mkdir -p /app/huggingface && chown -R appuser:appuser /app/huggingface
ENV HF_HOME=/app/huggingface

# Copy the application files from the builder stage
COPY --from=builder --chown=appuser:appuser /app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Disable tqdm for cleaner logs
ENV TQDM_DISABLE=1
ENV HF_HUB_DISABLE_PROGRESS_BARS=1

# Disable python warnings
ENV PYTHONWARNINGS="ignore"

# Switch to non-root user
USER appuser

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT ["python", "main.py"]

CMD ["--host", "0.0.0.0", "--port", "8080"]