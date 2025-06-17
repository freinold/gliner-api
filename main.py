import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from gliner import GLiNER

models = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load models on startup
    print("Loading GLiNER models...")
    for name, model_path in models.items():
        print(f"Loading {name} model: {model_path}")
        models[name] = GLiNER.from_pretrained(model_path)
        print(f"✓ {name} model loaded successfully")

    print("All models loaded successfully!")
    yield

    # Cleanup on shutdown
    models.clear()


app = FastAPI(
    title="GLiNER Detection Service",
    description="Remote service for GLiNER entity detection",
    version="1.0.0",
    lifespan=lifespan,
)


if __name__ == "__main__":
    host = os.getenv("GLINER_API_HOST", "0.0.0.0")
    port = int(os.getenv("GLINER_API_PORT", "8000"))
    workers = int(os.getenv("GLINER_API_WORKERS", "1"))

    uvicorn.run(app, host=host, port=port, workers=workers)
