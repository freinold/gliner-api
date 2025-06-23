# gliner-api

[![License](https://img.shields.io/github/license/freinold/gliner-api)](https://github.com/freinold/gliner-api/blob/main/LICENSE)
[![CodeQL](https://github.com/freinold/gliner-api/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/freinold/gliner-api/actions/workflows/github-code-scanning/codeql)
[![Build Container Image](https://github.com/freinold/gliner-api/actions/workflows/docker-release.yml/badge.svg)](https://github.com/freinold/gliner-api/actions/workflows/docker-release.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/freinold/gliner-api/badge)](https://scorecard.dev/viewer/?uri=github.com/freinold/gliner-api)

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
