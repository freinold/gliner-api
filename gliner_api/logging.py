import json
import logging
import logging.config
from datetime import datetime

from yaml import safe_load


def getLogger(name: str = "gliner-api") -> logging.Logger:
    """Configures logging and returns a logger with the specified name.

    Parameters:
    name (str): The name of the logger.

    Returns:
    logging.Logger: The logger with the specified name.
    """
    with open("logconf.yaml", "r", encoding="utf-8") as file:
        log_config = safe_load(file)

    logging.config.dictConfig(log_config)
    return logging.getLogger(name)


class JsonFormatter(logging.Formatter):
    """A custom JSON formatter for logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Formats the log record as a JSON string.

        Parameters:
        record (logging.LogRecord): The log record to format.

        Returns:
        str: The log record as a JSON string.
        """
        #
        log_data = {
            "time": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
        }

        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = str(record.exc_info)

        # Add extra fields if present (non-standard LogRecord attributes)
        standard_attrs = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
        }
        # Exclude 'color_message' from extra fields
        extra = {k: v for k, v in record.__dict__.items() if k not in standard_attrs and k != "color_message"}
        if extra:
            log_data.update(extra)

        return json.dumps(log_data)
