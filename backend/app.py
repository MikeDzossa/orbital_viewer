"""Global imports"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Tuple, Literal, Any, Dict
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
from .core import impactGenerator  # import module to access generate_impact_scenario


class ImpactRequest(BaseModel):
    asteroid_id: str = Field("USER-IMPACTOR-001", description="Identifier for metadata")
    diameter_km: float = Field(..., gt=0, description="Asteroid diameter (km)")
    impact_time_iso: str = Field(..., description="Target impact time ISO UTC (e.g. 2027-01-04T00:00:00Z)")
    asteroid_r0_au: Tuple[float, float, float] = Field(..., description="Initial asteroid heliocentric position (AU)")


class ImpactResponse(BaseModel):
    metadata: Dict[str, Any]
    timeline: list

logger = get_logger(__name__)

app = FastAPI()
logger.info("Backend starting (debug=%s)", ENABLE_DEBUG_LOGS)


@app.post("/api/orbit")
def get_orbit(elem: OrbitalElements, steps: int = 1000):
    trajectory = compute_orbit(elem, steps)
    return {"trajectory": trajectory}


@app.get("/api/planets")
def get_all_planets(epoch: str = "2025-10-01"):
    """
    Return orbital elements for all major planets at a given epoch.
    """
    results = fetch_planets_elements(epoch)
    return results


@app.post("/api/impact", response_model=ImpactResponse)
def create_impact_scenario(req: ImpactRequest):
    try:
        meta, timeline = impactGenerator.generate_impact_scenario(
            asteroid_id=req.asteroid_id,
            diameter_km=req.diameter_km,
            impact_time_iso=req.impact_time_iso,
            asteroid_r0_au=req.asteroid_r0_au,
        )
    except Exception as e:
        logger.exception("Impact scenario generation failed")
        raise HTTPException(status_code=400, detail=str(e))
    return ImpactResponse(metadata=meta, timeline=timeline)


# === Serve Vite React frontend build ===
frontend_dir = os.path.join(os.path.dirname(__file__), "../frontend/dist")
print(f"Frontend directory: {frontend_dir}")

if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        """Serve index.html for any route (React Router support)"""
        return FileResponse(os.path.join(frontend_dir, "index.html"))
