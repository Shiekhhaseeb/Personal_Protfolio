from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "info") -> None:
    """Configure structured terminal logging for the app."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(log_level)
    root.addHandler(handler)

    # Keep third-party noise down; app.* logs stay at the configured level.
    for noisy_logger in ("httpx", "httpcore", "urllib3", "faiss"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
