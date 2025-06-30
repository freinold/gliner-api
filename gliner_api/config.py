from functools import lru_cache

from huggingface_hub import HfApi, ModelInfo
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, CliSettingsSource, PydanticBaseSettingsSource, SettingsConfigDict, YamlConfigSettingsSource


class Config(BaseSettings):
    use_case: str = Field(
        default="general",
        description="The use case for the GLiNER model, useful for describing the intended application or domain.",
        validation_alias=AliasChoices("use_case", "name"),
    )
    model_id: str = Field(
        default="knowledgator/gliner-x-base",
        description="The Huggingface model ID for a GLiNER model. Browse available models at https://huggingface.co/models?library=gliner&sort=trending",
    )
    onnx_enabled: bool = Field(
        default=False,
        description="Whether to use ONNX for inference. If enabled, the model will be loaded in ONNX format for potentially faster inference.",
    )
    onnx_model_path: str = Field(
        default="model.onnx",
        description="The file path for the ONNX model. This is used if onnx_enabled is set to True. Some models are also provided in quantized ONNX format, e.g. `model_quantized.onnx`.",
    )
    default_entities: list[str] = Field(
        default=["person", "organization", "location", "date"],
        description="The default entities to be detected, used if request includes no specific entities.",
    )
    default_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="The default threshold for entity detection, used if request includes no specific threshold.",
    )
    api_key: str | None = Field(
        default=None,
        description="API key for authentication; if provided, each request needs to include it.",
    )
    host: str = Field(
        default="0.0.0.0",
        description="The host address for serving the API.",
    )
    port: int = Field(
        default=8080,
        ge=1,
        le=65535,
        description="The port number for serving the API.",
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
        cli_parse_args=True,
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
            CliSettingsSource(settings_cls),
            env_settings,
            YamlConfigSettingsSource(settings_cls),
            dotenv_settings,
        )

    @field_validator("model_id")
    @classmethod
    def validate_model_id(cls, v: str) -> str:
        try:
            hf_api: HfApi = HfApi()
            info: ModelInfo = hf_api.model_info(v)
            if info.library_name is None or info.library_name.lower() != "gliner":
                raise ValueError(
                    f"Model {v} is not a GLiNER model. Check for compatible models at https://huggingface.co/models?library=gliner&sort=trending"
                )
        except Exception as e:
            raise ValueError(f"Failed to validate model ID {v}: {e}")
        return v


@lru_cache
def get_config() -> Config:
    """Get the GLiNER API configuration."""
    return Config()
