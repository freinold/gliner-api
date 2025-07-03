from contextlib import asynccontextmanager
from logging import Logger
from sys import exit as sys_exit
from time import perf_counter
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Response
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
from gliner_api.metrics import app_state_metric, failed_auth_metric, failed_inference_metric, inference_time_metric, requests_metric

gliner: GLiNER | None = None

logger: Logger = getLogger("gliner-api.backend")
config: Config = get_config()
logger.info(f"Loaded configuration for use case {config.use_case}.")
logger.debug(f"Configuration:\n{config.model_dump_json(indent=2)}")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Lifespan event handler to initialize GLiNER model and configuration."""
    app_state_metric.state("starting")
    global gliner
    logger.info("Initializing GLiNER API...")
    logger.info(f"Loading GLiNER model {config.model_id}...")
    try:
        gliner = GLiNER.from_pretrained(
            config.model_id,
            load_onnx_model=config.onnx_enabled,
            load_tokenizer=True,
            onnx_model_file=config.onnx_model_path,
        )
        gliner.eval()
        logger.info("GLiNER model loaded.")
    except Exception as e:
        logger.exception("Failed to load GLiNER model", exc_info=e)
        sys_exit(1)

    app_state_metric.state("running")
    yield

    app_state_metric.state("stopping")
    gliner = None


app: FastAPI = FastAPI(
    title="GLiNER API - Backend",
    description="API for GLiNER entity detection",
    version="0.1.0",
    lifespan=lifespan,
)

bearer: HTTPBearer = HTTPBearer(
    auto_error=False,
    description="API Key for authentication",
    bearerFormat="API Key",
)


@failed_auth_metric.count_exceptions(HTTPException)
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


if not config.frontend_enabled:
    # Enable docs forward if we got no frontend
    @app.get(path="/", include_in_schema=False)
    async def docs_forward() -> RedirectResponse:
        """Redirect root path to API documentation."""
        requests_metric.labels("GET", "/docs").inc()
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
    response: Response,
) -> DetectionResponse:
    """Detect entities in a single text."""
    requests_metric.labels("POST", "/api/invoke").inc()

    if gliner is None:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ModelLoadError",
                "message": "No GLiNER model loaded",
            },
        )

    text_length: int = len(request.text)
    response.headers["X-Text-Length"] = str(text_length)

    try:
        start_time: float = perf_counter()
        raw_entities: list[dict[str, Any]] = gliner.predict_entities(
            text=request.text,
            labels=request.entity_types,
            flat_ner=request.flat_ner,
            threshold=request.threshold,
            multi_label=request.multi_label,
        )
        inference_time: float = perf_counter() - start_time
        inference_time_metric.labels("POST", "/api/invoke").observe(inference_time)
        response.headers["X-Inference-Time"] = f"{inference_time:.4f}"
        logger.debug(f"Entity detection took {inference_time:.4f} seconds for text of length {text_length}.")

        parsed_entities: list[Entity] = entity_list_adapter.validate_python(raw_entities)
        response.headers["X-Entity-Count"] = str(len(parsed_entities))

        return DetectionResponse(entities=parsed_entities)

    except Exception as e:
        failed_inference_metric.labels("POST", "/api/invoke").inc()
        raise HTTPException(status_code=500, detail=str(object=e))


@app.post(
    path="/api/batch",
    responses={
        200: {"model": BatchDetectionResponse},
        401: {"model": ErrorMessage},
        403: {"model": ErrorMessage},
        500: {"model": ErrorMessage},
    },
    dependencies=[Depends(dependency=verify_api_key)],
)
async def detect_entities_batch(
    request: BatchDetectionRequest,
    response: Response,
) -> BatchDetectionResponse:
    """Detect entities in multiple texts."""
    requests_metric.labels("POST", "/api/batch").inc()

    if gliner is None:
        raise HTTPException(status_code=500, detail="Server Error: No GLiNER model loaded")

    total_text_length: int = sum(len(text) for text in request.texts)
    response.headers["X-Text-Length"] = str(total_text_length)

    try:
        start_time: float = perf_counter()
        raw_entities_list: list[list[dict[str, Any]]] = gliner.batch_predict_entities(
            texts=request.texts,
            labels=request.entity_types,
            flat_ner=request.flat_ner,
            threshold=request.threshold,
            multi_label=request.multi_label,
        )
        inference_time: float = perf_counter() - start_time
        inference_time_metric.labels("POST", "/api/batch").observe(inference_time)
        response.headers["X-Inference-Time"] = f"{inference_time:.4f}"
        logger.debug(
            f"Batch entity detection took {inference_time:.4f} seconds for {len(request.texts)} texts of total length {total_text_length}."
        )

        parsed_entities_list: list[list[Entity]] = deep_entity_list_adapter.validate_python(raw_entities_list)
        response.headers["X-Entity-Count"] = str(sum(len(entities) for entities in parsed_entities_list))

        return BatchDetectionResponse(entities=parsed_entities_list)

    except Exception as e:
        failed_inference_metric.labels("POST", "/api/batch").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    requests_metric.labels("GET", "/api/health").inc()
    return HealthCheckResponse(status="healthy")


@app.get("/api/info")
async def info() -> InfoResponse:
    """Information on configured model and default settings."""
    requests_metric.labels("GET", "/api/info").inc()
    return InfoResponse(
        api_key_required=config.api_key is not None,
        model_id=config.model_id,
        default_entities=config.default_entities,
        default_threshold=config.default_threshold,
        configured_use_case=config.use_case,
        onnx_enabled=config.onnx_enabled,
    )
