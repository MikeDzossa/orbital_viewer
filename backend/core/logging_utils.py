"""Logging utilities respecting the master debug toggle.

Use get_logger(name) instead of logging.getLogger directly so that we
can automatically apply the debug level based on config.ENABLE_DEBUG_LOGS.
"""

from __future__ import annotations
import logging
from .config import ENABLE_DEBUG_LOGS

_BASE_CONFIGURED = False


def _configure_root():
    global _BASE_CONFIGURED
    if _BASE_CONFIGURED:
        return
    level = logging.DEBUG if ENABLE_DEBUG_LOGS else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    if not ENABLE_DEBUG_LOGS:
        # Reduce noise from external libraries when not debugging
        for noisy in ["urllib3", "requests"]:
            logging.getLogger(noisy).setLevel(logging.WARNING)
    _BASE_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    _configure_root()
    logger = logging.getLogger(name)
    # Ensure per-logger level honors global toggle
    logger.setLevel(logging.DEBUG if ENABLE_DEBUG_LOGS else logging.INFO)
    return logger
