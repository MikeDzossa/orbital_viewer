// Optional base URL (can be overridden in Vite env: VITE_API_BASE)
const API_BASE = import.meta?.env?.VITE_API_BASE || '';

// Fetch a set of space points computed from initial orbital parameters
// params: { a, e, i, raan, argp, M0, epoch, ... } - orbital elements and options
// Expected outcome: Returns an array of points [{ x, y, z, t }, ...] representing the orbit in space over time
// On error: throws or returns { error }
export async function fetchOrbit(params, steps = 1000) {
  const res = await fetch(`${API_BASE}/api/orbit?steps=${steps}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    throw new Error(`Orbit fetch failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// Fetch planetary orbital elements (all planets) for a given epoch (ISO date string)
// Returns shape: { epoch: string, planets: { planetName: { a,e,i,raan,argp,M0,epoch } | { error } } }
export async function fetchPlanets(epoch = "2025-10-01 00:00") {
  const url = `${API_BASE}/api/planets?epoch=${encodeURIComponent(epoch)}`;
  const res = await fetch(url, { method: 'GET' });
  if (!res.ok) {
    throw new Error(`Planets fetch failed: ${res.status} ${res.statusText}`);
  }
  const data = await res.json();
  return data;
}

/**
 * Create an impact scenario.
 * @param {Object} params
 * @param {string} params.asteroid_id - Identifier for the scenario (metadata only)
 * @param {number} params.diameter_km - Asteroid diameter in kilometers (>0)
 * @param {string} params.impact_time_iso - Target impact time ISO UTC (e.g. 2027-01-04T00:00:00Z)
 * @param {[number,number,number]} params.asteroid_r0_au - Initial asteroid heliocentric position (AU)
 * @returns {Promise<{metadata: Object, timeline: Array}>}
 */
export async function createImpactScenario(params) {
  const res = await fetch(`${API_BASE}/api/impact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Impact scenario failed: ${res.status} ${res.statusText} - ${text}`);
  }
  return res.json();
}
