from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_match_successful():
    # Surface energy matches PRD-001 or PRD-003 or PRD-002, processability is low enough
    payload = {
        "substrate_id": "sub-123",
        "surface_energy": 32.0,
        "roughness": 0.6,
        "finish_type": "Hairline",
        "required_processability_level": 3
    }
    res = client.post("/match", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0
    assert data["is_successful"] is True
    # Verify the structure
    rec = data["recommendations"][0]
    assert "product_code" in rec
    assert "match_score" in rec
    assert "match_reason" in rec

def test_match_no_results():
    # If required_processability_level is extremely low (e.g. 0), we shouldn't match anything since lowest DB product is 1
    payload = {
        "substrate_id": "sub-123",
        "surface_energy": 32.0,
        "roughness": 0.6,
        "finish_type": "Hairline",
        "required_processability_level": 0
    }
    res = client.post("/match", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["recommendations"]) == 0
    assert data["is_successful"] is False
