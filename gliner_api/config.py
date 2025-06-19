from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, YamlConfigSettingsSource


class GlinerModelConfig(BaseModel):
    model_id: str = Field(
        default="knowledgator/gliner-x-base-v0.5",
        description="The Huggingface model ID for a GLiNER model.",
    )
    default_entities: list[str] = Field(
        default=["person", "organization", "location"],
        description="The default entities to be detected, used if request includes no specific entities.",
    )
    default_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="The default threshold for entity detection, used if request includes no specific threshold.",
    )


class Config(BaseSettings):
    use_case: str = Field(
        default="default",
        description="The use case for the GLiNER model, used to load specific configurations.",
    )
    gliner_config: GlinerModelConfig = Field(
        default_factory=GlinerModelConfig,
        description="Configuration for the GLiNER model, including model ID, default entities and default threshold.",
    )
    api_key: str | None = Field(
        default=None,
        description="API key for authentication; if provided, each request needs to include it.",
    )

    # pydantic_settings configuration starts here
    model_config = SettingsConfigDict(
        env_prefix="GLINER_API_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        yaml_file="config.yaml",
        yaml_file_encoding="utf-8",
    )

    # Reorder settings sources to prioritize YAML config
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls),
            dotenv_settings,
        )


@lru_cache
def get_config() -> Config:
    """Get the GLiNER API configuration."""
    return Config()
