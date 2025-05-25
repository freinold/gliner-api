# gliner-api

A minimal FastAPI app serving GLiNER models

## Installation

Prerequisites:

- uv has to be installed.

```bash
# CPU version
uv sync --extra cpu

# GPU version
uv sync --extra gpu
```

## Usage

### Run the app directly

```bash
fastapi run main.py --host localhost
# or
uv run main.py
```

### Run with Docker

```bash
docker build -t gliner-api .
docker run -p 8000:8000 gliner-api
```

### Run with Docker Compose

```bash
docker-compose up --build
```

## Docs

Docs are served under `/docs` or `/redoc`.
