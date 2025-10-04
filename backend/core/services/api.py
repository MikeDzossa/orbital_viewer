import requests
from ..logging_utils import get_logger
from ..config import ENABLE_DEBUG_LOGS

logger = get_logger(__name__)


def get_horizons_response(planet_id: str, epoch: str) -> str:
    """Request orbital elements data from JPL Horizons API for a single epoch.

    For a single instant the more robust approach is to provide a TLIST of times
    instead of START/STOP/STEP_SIZE. This avoids the parser ambiguity.
    """
    url = "https://ssd.jpl.nasa.gov/api/horizons.api"
    params = {
        "format": "json",
        "COMMAND": f"'{planet_id}'",
        "MAKE_EPHEM": "YES",
        "EPHEM_TYPE": "ELEMENTS",
        "TLIST": f"'{epoch}'",
        "CENTER": "'@sun'",
    }
    logger.debug(
        "Requesting Horizons planet_id=%s epoch=%s params=%s", planet_id, epoch, params
    )
    resp = requests.get(url, params=params, timeout=30)
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        snippet = resp.text[:300].replace("\n", " ")
        logger.warning(
            "Horizons HTTP error planet_id=%s status=%s: %s | body snippet=%s",
            planet_id,
            resp.status_code,
            exc,
            snippet,
        )
        raise
    try:
        data = resp.json()
    except ValueError:
        logger.error(
            "Non-JSON response for planet_id=%s first 300 chars=%s",
            planet_id,
            resp.text[:300],
        )
        raise
    result_text = data.get("result", "")
    if not result_text:
        logger.warning(
            "No 'result' field returned for planet_id=%s keys=%s",
            planet_id,
            list(data.keys()),
        )
    # Log any Horizons-side INPUT ERROR lines to aid debugging
    if "INPUT ERROR" in result_text:
        logger.error(
            "Horizons INPUT ERROR planet_id=%s epoch=%s snippet=%s",
            planet_id,
            epoch,
            result_text[:250].replace("\n", " "),
        )
    return result_text
