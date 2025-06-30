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
        examples=["Steve Jobs founded Apple in Cupertino, California on April 1, 1976."],
    )
    threshold: float = Field(
        default=config.default_threshold,
        description="Threshold for entity detection; if not set, uses default threshold (see gliner config from /api/info endpoint)",
        examples=[0.5],
    )
    entity_types: list[str] = Field(
        default=config.default_entities,
        description="List of entity types to detect; if not set, uses default entities (see gliner config from /api/info endpoint)",
        examples=[["person", "organization", "location", "date"]],
    )
    flat_ner: bool = Field(
        default=True,
        description="Whether to return flat entities (default: True). If False, returns nested entities.",
        examples=[True],
    )
    multi_label: bool = Field(
        default=False,
        description="Whether to allow multiple labels per entity (default: False). If True, there can be multiple entities returned for the same span.",
        examples=[False],
    )


class DetectionResponse(BaseModel):
    entities: list[Entity] = Field(
        description="List of detected entities in the input text",
        examples=[
            [
                Entity(start=0, end=10, text="Steve Jobs", type="person", score=0.99),
                Entity(start=19, end=24, text="Apple", type="organization", score=0.98),
                Entity(start=28, end=37, text="Cupertino", type="location", score=0.98),
                Entity(start=39, end=49, text="California", type="location", score=0.99),
                Entity(start=53, end=66, text="April 1, 1976", type="date", score=0.68),
            ]
        ],
    )


class BatchDetectionRequest(BaseModel):
    texts: list[str] = Field(
        description="List of input texts to analyze for entities",
        examples=[
            [
                "Steve Jobs founded Apple in Cupertino, California on April 1, 1976.",
                "Until her death in 2022, the head of the Windsor family, Queen Elizabeth, resided in London.",
            ],
        ],
    )
    threshold: float = Field(
        default=config.default_threshold,
        description="Threshold for entity detection; if not set, uses default threshold (see gliner config from /api/info endpoint)",
        examples=[0.3],
    )
    entity_types: list[str] = Field(
        default=config.default_entities,
        description="List of entity types to detect; if not set, uses default entities (see gliner config from /api/info endpoint)",
        examples=[["person", "organization", "location", "date"]],
    )
    flat_ner: bool = Field(
        default=True,
        description="Whether to return flat entities (default: True). If False, returns nested entities.",
        examples=[True],
    )
    multi_label: bool = Field(
        default=False,
        description="Whether to allow multiple labels per entity (default: False). If True, there can be multiple entities returned for the same span.",
        examples=[False],
    )


class BatchDetectionResponse(BaseModel):
    entities: list[list[Entity]] = Field(
        description="List of lists of detected entities for each input text",
        examples=[
            [
                [
                    Entity(start=0, end=10, text="Steve Jobs", type="person", score=0.99),
                    Entity(start=19, end=24, text="Apple", type="organization", score=0.98),
                    Entity(start=28, end=37, text="Cupertino", type="location", score=0.98),
                    Entity(start=39, end=49, text="California", type="location", score=0.99),
                    Entity(start=53, end=66, text="April 1, 1976", type="date", score=0.68),
                ],
                [
                    Entity(start=19, end=23, text="2022", type="date", score=0.38),
                    Entity(start=41, end=55, text="Windsor family", type="organization", score=0.90),
                    Entity(start=57, end=72, text="Queen Elizabeth", type="person", score=0.99),
                    Entity(start=85, end=91, text="London", type="location", score=0.99),
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
        examples=["knowledgator/gliner-x-base"],
    )
    default_entities: list[str] = Field(
        default=config.default_entities,
        description="The default entities to be detected, used if request includes no specific entities.",
        examples=[["person", "organization", "location", "date"]],
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
