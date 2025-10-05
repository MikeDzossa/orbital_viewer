#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Impactor builder + impact effects (T0 = TODAY, daily step)

Fonctions principales :
- Construit une trajectoire impact (modèle linéaire) & timeline quotidienne
- Calcule le point d'impact (lat, lon) et la vitesse d'impact relative au sol
- Estime :
  * énergie d'impact (J, kt TNT, "Hiroshima")
  * rayons d'onde de choc (1/3/5/10 psi) via scaling W^(1/3)
  * victimes (par anneaux de surpression) selon densité fournie
  * diamètre du cratère (heuristique simple, ajustable)

Sortie :
- <asteroid_id>.json avec timeline + surface_impact + impact_effects
- Impression console des valeurs clés demandées
"""

from __future__ import annotations
import json
from typing import Tuple, Optional, Literal, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from math import sqrt, pi, sin, cos, atan2, asin

# =========================
# Paramètres & constantes
# =========================
# Timezone locale pour T0 "aujourd'hui"
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    ZoneInfo = None

# Astropy (pour Horizons & temps sidéral)
from astropy.time import Time
try:
    from astroquery.jplhorizons import Horizons
    HAS_HORIZONS = True
except Exception:
    HAS_HORIZONS = False

# Gravitation en unités AU/day
K_GAUSS = 0.01720209895            # AU^(3/2)/day
MU_SUN = K_GAUSS**2                # AU^3/day^2
AU_KM = 149_597_870.7
DAY_S = 86400.0
MU_EARTH_KM = 398600.435436        # km^3/s^2
MU_EARTH = MU_EARTH_KM * (DAY_S**2) / (AU_KM**3)  # AU^3/day^2
EPS_PARAB = 1e-12

# Terre
OMEGA_EARTH = 7.2921159e-5         # rad/s (rotation)
RE_KM = 6378.137
RE_AU = RE_KM / AU_KM
AUperDAY_to_KMperS = AU_KM / DAY_S

# Densités
DENSITY_METEORITE_KG_M3_DEFAULT = 3500.0  # ~3.5 g/cm^3 (stony avg)
DENSITY_TARGET_KG_M3_DEFAULT = 2500.0     # sol rocheux moyen (pour cratère)

# Obliquité (J2000)
EPS_OBL_DEG = 23.439291111
EPS_OBL = EPS_OBL_DEG * pi/180.0

# Conversion énergie
KT_J = 4.184e12         # 1 kilotonne TNT
E_HIROSHIMA_J = 15.0 * KT_J  # ~15 kt

# Ondes de choc (distance réduite Z en km/kt^(1/3)) — ajustables
Z_DEFAULT = {
    "10psi": 0.40,
    "5psi":  0.60,
    "3psi":  0.90,
    "1psi":  1.70,
}
# Taux de létalité par anneau — ajustables
LETHALITY_DEFAULT = {"10psi":0.9, "5psi":0.5, "3psi":0.2, "1psi":0.05}

# Heuristique cratère (diamètre final ~ K * d_proj, K dépend un peu de v)
# Ici : K = K0 + K_v * v(km/s) ; par défaut ~20x le projectile à 20 km/s
CRATER_K0 = 10.0
CRATER_KV = 0.5   # => K ≈ 10 + 0.5*v ; à 20 km/s → K ≈ 20

# =========================
# Helpers I/O
# =========================
def prompt_str(msg: str, default: Optional[str]=None) -> str:
    s = input(f"{msg}" + (f" [{default}]" if default is not None else "") + ": ").strip()
    return s if s else (default if default is not None else "")

def prompt_float(msg: str, default: Optional[float]=None) -> float:
    while True:
        s = input(f"{msg}" + (f" [{default}]" if default is not None else "") + ": ").strip()
        if not s and default is not None:
            return float(default)
        try:
            return float(s)
        except ValueError:
            print("Veuillez entrer un nombre valide.")

def prompt_vec3(msg: str, default: Optional[Tuple[float,float,float]]=None) -> Tuple[float,float,float]:
    hint = f"{default}" if default is not None else "ex: 1.0, -0.5, 0.0"
    while True:
        s = input(f"{msg} [{hint}]: ").strip()
        if not s and default is not None:
            return tuple(map(float, default))  # type: ignore
        try:
            parts = [p.strip() for p in s.split(",")]
            if len(parts) != 3: raise ValueError
            return (float(parts[0]), float(parts[1]), float(parts[2]))
        except Exception:
            print("Format attendu: trois nombres séparés par des virgules (x,y,z).")

def prompt_choice(msg: str, choices: list[str], default: Optional[str]=None) -> str:
    ch = "/".join(choices)
    while True:
        s = input(f"{msg} ({ch})" + (f" [{default}]" if default else "") + ": ").strip().lower()
        if not s and default:
            return default
        if s in choices:
            return s
        print(f"Choix invalide. Options: {choices}")

# =========================
# Temps
# =========================
def now_T0_iso_utc() -> tuple[str, str]:
    if ZoneInfo is not None:
        local_tz = ZoneInfo("Europe/Paris")
        now_local = datetime.now(local_tz)
        now_utc = now_local.astimezone(timezone.utc)
    else:
        now_utc = datetime.now(timezone.utc)
        now_local = now_utc
    T0_iso_utc = now_utc.isoformat().replace("+00:00", "Z")
    T0_iso_local = now_local.isoformat()
    return T0_iso_utc, T0_iso_local

def parse_iso_utc(iso: str) -> datetime:
    s = iso.strip()
    if s.endswith("Z"):
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    else:
        dt = datetime.fromisoformat(s if "+" in s else s + "+00:00")
    return dt.astimezone(timezone.utc)

def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00","Z")

# GMST
def gmst_radians(dt_utc: datetime) -> float:
    t = Time(dt_utc)
    jd = t.jd
    T = (jd - 2451545.0)/36525.0
    gmst_deg = (280.46061837
                + 360.98564736629*(jd - 2451545.0)
                + 0.000387933*T*T
                - (T**3)/38710000.0)
    return (gmst_deg % 360.0) * pi/180.0

# =========================
# Vecteurs & rotations
# =========================
def vadd(a,b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def vsub(a,b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def vscale(a,s): return (a[0]*s, a[1]*s, a[2]*s)
def vdot(a,b): return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
def vcross(a,b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def vnorm(a): return sqrt(vdot(a,a))

def rot_x(v, ang):
    c, s = cos(ang), sin(ang)
    x, y, z = v
    return (x, c*y - s*z, s*y + c*z)

def rot_z(v, ang):
    c, s = cos(ang), sin(ang)
    x, y, z = v
    return (c*x - s*y, s*x + c*y, z)

def ecl_to_eq(v):    # Ecliptic → Equatorial (J2000)
    return rot_x(v, +EPS_OBL)

def eci_to_ecef(v, gmst_rad):  # ECI → ECEF
    return rot_z(v, +gmst_rad)

# =========================
# Éphémérides / États
# =========================
@dataclass
class BodyState:
    r_au: Tuple[float,float,float]
    v_au_per_day: Tuple[float,float,float]

class EphemerisProvider:
    def __init__(self):
        self.has_h = HAS_HORIZONS

    def fetch_horizons(self, target: str, epoch_iso: str) -> BodyState:
        if not self.has_h:
            raise RuntimeError("astroquery/jplhorizons non disponible.")
        t = Time(parse_iso_utc(epoch_iso))
        obj = Horizons(id=target, location="500@0", epochs=t.jd, id_type="smallbody")
        vec = obj.vectors(refplane='ecliptic')
        r = (float(vec['x'][0]), float(vec['y'][0]), float(vec['z'][0]))
        v = (float(vec['vx'][0]), float(vec['vy'][0]), float(vec['vz'][0]))
        return BodyState(r, v)

    def earth_state(self, epoch_iso: str, mode: str,
                    r0: Optional[Tuple[float,float,float]]=None,
                    v0: Optional[Tuple[float,float,float]]=None) -> BodyState:
        if mode == "manual":
            if r0 is None or v0 is None:
                raise ValueError("Terre 'manual' requiert r0 & v0.")
            return BodyState(r0, v0)
        return self.fetch_horizons("399", epoch_iso)

    def asteroid_state(self, epoch_iso: str, mode: str,
                       asteroid_id: Optional[str]=None,
                       r0: Optional[Tuple[float,float,float]]=None,
                       v0: Optional[Tuple[float,float,float]]=None) -> BodyState:
        if mode == "manual":
            if r0 is None:
                raise ValueError("Astéroïde 'manual' requiert r0.")
            return BodyState(r0, v0 or (0.0,0.0,0.0))
        if not asteroid_id:
            raise ValueError("fetch_by_id requiert un identifiant Horizons.")
        return self.fetch_horizons(asteroid_id, epoch_iso)

# =========================
# Construction de l'impact (linéaire)
# =========================
def solve_v0_for_impact(r_a0, T0_iso, Ti_iso, r_e0, v_e0):
    dt_days = max(1e-9, (parse_iso_utc(Ti_iso) - parse_iso_utc(T0_iso)).total_seconds()/86400.0)
    term = vscale(vsub(r_e0, r_a0), 1.0/dt_days)
    return vadd(v_e0, term)

def orbital_diagnostics(r, v, mu):
    rmag = vnorm(r); vmag = vnorm(v)
    eps = 0.5*vmag*vmag - mu/rmag
    h = vcross(r, v); hmag = vnorm(h)
    e2 = 1.0 + 2.0*eps*hmag*hmag/(mu*mu)
    e = sqrt(e2) if e2 > 0 else 0.0
    if abs(eps) <= EPS_PARAB:
        conic, a, P_days, P_years = "parabola", float("inf"), None, None
    elif eps < 0:
        conic = "ellipse"; a = -mu/(2.0*eps)
        from math import pi as mpi
        P_days = 2.0*mpi*sqrt(a*a*a/mu); P_years = P_days/365.25
    else:
        conic, a, P_days, P_years = "hyperbola", -mu/(2.0*eps), None, None
    return {"conic": conic, "semi_major_axis_au": a, "eccentricity": e,
            "period_days": P_days, "period_years": P_years}

def build_daily_timeline(T0_iso, Ti_iso, r_a0, v_a0, r_e0, v_e0):
    t0 = parse_iso_utc(T0_iso); ti = parse_iso_utc(Ti_iso)
    series = []
    ts = t0
    while ts <= ti:
        dt_days = (ts - t0).total_seconds() / 86400.0
        r_ast = vadd(r_a0, vscale(v_a0, dt_days)); v_ast = v_a0
        r_earth = vadd(r_e0, vscale(v_e0, dt_days)); v_earth = v_e0
        r_geo = vsub(r_ast, r_earth); v_geo = vsub(v_ast, v_earth)
        series.append({
            "iso": iso_z(ts),
            "heliocentric": {"r_au": {"x": r_ast[0], "y": r_ast[1], "z": r_ast[2]},
                             "v_au_per_day": {"x": v_ast[0], "y": v_ast[1], "z": v_ast[2]}},
            "geocentric":   {"r_au": {"x": r_geo[0], "y": r_geo[1], "z": r_geo[2]},
                             "v_au_per_day": {"x": v_geo[0], "y": v_geo[1], "z": v_geo[2]}}
        })
        ts = ts + timedelta(days=1)
    return series

def compute_surface_impact(Ti_iso, r_a0, v_a0, r_e0, v_e0):
    Ti = parse_iso_utc(Ti_iso)
    v_geo = vsub(v_a0, v_e0)  # AU/day
    v_geo_mag = max(1e-16, vnorm(v_geo))
    dt_surface_days = RE_AU / v_geo_mag
    Ts = Ti - timedelta(days=dt_surface_days)
    r_geo_Ts = vscale(v_geo, -dt_surface_days)  # AU
    rhat_ecl = vscale(r_geo_Ts, 1.0 / RE_AU)
    rhat_eq = ecl_to_eq(rhat_ecl)
    r_eq_au = vscale(rhat_eq, RE_AU)
    theta = gmst_radians(Ts)
    r_ecef_au = eci_to_ecef(r_eq_au, theta)
    x, y, z = r_ecef_au
    rmag = sqrt(x*x + y*y + z*z)
    lat = asin(z / rmag) * 180.0/pi
    lon = atan2(y, x) * 180.0/pi
    if lon > 180.0: lon -= 360.0
    if lon <= -180.0: lon += 360.0
    # vitesses
    v_geo_eq = ecl_to_eq(v_geo)  # AU/day
    v_ecef_au_per_day = eci_to_ecef(v_geo_eq, theta)
    v_inertial_km_s = tuple(c * AUperDAY_to_KMperS for c in v_ecef_au_per_day)
    v_inertial_speed_km_s = sqrt(sum(ci*ci for ci in v_inertial_km_s))
    r_ecef_km = tuple(c * AU_KM for c in r_ecef_au)
    omega = (0.0, 0.0, OMEGA_EARTH)
    wxr = (
        omega[1]*r_ecef_km[2] - omega[2]*r_ecef_km[1],
        omega[2]*r_ecef_km[0] - omega[0]*r_ecef_km[2],
        omega[0]*r_ecef_km[1] - omega[1]*r_ecef_km[0],
    )
    v_ground_km_s = (
        v_inertial_km_s[0] - wxr[0],
        v_inertial_km_s[1] - wxr[1],
        v_inertial_km_s[2] - wxr[2],
    )
    v_ground_speed_km_s = sqrt(sum(ci*ci for ci in v_ground_km_s))
    return {
        "impact_time_center_iso": Ti_iso,
        "impact_surface_time_iso": iso_z(Ts),
        "impact_point": {"latitude_deg": lat, "longitude_deg": lon},
        "velocity_at_impact": {
            "inertial_ecef_km_s": {"x": v_inertial_km_s[0], "y": v_inertial_km_s[1], "z": v_inertial_km_s[2]},
            "inertial_speed_km_s": v_inertial_speed_km_s,
            "ground_relative_km_s": {"x": v_ground_km_s[0], "y": v_ground_km_s[1], "z": v_ground_km_s[2]},
            "ground_relative_speed_km_s": v_ground_speed_km_s
        },
        "ecef_position_at_impact_au": {"x": r_ecef_au[0], "y": r_ecef_au[1], "z": r_ecef_au[2]}
    }

# =========================
# Effets d'impact
# =========================
def mass_from_diameter_m(d_m, rho_i=DENSITY_METEORITE_KG_M3_DEFAULT):
    r = 0.5 * d_m
    return rho_i * (4.0/3.0) * pi * (r**3)

def kinetic_energy_joules(mass_kg, v_km_s):
    v = v_km_s * 1000.0
    return 0.5 * mass_kg * v * v

def yield_kt(E_j): return E_j / KT_J
def hiroshima_equiv(E_j): return E_j / E_HIROSHIMA_J

def blast_radii_km_from_energy(E_j, z_table=Z_DEFAULT):
    W_kt = yield_kt(E_j)
    W13 = W_kt ** (1.0/3.0)
    return {k: z_table[k]*W13 for k in z_table}

def fatalities_from_rings(E_j, pop_density_per_km2,
                          lethality_map=LETHALITY_DEFAULT,
                          z_table=Z_DEFAULT):
    R = blast_radii_km_from_energy(E_j, z_table)
    order = ["10psi", "5psi", "3psi", "1psi"]
    rings = []
    total = 0.0
    r_in = 0.0
    for key in order:
        if key not in R: continue
        r_out = R[key]
        f = lethality_map.get(key, 0.0)
        area = pi * (r_out*r_out - r_in*r_in)
        victims = area * pop_density_per_km2 * f
        rings.append({"band": key, "r_in_km": r_in, "r_out_km": r_out,
                      "fatality_rate": f, "fatalities_est": victims})
        total += victims
        r_in = r_out
    return {"radii_km": {k: R[k] for k in order if k in R},
            "rings": rings, "fatalities_total_est": total}

def crater_diameter_km_heuristic(diameter_km, v_km_s,
                                 K0=CRATER_K0, Kv=CRATER_KV):
    """
    Heuristique simple : D_crater ≈ (K0 + Kv*v) * d_proj
    Par défaut : ≈ 20x le projectile à 20 km/s (ordre de grandeur).
    """
    K = K0 + Kv * v_km_s
    return K * diameter_km

# =========================
# JSON
# =========================
def save_json(asteroid_id: str, meta: dict, timeline: list) -> str:
    fname = f"{asteroid_id}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump({"metadata": meta, "timeline": timeline}, f, indent=2)
    return fname

# =========================
# MAIN
# =========================
def generate_impact_scenario(
        asteroid_id: str,
        diameter_km: float,
        impact_time_iso: str,
        asteroid_r0_au: Tuple[float, float, float],
) -> Tuple[Dict[str, Any], list]:
    """Simplified non-interactive impact scenario generator that auto-solves initial asteroid velocity.

    Velocity is chosen so that (under linear relative motion) the asteroid impacts Earth at impact_time_iso.
    JSON file saving is not performed here; caller can save if desired using save_json.
    Returns (metadata, timeline)
    """
    # Internal defaults
    meteorite_density_kg_m3 = DENSITY_METEORITE_KG_M3_DEFAULT
    pop_density_per_km2 = 3000.0

    # Epoch now (T0)
    T0_iso, T0_iso_local = now_T0_iso_utc()

    # Mass from diameter & default density
    mass_kg = mass_from_diameter_m(diameter_km * 1000.0, meteorite_density_kg_m3)

    # Fetch Earth state (always Horizons when available)
    eph = EphemerisProvider()
    earth_state = eph.earth_state(T0_iso, mode="fetch_by_id")

    # Solve asteroid initial velocity for desired impact time (linear model)
    ast_state = BodyState(asteroid_r0_au, (0.0, 0.0, 0.0))
    v_a0 = solve_v0_for_impact(asteroid_r0_au, T0_iso, impact_time_iso, earth_state.r_au, earth_state.v_au_per_day)
    ast_state = BodyState(asteroid_r0_au, v_a0)

    # Diagnostics
    diag_sun = orbital_diagnostics(ast_state.r_au, v_a0, MU_SUN)
    r_rel = vsub(ast_state.r_au, earth_state.r_au)
    v_rel = vsub(v_a0, earth_state.v_au_per_day)
    diag_earth = orbital_diagnostics(r_rel, v_rel, MU_EARTH)

    # Timeline
    timeline = build_daily_timeline(T0_iso, impact_time_iso, ast_state.r_au, v_a0, earth_state.r_au, earth_state.v_au_per_day)

    # Impact surface & velocity
    surface = compute_surface_impact(impact_time_iso, ast_state.r_au, v_a0, earth_state.r_au, earth_state.v_au_per_day)
    v_impact_km_s = surface["velocity_at_impact"]["ground_relative_speed_km_s"]

    # Effects
    E_j = kinetic_energy_joules(mass_kg, v_impact_km_s)
    W_kt = yield_kt(E_j)
    N_hiro = hiroshima_equiv(E_j)
    radii_km = blast_radii_km_from_energy(E_j)
    casualties = fatalities_from_rings(E_j, pop_density_per_km2)
    crater_D_km = crater_diameter_km_heuristic(diameter_km, v_impact_km_s)

    meta = {
        "frame": "heliocentrique écliptique J2000",
        "units": {"position": "AU", "velocity": "AU/day"},
        "earth_radius_km": RE_KM,
        "assumptions": {
            "meteorite_density_kg_m3": meteorite_density_kg_m3,
            "blast_Z_km_per_kt13": Z_DEFAULT,
            "lethality_by_ring": LETHALITY_DEFAULT,
            "crater_heuristic": {"K0": CRATER_K0, "Kv": CRATER_KV, "note": "D_crater ≈ (K0+Kv*v[km/s]) * d[km]"},
            "notes": "Ondes & cratère = ordres de grandeur; ajustez coefficients selon vos références."
        },
        "asteroid": {
            "id": asteroid_id,
            "diameter_km": diameter_km,
            "mass_kg": mass_kg
        },
        "initial_conditions": {
            "epoch_T0_local": T0_iso_local,
            "epoch_T0_utc_iso": T0_iso,
            "impact_center_time_iso": surface["impact_time_center_iso"],
            "impact_surface_time_iso": surface["impact_surface_time_iso"],
            "earth_T0": {
                "r_au": {"x": earth_state.r_au[0], "y": earth_state.r_au[1], "z": earth_state.r_au[2]},
                "v_au_per_day": {"x": earth_state.v_au_per_day[0], "y": earth_state.v_au_per_day[1], "z": earth_state.v_au_per_day[2]},
                "source": "fetch_by_id" if HAS_HORIZONS else "manual"
            },
            "asteroid_T0": {
                "r_au": {"x": ast_state.r_au[0], "y": ast_state.r_au[1], "z": ast_state.r_au[2]},
                "v_au_per_day": {"x": v_a0[0], "y": v_a0[1], "z": v_a0[2]},
                "source": "manual_solved_v0"
            }
        },
        "orbit_diagnostics": {
            "sun_centered": diag_sun,
            "earth_centered": diag_earth
        },
        "surface_impact": {**surface},
        "impact_effects": {
            "energy_joules": E_j,
            "yield_kilotons": W_kt,
            "hiroshima_equiv": N_hiro,
            "blast_radii_km": radii_km,
            "casualties": casualties,
            "crater_diameter_km_heuristic": crater_D_km
        },
        "propagation_model": "linéaire (r(t)=r0+v*t ; v constante)"
    }

    return meta, timeline

# def main():
#     """Interactive CLI preserved; delegates to generate_impact_scenario."""
#     print("\n=== Impactor + Effects (T0 = aujourd'hui, pas 1 jour) ===\n")
#     T0_iso, T0_iso_local = now_T0_iso_utc()
#     print(f"T0 (Europe/Paris) : {T0_iso_local}")
#     print(f"T0 (UTC Z)        : {T0_iso}")

#     asteroid_id = prompt_str("Identifiant de l'astéroïde (nom du fichier)", "USER-IMPACTOR-001")
#     diameter_km = prompt_float("Diamètre de l'astéroïde [km]", 5.0)
#     Ti_iso = prompt_str("Date d'impact souhaitée (ISO UTC)", "2027-01-04T00:00:00Z")
#     # Mandatory asteroid state (manual mode only now)
#     ast_r0 = prompt_vec3("Astéroïde r0 [AU] (x,y,z)", (-0.80, 0.35, 0.01))
#     # Velocity now auto-computed; no prompt needed

#     meta, timeline = generate_impact_scenario(
#         asteroid_id=asteroid_id,
#         diameter_km=diameter_km,
#         impact_time_iso=Ti_iso,
#         asteroid_r0_au=ast_r0,
#     )

#     # Save JSON explicitly (API does not save)
#     json_path = save_json(asteroid_id, meta, timeline)

#     eff = meta["impact_effects"]
#     surf = meta["surface_impact"]
#     lat = surf["impact_point"]["latitude_deg"]
#     lon = surf["impact_point"]["longitude_deg"]
#     v_impact_km_s = surf["velocity_at_impact"]["ground_relative_speed_km_s"]
#     v0 = meta["initial_conditions"]["asteroid_T0"]["v_au_per_day"]
#     crater_D_km = eff["crater_diameter_km_heuristic"]
#     casualties = eff["casualties"]["fatalities_total_est"]
#     print("\n--- RÉSUMÉ IMPACT ---")
#     print(f"Diamètre projectile        : {meta['asteroid']['diameter_km']:.3f} km")
#     print(f"Vitesse d'impact (sol)     : {v_impact_km_s:.3f} km/s")
#     print(f"Latitude / Longitude       : {lat:.3f}°, {lon:.3f}°")
#     print(f"Energie d'impact           : {eff['energy_joules']:.3e} J  (~{eff['yield_kilotons']:.1f} kt, ~{eff['hiroshima_equiv']:.1f} 'Hiroshima')")
#     print(f"Rayons onde de choc (km)   : {eff['blast_radii_km']}")
#     print(f"Diamètre de cratère (heur.) : {crater_D_km:.2f} km")
#     print(f"Nombre de morts (est.)     : {casualties:.0f}")
#     print(f"v0 résolu (AU/jour)        : ({v0['x']:.6f}, {v0['y']:.6f}, {v0['z']:.6f})")
#     print(f"\n✅ JSON écrit : {json_path}")

# if __name__ == "__main__":
#     main()
