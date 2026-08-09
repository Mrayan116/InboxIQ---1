"""
Structured logging setup.

Why: print() statements don't scale past a hobby project. We want log level
control per environment, consistent formatting, and (in prod) JSON output
so logs are machine-parseable by whatever aggregator you point at this later
(CloudWatch, Datadog, etc.) without touching this file again.
"""

import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        if settings.environment == "development"
        else '{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
    )

    logging.basicConfig(
        level=settings.log_level,
        format=log_format,
        stream=sys.stdout,
    )

    # Quiet down noisy third-party loggers unless we're debugging them specifically.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
