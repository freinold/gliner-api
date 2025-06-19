from pydantic import BaseModel, Field

from gliner_api.config import GlinerModelConfig


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
        validation_alias="label",
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
    threshold: float | None = Field(
        default=None,
        description="Threshold for entity detection; if not set, uses default threshold (see gliner config from /api/info endpoint)",
        examples=[0.5],
    )
    entity_types: list[str] | None = Field(
        default=None,
        description="List of entity types to detect; if not set, uses default entities (see gliner config from /api/info endpoint)",
        examples=[["person", "organization", "location"]],
    )


class DetectionResponse(BaseModel):
    entities: list[Entity] = Field(
        description="List of detected entities in the input text",
        examples=[
            [
                Entity(start=0, end=11, text="Sam Altman", type="person", score=0.95),
                Entity(start=22, end=27, text="OpenAI", type="organization", score=0.98),
                Entity(start=31, end=44, text="San Francisco", type="location", score=0.92),
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
    threshold: float | None = Field(
        default=None,
        description="Threshold for entity detection; if not set, uses default threshold (see gliner config from /api/info endpoint)",
    )
    entity_types: list[str] | None = Field(
        default=None,
        description="List of entity types to detect; if not set, uses default entities (see gliner config from /api/info endpoint)",
        examples=[["person", "organization", "location"]],
    )


class BatchDetectionResponse(BaseModel):
    results: list[list[Entity]] = Field(
        description="List of lists of detected entities for each input text",
        examples=[
            [
                [
                    Entity(start=0, end=11, text="Sam Altman", type="person", score=0.95),
                    Entity(start=22, end=27, text="OpenAI", type="organization", score=0.98),
                    Entity(start=31, end=44, text="San Francisco", type="location", score=0.92),
                ],
                [
                    Entity(start=0, end=13, text="Queen Elizabeth", type="person", score=0.97),
                    Entity(start=30, end=47, text="Windsor family", type="organization", score=0.62),
                    Entity(start=41, end=47, text="London", type="location", score=0.93),
                ],
            ]
        ],
    )


class InfoResponse(BaseModel):
    gliner_config: GlinerModelConfig = Field(
        default_factory=GlinerModelConfig,
        description="Configuration for the GLiNER model",
    )
    api_key_required: bool = Field(
        default=False,
        description="Whether an API key is required for requests",
    )
    configured_use_case: str = Field(
        default="default",
        description="The configured use case for this deployment",
    )
