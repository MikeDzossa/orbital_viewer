"""Central configuration for backend.

ENABLE_DEBUG_LOGS: master boolean to turn verbose debug logging on/off.
Can be overridden via environment variable ORBITAL_DEBUG=1/0.
"""

from __future__ import annotations
import os

# Master toggle (default False for production safety)
ENABLE_DEBUG_LOGS: bool = os.getenv("ORBITAL_DEBUG", "0") in {
    "1",
    "true",
    "True",
    "YES",
    "yes",
}
