import json
import math
import os
from pathlib import Path

from loguru import logger

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config.json"
try:
    with open(CONFIG_PATH, "r") as f:
        MCDA_CONFIG = json.load(f)
except Exception as e:
    logger.error(f"Failed to load MCDA config: {e}. Using fallback defaults.")
    MCDA_CONFIG = {
        "weights": {
            "surface_energy": 0.40,
            "roughness": 0.20,
            "processability": 0.20,
            "finish_type": 0.20
        },
        "reference_bounds": {
            "surface_energy_diff_max": 50.0,
            "roughness_diff_max": 5000.0,
            "processability_diff_max": 5.0
        }
    }


def calculate_topsis_scores(
    req_se: float, req_rough: float, req_proc: int, req_finish: str,
    candidates: list[dict]
) -> list[dict]:
    """
    Perform a formal reference-based TOPSIS evaluation on a list of candidates.
    Candidates should be a list of dicts with:
      {'id': ..., 'se': ..., 'rough': ..., 'proc': ..., 'finish': ...}
      
    Returns the candidates list with added 'topsis_score' and 'details' fields.
    """
    if not candidates:
        return []

    # 1. Configuration & Weights
    w = MCDA_CONFIG["weights"]
    w_se = w.get("surface_energy", 0.4)
    w_rough = w.get("roughness", 0.2)
    w_proc = w.get("processability", 0.2)
    w_finish = w.get("finish_type", 0.2)
    
    b = MCDA_CONFIG["reference_bounds"]
    max_se_diff = b.get("surface_energy_diff_max", 50.0)
    max_rough_diff = b.get("roughness_diff_max", 5000.0)
    max_proc_diff = b.get("processability_diff_max", 5.0)

    # 2. Decision Matrix & Vector Normalization
    # Since we want absolute stability (no rank reversal), we use predefined reference limits
    # instead of finding min/max across the current candidate pool.
    
    # We formulate this as distance to the Theoretical Positive Ideal Solution (PIS)
    # and Negative Ideal Solution (NIS).
    
    # Cost Criteria (diffs to minimize): SE, Roughness, Processability
    # Benefit Criteria: Finish Type (1 = match, 0 = mismatch)
    
    scored_candidates = []
    
    for c in candidates:
        # Calculate raw differences
        diff_se = abs(req_se - c["se"])
        diff_rough = abs(req_rough - c["rough"])
        diff_proc = float(abs(req_proc - c["proc"]))
        finish_match = 1.0 if (c["finish"] == "Any" or c["finish"] == req_finish) else 0.0
        
        # Min-Max Normalization using reference bounds (0 = ideal cost, max = worst cost)
        # norm_x = (x - min) / (max - min). Since min=0, norm_x = x / max
        # Cap at 1.0 (worst)
        norm_se = min(1.0, diff_se / max_se_diff)
        norm_rough = min(1.0, diff_rough / max_rough_diff)
        norm_proc = min(1.0, diff_proc / max_proc_diff)
        
        # Weighted Normalized Values
        v_se = w_se * norm_se
        v_rough = w_rough * norm_rough
        v_proc = w_proc * norm_proc
        v_finish = w_finish * finish_match
        
        # PIS (Ideal): Cost diffs = 0, Benefit match = 1
        # v_ideal_se = 0, v_ideal_rough = 0, v_ideal_proc = 0, v_ideal_finish = w_finish
        d_pos = math.sqrt(
            (v_se - 0.0)**2 + 
            (v_rough - 0.0)**2 + 
            (v_proc - 0.0)**2 + 
            (v_finish - w_finish)**2
        )
        
        # NIS (Worst): Cost diffs = Max (weighted), Benefit match = 0
        # v_worst_se = w_se, v_worst_rough = w_rough, v_worst_proc = w_proc, v_worst_finish = 0
        d_neg = math.sqrt(
            (v_se - w_se)**2 + 
            (v_rough - w_rough)**2 + 
            (v_proc - w_proc)**2 + 
            (v_finish - 0.0)**2
        )
        
        # Relative Closeness to Ideal Solution (0 to 1)
        # Convert to 100-point scale
        closeness = d_neg / (d_pos + d_neg) if (d_pos + d_neg) > 0 else 0.0
        score = closeness * 100.0
        
        c["topsis_score"] = score
        c["details"] = {
            "surface_energy_norm": round(1.0 - norm_se, 2),
            "roughness_norm": round(1.0 - norm_rough, 2),
            "processability_norm": round(1.0 - norm_proc, 2),
            "finish_match": finish_match
        }
        scored_candidates.append(c)
        
    return scored_candidates
