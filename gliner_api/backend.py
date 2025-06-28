from contextlib import asynccontextmanager
from logging import Logger
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from gliner import GLiNER
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from gliner_api.config import Config, get_config
from gliner_api.datamodel import (
    BatchDetectionRequest,
    BatchDetectionResponse,
    DetectionRequest,
    DetectionResponse,
    Entity,
    ErrorMessage,
    HealthCheckResponse,
    InfoResponse,
    deep_entity_list_adapter,
    entity_list_adapter,
)
from gliner_api.logging import getLogger

gliner: GLiNER | None = None

logger: Logger = getLogger("gliner-api.backend")
config: Config = get_config()
logger.info(f"Loaded configuration for use case {config.use_case}.")
logger.debug(f"Configuration:\n{config.model_dump_json(indent=2)}")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Lifespan event handler to initialize GLiNER model and configuration."""
    global gliner
    logger.info("Initializing GLiNER API...")
    logger.info(f"Loading GLiNER model {config.model_id}...")
    gliner = GLiNER.from_pretrained(config.model_id)
    logger.info("GLiNER model loaded.")
    yield

    gliner = None


app: FastAPI = FastAPI(
    title="GLiNER Detection API",
    description="API for GLiNER entity detection",
    version="0.1.0",
    lifespan=lifespan,
)

bearer: HTTPBearer = HTTPBearer(
    auto_error=False,
    description="API Key for authentication",
    bearerFormat="API Key",
)


def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(dependency=bearer)) -> None:
    if config.api_key is None:
        return
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail={"error": "InvalidAuthenticationScheme", "message": "Authentication scheme must be Bearer"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    if credentials.credentials != config.api_key:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail={"error": "InvalidAPIKey", "message": "Provided API key is invalid"},
        )
    return


@app.get(path="/", include_in_schema=False)
async def docs_forward() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.post(
    path="/api/invoke",
    responses={
        200: {"model": DetectionResponse},
        401: {"model": ErrorMessage},
        403: {"model": ErrorMessage},
        500: {"model": ErrorMessage},
    },
    dependencies=[Depends(dependency=verify_api_key)],
)
async def detect_entities(
    request: DetectionRequest,
) -> DetectionResponse:
    """Detect entities in text using specified detectors."""
    if gliner is None:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ModelLoadError",
                "message": "No GLiNER model loaded",
            },
        )

    try:
        raw_entities: list[dict[str, Any]] = gliner.predict_entities(
            text=request.text,
            labels=request.entity_types,
            flat_ner=True,
            threshold=request.threshold,
            multi_label=False,
        )

        parsed_entities: list[Entity] = entity_list_adapter.validate_python(raw_entities)
        return DetectionResponse(entities=parsed_entities)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(object=e))


@app.post(
    path="/api/batch",
    responses={
        200: {"model": DetectionResponse},
        401: {"model": ErrorMessage},
        403: {"model": ErrorMessage},
        500: {"model": ErrorMessage},
    },
    dependencies=[Depends(dependency=verify_api_key)],
)
async def detect_entities_batch(
    request: BatchDetectionRequest,
) -> BatchDetectionResponse:
    """Detect entities in a batch of texts using specified detectors."""
    if gliner is None:
        raise HTTPException(status_code=500, detail="Server Error: No GLiNER model loaded")

    try:
        raw_entities_list: list[list[dict[str, Any]]] = gliner.batch_predict_entities(
            texts=request.texts,
            labels=request.entity_types,
            flat_ner=True,
            threshold=request.threshold,
            multi_label=False,
        )

        parsed_entities_list: list[list[Entity]] = deep_entity_list_adapter.validate_python(raw_entities_list)
        return BatchDetectionResponse(entities=parsed_entities_list)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    return HealthCheckResponse(status="healthy")


@app.get("/api/info")
async def info() -> InfoResponse:
    """Information on configured model and default settings."""
    if config is None:
        raise HTTPException(status_code=500, detail="Server Error: No config present")

    return InfoResponse(
        api_key_required=config.api_key is not None,
        model_id=config.model_id,
        default_entities=config.default_entities,
        default_threshold=config.default_threshold,
        configured_use_case=config.use_case,
    )
