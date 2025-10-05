import numpy as np
from astropy import units as u
from astropy.time import Time
from poliastro.bodies import Sun
from poliastro.twobody import Orbit
from poliastro.twobody.angles import M_to_E, E_to_nu
from .models import OrbitalElements
import logging


def mean_to_true_anomaly(M0_deg, e):
    """
    Convert mean anomaly (degrees) to true anomaly (degrees or radians).
    Handles elliptical (0 <= e < 1), parabolic (e == 1), and hyperbolic (e > 1) orbits.
    """
    if e < 0:
        raise ValueError(f"Negative eccentricity is not physical: e={e}")

    if np.isclose(e, 1.0):
        # Parabolic case: use Barker's equation
        # M0_deg is assumed to be mean anomaly in degrees, convert to radians
        M0_rad = np.deg2rad(M0_deg)
        # Barker's equation: M = D + (1/3)D^3, solve for D (parabolic anomaly)
        # For small M, D ≈ M
        # For more accuracy, use Newton-Raphson
        D = M0_rad  # initial guess
        for _ in range(10):
            f = D + (1 / 3) * D**3 - M0_rad
            df = 1 + D**2
            D -= f / df
        # True anomaly: tan(nu/2) = D
        nu = 2 * np.arctan(D)
        return np.rad2deg(nu).value  # degrees
    elif e < 1:
        # Elliptic case
        if e < 1e-10:
            # Near-circular: mean ≈ true anomaly
            return M0_deg
        else:
            M0_rad = np.deg2rad(M0_deg) * u.rad
            E = M_to_E(M0_rad, e * u.one) * u.rad
            nu = E_to_nu(E, e * u.one)
            return np.rad2deg(nu).value  # degrees
    else:
        # Hyperbolic case (e > 1)
        # M0_deg is assumed to be mean anomaly in degrees, convert to radians
        M0_rad = np.deg2rad(M0_deg)
        # Solve Kepler's equation for hyperbolic orbits: M = e*sinhH - H
        # Use Newton-Raphson to solve for H (hyperbolic anomaly)
        H = np.arcsinh(M0_rad / e)  # initial guess
        for _ in range(10):
            f = e * np.sinh(H) - H - M0_rad
            df = e * np.cosh(H) - 1
            H -= f / df
        # True anomaly: tanh(nu/2) = sqrt((e+1)/(e-1)) * tanh(H/2)
        sqrt_arg = np.sqrt((e + 1) / (e - 1))
        tanh_half_H = np.tanh(H / 2)
        tan_half_nu = sqrt_arg * tanh_half_H
        nu = 2 * np.arctan(tan_half_nu)
        return np.rad2deg(nu).value  # degrees


def compute_orbit(elem: OrbitalElements, steps=1000):
    epoch = Time(elem.epoch)
    nu = mean_to_true_anomaly(elem.M0, elem.e)
    # Orbit poliastro
    orb = Orbit.from_classical(
        Sun,
        elem.a * u.km,
        elem.e * u.one,
        elem.i * u.deg,
        elem.raan * u.deg,
        elem.argp * u.deg,
        nu * u.deg,
        epoch,
    )

    days = orb.period.to(u.day).value
    times = epoch + np.linspace(0, days, steps) * u.day
    points = []
    for t in times:
        r = orb.propagate(t - epoch).r.to(u.AU).value
        points.append(
            {"t": t.iso, "x": float(r[0]), "y": float(r[1]), "z": float(r[2])}
        )
    return points
