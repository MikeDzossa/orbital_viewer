"""Backend package initializer.

Exposes the FastAPI `app` and selected core utilities so external code can:

    from backend import app, OrbitalElements

Avoids needing deep import paths like `backend.core.models`.
"""

from .app import app  # noqa: F401

# Re-export selected frequently used core symbols for convenience
try:  # pragma: no cover
    from .core import (  # type: ignore
        OrbitalElements,
        compute_orbit,
        fetch_planets_elements,
        get_logger,
        ENABLE_DEBUG_LOGS,
    )

    __all__ = [
        "app",
        "OrbitalElements",
        "compute_orbit",
        "fetch_planets_elements",
        "get_logger",
        "ENABLE_DEBUG_LOGS",
    ]
except Exception:  # If core changes or partial imports fail
    __all__ = ["app"]
