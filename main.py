from logging import Logger

import uvicorn
from prometheus_client import start_http_server

from gliner_api.backend import app
from gliner_api.config import Config, get_config
from gliner_api.logging import getLogger

config: Config = get_config()
logger: Logger = getLogger("gliner-api")


def main() -> None:
    """Run the GLiNER API server."""
    if config.metrics_enabled:
        if config.metrics_port == config.port:
            raise ValueError("Metrics port cannot be the same as API port. Please set a different port for metrics.")
        metrics_server, metrics_thread = start_http_server(addr=config.host, port=config.metrics_port)
        logger.info(f"Prometheus metrics server started at http://{config.host}:{config.metrics_port}")

        @app.on_event("shutdown")
        async def close_metrics_server():
            metrics_server.shutdown()
            metrics_thread.join()
            logger.info("Prometheus metrics server shutdown complete.")

    if config.frontend_enabled:
        from fastapi.staticfiles import StaticFiles
        from gradio import mount_gradio_app

        from gliner_api.frontend import client, interface

        app.mount("/static", StaticFiles(directory="static"), name="static")
        mount_gradio_app(
            app,
            interface,
            path="",
            show_api=False,
        )

        @app.on_event("shutdown")
        async def close_httpx_client():
            await client.aclose()

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_config="logconf.yaml",
    )


if __name__ == "__main__":
    main()
