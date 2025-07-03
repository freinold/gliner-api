from copy import deepcopy
from typing import Any

import gradio as gr
import gradio.themes as gr_themes
from httpx import AsyncClient, HTTPError, Response
from stamina import retry_context

from gliner_api.config import Config, get_config

config: Config = get_config()
client: AsyncClient = AsyncClient(
    base_url=f"http://{config.host}:{config.port}",
    headers={"Authorization": f"Bearer {config.api_key}"} if config.api_key is not None else None,
)


async def call_invoke(
    text: str,
    threshold: float,
    entity_types: list[str],
    additional_options: list[str],
) -> tuple[dict[str, str | list[dict[str, Any]]], list[dict[str, Any]]]:
    """Call the /api/invoke endpoint with the provided text."""
    flat_ner: bool = "deep_ner" not in additional_options
    multi_label: bool = "multi_label" in additional_options
    response: Response | None = None
    try:
        async for attempt in retry_context(on=HTTPError, attempts=3):
            with attempt:
                response = await client.post(
                    url="/api/invoke",
                    json={
                        "text": text,
                        "threshold": threshold,
                        "entity_types": entity_types,
                        "flat_ner": flat_ner,
                        "multi_label": multi_label,
                    },
                )
                response.raise_for_status()

    except HTTPError as e:
        raise gr.Error(message=f"HTTP error occurred: {e}")

    except Exception as e:
        raise gr.Error(message=f"An unexpected error occurred: {e}")

    try:
        if response is None:
            raise gr.Error(message="No response received from the server.")
        response_data: dict[str, Any] = response.json()
    except Exception as e:
        raise gr.Error(message=f"Failed to parse response JSON: {e}")

    entities: list[dict[str, Any]] | None = response_data.get("entities")

    if entities is None:
        raise gr.Error(message="Corrupted response: 'entities' field is missing.")

    gradio_entities: list[dict[str, Any]] = deepcopy(entities)

    # Gradio needs 'entity' key instead of 'type'
    for entity in gradio_entities:
        if "type" in entity:
            entity["entity"] = entity.pop("type")

    return {"entities": gradio_entities, "text": text}, entities


description: str = """
<div style='text-align: center;'>
    <img src='/static/logo.png' alt='GLiNER Logo' style='height: 50px; width: auto; margin-bottom: 10px; display: block; margin-left: auto; margin-right: auto;'>
    <div>
        A simple frontend for the GLiNER entity detection API.
    </div>
</div>
"""

article: str = """
<div style='text-align: center;'>
    See the <a href='/docs'>API documentation</a> for more details on how to use the GLiNER API from your programs or scripts.
</div>
"""

interface = gr.Interface(
    fn=call_invoke,
    inputs=[
        gr.Textbox(
            label="Input Text",
            placeholder="Enter text...",
            lines=5,
            max_lines=15,
            info="Text to analyze for named entities.",
        ),
        gr.Slider(
            label="Threshold",
            minimum=0.0,
            maximum=1.0,
            step=0.05,
            value=config.default_threshold,
            info="Minimum confidence score for entities to be included in the response.",
        ),
        gr.Dropdown(
            label="Entity Types",
            choices=config.default_entities,
            multiselect=True,
            value=config.default_entities,
            allow_custom_value=True,
            info="Select entity types to detect. Add custom entity types as needed.",
        ),
        gr.CheckboxGroup(
            label="Additional Options (Advanced)",
            choices=[
                ("Enable deep NER mode", "deep_ner"),
                ("Enable multi-label classification", "multi_label"),
            ],
            value=[],
            info="Deep NER: hierarchical entity detection for nested entities. Multi-label: entities can belong to multiple types.",
        ),
    ],
    outputs=[
        gr.HighlightedText(label="Detected Entities"),
        gr.JSON(label="Raw Response Payload"),
    ],
    title="GLiNER API - Frontend",
    description=description,
    article=article,
    examples=[
        ["Steve Jobs founded Apple in Cupertino, California on April 1, 1976."],
        ["Until her death in 2022, the head of the Windsor family, Queen Elizabeth, resided in London."],
        ["The Eiffel Tower was completed in 1889 and is located in Paris, France."],
        ["Barack Obama served as the 44th President of the United States from 2009 to 2017."],
        ["The Great Wall of China was built over several dynasties, starting in the 7th century BC."],
        ["Albert Einstein developed the theory of relativity, which revolutionized modern physics."],
    ],
    api_name=False,
    flagging_mode="never",
    theme=gr_themes.Base(primary_hue="teal"),
    submit_btn="Detect Entities",
)
