from pydantic import AliasChoices, BaseModel, Field, TypeAdapter

from gliner_api.config import Config, get_config

config: Config = get_config()


class ErrorMessage(BaseModel):
    error: str = Field(description="Short error code")
    detail: str = Field(description="Detailed error explanaiton")


class Entity(BaseModel):
    start: int = Field(
        ge=0,
        description="Start index of the entity in the input text",
    )
    end: int = Field(
        ge=0,
        description="End index of the entity in the input text",
    )
    text: str = Field(
        description="Text of the entity, extracted from the input text",
    )
    type: str = Field(
        validation_alias=AliasChoices("type", "label"),
        description="Entity type or label",
    )
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score of the entity detection, between 0 and 1",
    )


class DetectionRequest(BaseModel):
    text: str = Field(
        description="Input text to analyze for entities",
        examples=["Sam Altman works at OpenAI in San Francisco."],
    )
    threshold: float = Field(
        default=config.default_threshold,
        description="Threshold for entity detection; if not set, uses default threshold (see gliner config from /api/info endpoint)",
        examples=[0.5],
    )
    entity_types: list[str] = Field(
        default=config.default_entities,
        description="List of entity types to detect; if not set, uses default entities (see gliner config from /api/info endpoint)",
        examples=[["person", "organization", "location"]],
    )


class DetectionResponse(BaseModel):
    entities: list[Entity] = Field(
        description="List of detected entities in the input text",
        examples=[
            [
                Entity(start=0, end=10, text="Sam Altman", type="person", score=0.95),
                Entity(start=20, end=26, text="OpenAI", type="organization", score=0.98),
                Entity(start=30, end=43, text="San Francisco", type="location", score=0.92),
            ]
        ],
    )


class BatchDetectionRequest(BaseModel):
    texts: list[str] = Field(
        description="List of input texts to analyze for entities",
        examples=[
            [
                "Sam Altman works at OpenAI in San Francisco.",
                "Queen Elizabeth was the head of the Windsor family and resided in London.",
            ],
        ],
    )
    threshold: float = Field(
        default=config.default_threshold,
        description="Threshold for entity detection; if not set, uses default threshold (see gliner config from /api/info endpoint)",
    )
    entity_types: list[str] = Field(
        default=config.default_entities,
        description="List of entity types to detect; if not set, uses default entities (see gliner config from /api/info endpoint)",
        examples=[["person", "organization", "location"]],
    )


class BatchDetectionResponse(BaseModel):
    entities: list[list[Entity]] = Field(
        description="List of lists of detected entities for each input text",
        examples=[
            [
                [
                    Entity(start=0, end=10, text="Sam Altman", type="person", score=0.95),
                    Entity(start=20, end=26, text="OpenAI", type="organization", score=0.98),
                    Entity(start=30, end=43, text="San Francisco", type="location", score=0.92),
                ],
                [
                    Entity(start=0, end=13, text="Queen Elizabeth", type="person", score=0.97),
                    Entity(start=30, end=47, text="Windsor family", type="organization", score=0.62),
                    Entity(start=41, end=47, text="London", type="location", score=0.93),
                ],
            ]
        ],
    )


class HealthCheckResponse(BaseModel):
    status: str = Field(
        description="Health status of the GLiNER API",
        examples=["healthy"],
    )


class InfoResponse(BaseModel):
    model_id: str = Field(
        default=config.model_id,
        description="The Huggingface model ID for a GLiNER model.",
        examples=["knowledgator/gliner-x-base-v0.5"],
    )
    default_entities: list[str] = Field(
        default=config.default_entities,
        description="The default entities to be detected, used if request includes no specific entities.",
        examples=[["person", "organization", "location"]],
    )
    default_threshold: float = Field(
        default=config.default_threshold,
        description="The default threshold for entity detection, used if request includes no specific threshold.",
        examples=[0.5],
        ge=0.0,
        le=1.0,
    )
    api_key_required: bool = Field(
        default=config.api_key is not None,
        description="Whether an API key is required for requests",
        examples=[False],
    )
    configured_use_case: str = Field(
        default=config.use_case,
        description="The configured use case for this deployment",
        examples=["general"],
    )


# Define TypeAdapter for Entity list once and reuse it
entity_list_adapter: TypeAdapter[list[Entity]] = TypeAdapter(list[Entity])
deep_entity_list_adapter: TypeAdapter[list[list[Entity]]] = TypeAdapter(list[list[Entity]])
