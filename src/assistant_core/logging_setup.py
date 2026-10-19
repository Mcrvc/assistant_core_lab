"""Structured JSON logging configuration."""

import json
import logging
import sys


class JsonFormatter(logging.Formatter):
    """Format log records as structured JSON omitting sensitive inputs."""

    def format(self, record: logging.LogRecord) -> str:
        data = {
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key in ("intent", "latency_ms", "session", "degraded"):
            if hasattr(record, key):
                data[key] = getattr(record, key)
        return json.dumps(data, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    """Configure the root or package logger to output JSON to stderr."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    pkg_logger = logging.getLogger("assistant_core")
    pkg_logger.handlers.clear()
    pkg_logger.addHandler(handler)
    pkg_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    pkg_logger.propagate = False
