import math
import pytest
from src.core.mcda import calculate_topsis_scores, MCDA_CONFIG

def test_calculate_topsis_scores_perfect_match():
    # Force weights and bounds to known values for mathematical validation
    MCDA_CONFIG["weights"] = {
        "surface_energy": 0.5,
        "roughness": 0.2,
        "processability": 0.2,
        "finish_type": 0.1
    }
    MCDA_CONFIG["reference_bounds"] = {
        "surface_energy_diff_max": 50.0,
        "roughness_diff_max": 5000.0,
        "processability_diff_max": 5.0
    }
    
    req_se = 35.0
    req_rough = 500.0
    req_proc = 2
    req_finish = "BA"
    
    # Perfect match candidate
    candidates = [{
        "id": "PRD-PERFECT",
        "se": 35.0,
        "rough": 500.0,
        "proc": 2,
        "finish": "BA"
    }]
    
    results = calculate_topsis_scores(req_se, req_rough, req_proc, req_finish, candidates)
    
    assert len(results) == 1
    c = results[0]
    assert c["id"] == "PRD-PERFECT"
    
    # Mathematical validation for perfect match:
    # All diffs = 0 -> norm = 0.
    # v_se = 0, v_rough = 0, v_proc = 0, v_finish = 0.1
    # d_pos (distance to PIS): sqrt(0 + 0 + 0 + (0.1 - 0.1)^2) = 0.0
    # d_neg (distance to NIS): sqrt((0 - 0.5)^2 + (0 - 0.2)^2 + (0 - 0.2)^2 + (0.1 - 0)^2) 
    # = sqrt(0.25 + 0.04 + 0.04 + 0.01) = sqrt(0.34)
    # closeness = d_neg / (d_pos + d_neg) = sqrt(0.34) / (0 + sqrt(0.34)) = 1.0
    # Score should be 100.0
    assert c["topsis_score"] == 100.0
    assert c["details"]["surface_energy_norm"] == 1.0
    assert c["details"]["roughness_norm"] == 1.0
    assert c["details"]["processability_norm"] == 1.0
    assert c["details"]["finish_match"] == 1.0

def test_calculate_topsis_scores_partial_match():
    # Force weights and bounds
    MCDA_CONFIG["weights"] = {
        "surface_energy": 0.5,
        "roughness": 0.2,
        "processability": 0.2,
        "finish_type": 0.1
    }
    
    candidates = [{
        "id": "PRD-PARTIAL",
        "se": 60.0,      # Diff = 25.0, norm = 25/50 = 0.5
        "rough": 3000.0, # Diff = 2500, norm = 2500/5000 = 0.5
        "proc": 0,       # Diff = 2, norm = 2/5 = 0.4
        "finish": "2B"   # Mismatch, score = 0.0
    }]
    
    results = calculate_topsis_scores(
        req_se=35.0, 
        req_rough=500.0, 
        req_proc=2, 
        req_finish="BA", 
        candidates=candidates
    )
    
    c = results[0]
    
    # v_se = 0.5 * 0.5 = 0.25
    # v_rough = 0.2 * 0.5 = 0.1
    # v_proc = 0.2 * 0.4 = 0.08
    # v_finish = 0.0
    
    # PIS: (0, 0, 0, 0.1)
    # d_pos = sqrt((0.25 - 0)^2 + (0.1 - 0)^2 + (0.08 - 0)^2 + (0.0 - 0.1)^2)
    #       = sqrt(0.0625 + 0.01 + 0.0064 + 0.01) = sqrt(0.0889) = 0.29816...
    
    # NIS: (0.5, 0.2, 0.2, 0)
    # d_neg = sqrt((0.25 - 0.5)^2 + (0.1 - 0.2)^2 + (0.08 - 0.2)^2 + (0.0 - 0)^2)
    #       = sqrt(0.0625 + 0.01 + 0.0144 + 0) = sqrt(0.0869) = 0.29478...
    
    # closeness = 0.29478 / (0.29816 + 0.29478) = 0.29478 / 0.59294 = 0.4971
    # topsis_score should be around 49.71
    
    assert 49.0 < c["topsis_score"] < 50.0
    assert c["details"]["surface_energy_norm"] == 0.5
    assert c["details"]["roughness_norm"] == 0.5
    assert c["details"]["processability_norm"] == 0.6
    assert c["details"]["finish_match"] == 0.0
