import re
from .models import OrbitalElements
from .constants import PLANET_IDS
from .services.api import get_horizons_response
from .logging_utils import get_logger
from .config import ENABLE_DEBUG_LOGS

logger = get_logger(__name__)

PATTERNS = {
    "e": r"EC=\s*([\-0-9.E+]+)",
    "a": r"(?:^|\s|\n)A\s*=\s*([\-0-9.E+]+)",
    "i": r"IN=\s*([\-0-9.E+]+)",
    "raan": r"OM=\s*([\-0-9.E+]+)",
    "argp": r"W\s*=\s*([\-0-9.E+]+)",
    "M0": r"MA=\s*([\-0-9.E+]+)",
}


def extract_orbital_elements(text: str, patterns=PATTERNS):
    """Extract orbital elements from Horizons text block using regex patterns."""
    return {
        key: float(match.group(1))
        for key, pattern in patterns.items()
        if (match := re.search(pattern, text))
    }


def fetch_planet_data(planet_id: str, epoch: str = "2025-10-01"):
    """Fetch and parse orbital elements for a planet from Horizons."""
    text_block = get_horizons_response(planet_id, epoch)
    if not text_block:
        logger.warning("Empty result block for planet_id=%s epoch=%s", planet_id, epoch)
    elements = extract_orbital_elements(text_block)
    elements["epoch"] = epoch  # Add epoch to the elements
    logger.debug("Extracted elements for planet_id=%s: %s", planet_id, elements)
    missing = [k for k in ["a", "e", "i", "raan", "argp", "M0", "epoch"] if k not in elements]
    if missing:
        logger.error(
            "Missing required elements planet=%s: %s", PLANET_IDS[planet_id], missing
        )
        raise ValueError(f"Missing required elements: {missing}")

    logger.debug("Constructed OrbitalElements planet_id=%s: %s", planet_id, elements)
    return elements


# === New helper ===


def fetch_planets_elements(epoch: str = "2025-10-01"):
    """Loop over multiple planet ids and return their orbital elements."""
    logger.info(
        "Fetching multiple planet elements epoch=%s debug=%s", epoch, ENABLE_DEBUG_LOGS
    )
    results = {}
    for planet, pid in PLANET_IDS.items():
        try:
            elements = fetch_planet_data(pid, epoch)
            results[planet] = elements
        except Exception as e:
            logger.warning("Failed planet=%s id=%s: %s", planet, pid, e)
            results[planet] = {"error": str(e)}
    logger.debug("Fetch complete for epoch=%s planets=%s", epoch, list(results.keys()))
    return {"epoch": epoch, "planets": results}
