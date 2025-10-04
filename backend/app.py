"""Global imports"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

""" core imports """
from .core import (
    ENABLE_DEBUG_LOGS,
    get_logger,
    fetch_planets_elements,
    OrbitalElements,
    compute_orbit,
)

logger = get_logger(__name__)

app = FastAPI()
logger.info("Backend starting (debug=%s)", ENABLE_DEBUG_LOGS)


@app.post("/api/orbit")
def get_orbit(elem: OrbitalElements, steps: int = 200):
    trajectory = compute_orbit(elem, steps)
    return {"trajectory": trajectory}


@app.get("/api/planets")
def get_all_planets(epoch: str = "2025-10-01"):
    """
    Return orbital elements for all major planets at a given epoch.
    """
    results = fetch_planets_elements(epoch)
    return results


# === Serve Vite React frontend build ===
frontend_dir = os.path.join(os.path.dirname(__file__), "../frontend/dist")
print(f"Frontend directory: {frontend_dir}")

if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        """Serve index.html for any route (React Router support)"""
        return FileResponse(os.path.join(frontend_dir, "index.html"))
