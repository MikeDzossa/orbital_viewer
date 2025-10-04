import os
import pytest
from fastapi.testclient import TestClient

# Ensure debug logs can be toggled during tests
os.environ.setdefault("ORBITAL_DEBUG", "0")

from backend.app import app  # noqa: E402
from backend.core.models import OrbitalElements  # noqa: E402

client = TestClient(app)

# --- Fixtures --- #


@pytest.fixture
def sample_elements():
    return OrbitalElements(
      e=0.2056484321472573,
      a=57908912.27023789,
      i=7.00344805866192,
      raan=48.29898906169271,
      argp=29.19834566085932,
      M0=141.1547654302108,
      epoch="2025-10-01 00:00"
    )


# --- Tests --- #


def test_orbit_endpoint(sample_elements):
    payload = sample_elements.model_dump()
    r = client.post("/api/orbit", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "trajectory" in data
    assert isinstance(data["trajectory"], list)
    assert len(data["trajectory"]) > 0


def test_planets_endpoint_monkeypatch(monkeypatch, sample_elements):
    # Monkeypatch the network call to avoid external dependency
    epoch = "2025-10-01 01:10"
    def fake_fetch(pid: str, epoch: str = epoch):
        return sample_elements

    monkeypatch.setattr("backend.core.planets.fetch_planets_elements", fake_fetch)

    r = client.get(f"/api/planets?epoch={epoch}")
    assert r.status_code == 200
    data = r.json()
    assert "epoch" in data
    assert data["epoch"] == epoch
    assert "planets" in data
    assert isinstance(data["planets"], dict)
    # All planets should have the same mocked elements structure
    for name, elems in data["planets"].items():
        # elems might be serialized Pydantic model
        assert set(elems.keys()) >= {"a", "e", "i", "raan", "argp", "M0", "epoch"}


def test_orbit_bad_payload():
    # Missing required field 'a'
    bad = {
        "e": 0.01,
        "i": 1.0,
        "raan": 0.0,
        "argp": 0.0,
        "M0": 0.0,
        "epoch": "2025-10-01",
    }
    r = client.post("/api/orbit", json=bad)
    assert r.status_code == 422  # validation error
