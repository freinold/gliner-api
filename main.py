from logging import Logger

import uvicorn

from gliner_api.backend import app
from gliner_api.config import Config, get_config
from gliner_api.logging import getLogger

config: Config = get_config()
logger: Logger = getLogger("gliner-api")


def main() -> None:
    """Run the GLiNER API server."""
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_config="logconf.yaml",
    )


if __name__ == "__main__":
    main()
