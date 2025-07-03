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
) -> tuple[dict[str, str | list[dict[str, Any]]], str, list[dict[str, Any]]]:
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
        response_body: dict[str, Any] = response.json()
        inference_time: float = float(response.headers.get("X-Inference-Time", "0.0"))

    except Exception as e:
        raise gr.Error(message=f"Failed to parse response JSON: {e}")

    entities: list[dict[str, Any]] | None = response_body.get("entities")

    if entities is None:
        raise gr.Error(message="Corrupted response: 'entities' field is missing.")

    gradio_entities: list[dict[str, Any]] = deepcopy(entities)

    # Gradio needs 'entity' key instead of 'type'
    for entity in gradio_entities:
        if "type" in entity:
            entity["entity"] = entity.pop("type")

    return {"entities": gradio_entities, "text": text}, f"{inference_time:.2f} seconds", entities


description: str = f"""
<div style='text-align: center;'>
    <img src='/static/logo_border.png' alt='GLiNER Logo' style='height: auto; width: 100px; display: block; margin: auto;'>
    <div>
        A simple frontend for the GLiNER entity detection API.<br>
        This interface allows you to detect named entities in text using GLiNER's powerful models.<br>
        Currently loaded model: <strong><a href='https://huggingface.co/{config.model_id}'>{config.model_id}</a></strong><br>
    </div>
</div>
"""

article: str = """
<div style='text-align: center;'>
    See the <a href='/docs'>API documentation</a> for more details on how to use the GLiNER API from your programs or scripts.<br>
    <b>This project is licensed under MIT-License and can be found on <a href='https://github.com/freinold/GLiNER-API'>GitHub</a>.</b>
</div>
"""

interface = gr.Interface(
    fn=call_invoke,
    inputs=[
        gr.Textbox(
            label="Input Text",
            placeholder="Enter text...\nYou can also paste longer texts here.",
            lines=3,
            max_lines=15,
            value="Steve Jobs founded Apple Inc. in Cupertino, CA on April 1, 1976.",
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
        gr.HighlightedText(
            label="Detected Entities",
        ),
        gr.Label(label="Inference Time"),
        gr.JSON(label="Raw Response Body"),
    ],
    title="GLiNER API - Frontend",
    description=description,
    article=article,
    examples=[
        ["Steve Jobs founded Apple Inc. in Cupertino, CA on April 1, 1976."],
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
