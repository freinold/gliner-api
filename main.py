import os
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from gliner import GLiNER
from pydantic import BaseModel, Field

# Models to load
MODELS = {
    "pii": "E3-JSI/gliner-multi-pii-domains-v1",
    "medical": "Ihor/gliner-biomed-large-v1.0",
}

# Entity configurations
ENTITY_CONFIGS = {
    "pii": {
        "entities": {
            "person",
            "email",
            "phone number",
            "address",
            "iban",
            "credit card number",
            "location",
            "age",
            "date",
            "country",
            "state",
            "city",
            "zip code",
        },
        "default_threshold": 0.5,
    },
    "medical": {
        "entities": {
            "Anatomy",
            "Bacteria",
            "Demographic information",
            "Disease",
            "Doctor",
            "Drug dosage",
            "Drug frequency",
            "Drug",
            "Illness",
            "Lab test value",
            "Lab test",
            "Medical Worker",
            "Procedure",
            "Symptom",
            "Test",
            "Treatment",
            "Virus",
        },
        "default_threshold": 0.3,
    },
}

# Global variable to store loaded models
models: Dict[str, GLiNER] = {}


class Entity(BaseModel):
    start: int
    end: int
    text: str
    label: str
    score: float = Field(ge=0.0, le=1.0)
    detector: str = Field(description="Name of the detector that found this entity")


class DetectionRequest(BaseModel):
    text: str
    detectors: List[str] = Field(default=["pii", "medical"], description="List of detectors to use")
    threshold: Optional[float] = Field(default=None, description="Override threshold for all detectors")


class DetectionResponse(BaseModel):
    entities: List[Entity]


class BatchDetectionRequest(BaseModel):
    texts: List[str]
    detectors: List[str] = Field(default=["pii", "medical"], description="List of detectors to use")
    threshold: Optional[float] = Field(default=None, description="Override threshold for all detectors")


class BatchDetectionResponse(BaseModel):
    results: List[List[Entity]]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load models on startup
    print("Loading GLiNER models...")
    for name, model_path in MODELS.items():
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


def merge_overlapping_entities(entities: List[Entity]) -> List[Entity]:
    """
    Merge overlapping entities, keeping larger entities and higher confidence scores.

    Rules:
    1. If entities have the same span, keep the one with higher confidence
    2. If entities overlap, keep the larger one
    3. If same size and overlap, keep the one with higher confidence
    """
    if not entities:
        return []

    # Sort by start position, then by length (descending), then by score (descending)
    sorted_entities = sorted(entities, key=lambda e: (e.start, -(e.end - e.start), -e.score))

    merged = []
    for entity in sorted_entities:
        # Check if this entity overlaps with any already merged entity
        should_add = True
        for i, merged_entity in enumerate(merged):
            # Check for overlap
            if entity.start < merged_entity.end and entity.end > merged_entity.start:
                # Entities overlap
                entity_length = entity.end - entity.start
                merged_length = merged_entity.end - merged_entity.start

                # If same span, keep higher confidence
                if entity.start == merged_entity.start and entity.end == merged_entity.end:
                    if entity.score > merged_entity.score:
                        merged[i] = entity
                    should_add = False
                    break
                # If current entity is larger, replace the merged one
                elif entity_length > merged_length:
                    merged[i] = entity
                    should_add = False
                    break
                # If merged entity is larger or same size with higher score, skip current
                elif merged_length > entity_length or merged_entity.score >= entity.score:
                    should_add = False
                    break

        if should_add:
            merged.append(entity)

    # Sort final result by start position
    return sorted(merged, key=lambda e: e.start)


@app.post("/detect", response_model=DetectionResponse)
async def detect_entities(request: DetectionRequest):
    """Detect entities in text using specified detectors."""
    try:
        all_entities = []

        for detector_name in request.detectors:
            if detector_name not in models:
                raise HTTPException(status_code=400, detail=f"Unknown detector: {detector_name}")

            model = models[detector_name]
            config = ENTITY_CONFIGS[detector_name]
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
                config = ENTITY_CONFIGS[detector_name]
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
                "model_path": MODELS[name],
                "entities": list(ENTITY_CONFIGS[name]["entities"]),
                "default_threshold": ENTITY_CONFIGS[name]["default_threshold"],
            }
            for name in models.keys()
        }
    }


if __name__ == "__main__":
    host = os.getenv("GLINER_API_HOST", "0.0.0.0")
    port = int(os.getenv("GLINER_API_PORT", "8000"))
    workers = int(os.getenv("GLINER_API_WORKERS", "1"))

    uvicorn.run(app, host=host, port=port, workers=workers)
