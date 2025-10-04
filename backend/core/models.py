from pydantic import BaseModel


class OrbitalElements(BaseModel):
    a: float  # semi-major axis (AU)
    e: float  # eccentricity
    i: float  # inclination (deg)
    raan: float  # longitude of ascending node (deg)
    argp: float  # argument of periapsis (deg)
    M0: float  # mean anomaly at epoch (deg)
    epoch: str  # ISO date
