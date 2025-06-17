from pydantic import BaseModel, Field


class Entity(BaseModel):
    start: int
    end: int
    text: str
    label: str
    score: float = Field(ge=0.0, le=1.0)
    detector: str = Field(description="Name of the detector that found this entity")


class DetectionRequest(BaseModel):
    text: str
    detectors: list[str] = Field(default=["pii", "medical"], description="List of detectors to use")
    threshold: float | None = Field(default=None, description="Override threshold for all detectors")


class DetectionResponse(BaseModel):
    entities: list[Entity]


class BatchDetectionRequest(BaseModel):
    texts: list[str]
    detectors: list[str] = Field(
        default=[
            "pii",
            "medical",
        ],
        description="List of detectors to use",
    )
    threshold: float | None = Field(default=None, description="Override threshold for all detectors")


class BatchDetectionResponse(BaseModel):
    results: list[list[Entity]]


class ModelConfig(BaseModel):
    model: str = Field(
        default="knowledgator/gliner-x-base-v0.5",
        description="Model identifier",
    )
    use_case: str = Field(
        default="general",
        description="Use case for the model",
    )
    default_entities: list[str] = Field(
        default=[
            "Person",
            "Organization",
            "Location",
        ],
        description="Default entities to detect",
    )
    default_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Default threshold for entity detection",
    )


class ModelListResponse(BaseModel):
    models: list[ModelConfig] = Field(
        default=[
            ModelConfig(
                model="knowledgator/gliner-x-base-v0.5",
                use_case="general",
                default_entities=["Person", "Organization", "Location"],
                default_threshold=0.5,
            )
        ],
        description="List of available models with their configurations",
    )
