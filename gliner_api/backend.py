from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from gliner import GLiNER

from gliner_api.datamodel import BatchDetectionRequest, BatchDetectionResponse, DetectionRequest, DetectionResponse, Entity
from gliner_api.helpers import merge_overlapping_entities

models: dict[str, str | GLiNER] = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
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


@app.post("/detect", response_model=DetectionResponse)
async def detect_entities(request: DetectionRequest):
    """Detect entities in text using specified detectors."""
    try:
        all_entities = []

        for detector_name in request.detectors:
            if detector_name not in models:
                raise HTTPException(status_code=400, detail=f"Unknown detector: {detector_name}")

            model = models[detector_name]
            config = {}
            threshold = request.threshold if request.threshold is not None else config["default_threshold"]

            # Predict entities
            raw_entities = model.predict_entities(text=request.text, labels=config["entities"], threshold=threshold)

            # Convert to our Entity model with detector info
            for entity_dict in raw_entities:
                entity = Entity(
                    start=entity_dict["start"],
                    end=entity_dict["end"],
                    text=entity_dict["text"],
                    label=entity_dict["label"],
                    score=entity_dict["score"],
                    detector=detector_name,
                )
                all_entities.append(entity)

        # Merge overlapping entities
        merged_entities = merge_overlapping_entities(all_entities)

        return DetectionResponse(entities=merged_entities)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detect/batch", response_model=BatchDetectionResponse)
async def detect_entities_batch(request: BatchDetectionRequest):
    """Detect entities in a batch of texts using specified detectors."""
    try:
        batch_results = []

        for text in request.texts:
            text_entities = []

            for detector_name in request.detectors:
                if detector_name not in models:
                    raise HTTPException(status_code=400, detail=f"Unknown detector: {detector_name}")

                model = models[detector_name]
                config = {}
                threshold = request.threshold if request.threshold is not None else config["default_threshold"]

                # Predict entities
                raw_entities = model.predict_entities(text=text, labels=config["entities"], threshold=threshold)

                # Convert to our Entity model with detector info
                for entity_dict in raw_entities:
                    entity = Entity(
                        start=entity_dict["start"],
                        end=entity_dict["end"],
                        text=entity_dict["text"],
                        label=entity_dict["label"],
                        score=entity_dict["score"],
                        detector=detector_name,
                    )
                    text_entities.append(entity)

            # Merge overlapping entities for this text
            merged_entities = merge_overlapping_entities(text_entities)
            batch_results.append(merged_entities)

        return BatchDetectionResponse(results=batch_results)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "models_loaded": list(models.keys())}


@app.get("/models")
async def list_models():
    """List available models and their configurations."""
    return {
        "models": {
            name: {
                "model_path": models[name],
                "entities": {},
                "default_threshold": 0,
            }
            for name in models.keys()
        }
    }
