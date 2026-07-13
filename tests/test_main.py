# TOPSIS 다기준 의사결정 추천 매칭 모듈의 FastAPI 엔드포인트(/match) 및 가중치 매칭 점수 산출 로직을 검증하는 테스트 코드입니다.
from fastapi.testclient import TestClient
from src.main import app
import pytest

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_load_rule_matrix(monkeypatch):
    from src.core.matcher import MatchingRule
    async def mock_load():
        return [
            MatchingRule("PRD-001", 32.0, 600.0, 2, "Hairline"),
            MatchingRule("PRD-002", 40.0, 1000.0, 3, "2B"),
            MatchingRule("PRD-003", 35.0, 800.0, 1, "BA")
        ]
    monkeypatch.setattr("src.core.matcher.load_rule_matrix", mock_load)

def test_match_successful():
    # Surface energy matches PRD-001 or PRD-003 or PRD-002, processability is low enough
    payload = {
        "substrate_id": "sub-123",
        "surface_energy": 32.0,
        "roughness": 600.0,
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
        "roughness": 600.0,
        "finish_type": "Hairline",
        "required_processability_level": 0
    }
    res = client.post("/match", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["recommendations"]) == 0
    assert data["is_successful"] is False
