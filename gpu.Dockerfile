# Use a full image with uv pre-installed as builder
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder

# Install build tools needed for some packages
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     cmake \
#     libboost-all-dev \
#     libeigen3-dev \
#     && rm -rf /var/lib/apt/lists/*

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
    uv sync --no-dev --extra gpu --compile-bytecode

# Use slim image as runner
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS runner

# Metadata for the image
LABEL org.opencontainers.image.authors='Fabian Reinold <contact@freinold.eu>' \
    org.opencontainers.image.vendor='Fabian Reinold' \
    org.opencontainers.image.created='$(date -u +%Y-%m-%dT%H:%M:%SZ)' \
    org.opencontainers.image.revision='$(git rev-parse HEAD)' \
    org.opencontainers.image.version='$(git describe --tags --always)' \
    org.opencontainers.image.url='https://github.com/freinold/gliner-api/pkgs/container/gliner-api-gpu' \
    org.opencontainers.image.documentation='https://github.com/freinold/gliner-api/README.md' \
    org.opencontainers.image.source='https://github.com/freinold/gliner-api' \
    org.opencontainers.image.licenses='MIT' \
    org.opencontainers.image.title='gliner-api' \
    org.opencontainers.image.description='A minimal FastAPI app serving GLiNER models; this image is built for GPU only.'

# Install the project into `/app`
WORKDIR /app

# Nur das, was du wirklich brauchst, übernehmen:
COPY --from=builder /app /app
COPY --from=builder /app/.venv /app/.venv

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Set cache directory for Huggingface Models
ENV HF_HOME=/app/huggingface

# Disable tqdm for cleaner logs
ENV TQDM_DISABLE=1

# Disable python warnings
ENV PYTHONWARNINGS="ignore"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT ["uv", "run", "main.py"]

CMD ["--host", "0.0.0.0", "--port", "8080"]