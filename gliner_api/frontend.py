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


async def call_invoke(text: str) -> tuple[dict[str, str | list[dict[str, Any]]], list[dict[str, Any]]]:
    """Call the /api/invoke endpoint with the provided text."""
    response: Response | None = None
    try:
        async for attempt in retry_context(on=HTTPError):
            with attempt:
                response = await client.post("/api/invoke", json={"text": text})
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
    <img src='/static/logo.png' alt='GLiNER Logo' style='width: 200px; height: auto; margin-bottom: 20px; display: block; margin-left: auto; margin-right: auto;'>
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
    inputs=gr.Textbox(label="Input Text", placeholder="Enter text to analyze...", lines=5, max_lines=15),
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
