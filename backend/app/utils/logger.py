"""
Structured logging setup.

Logs important lifecycle events (user registered, document uploaded,
embedding completed, query received, etc.) as requested by the spec.
NEVER log passwords, JWT secrets, API keys, or raw sensitive user data.
"""
import logging
import sys


def setup_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        # Avoid duplicate handlers on reload
        return

    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Quiet down noisy third-party loggers a little
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
