from typing import List, Tuple, Dict
from src.models.schemas import MatchingRequest, ProductRecommendation

class MatchingRule:
    def __init__(self, code: str, se: float, rough: float, proc: int, finish: str):
        self.code = code
        self.surface_energy = se
        self.roughness = rough
        self.processability_level = proc
        self.finish_type = finish

import json
from pathlib import Path

# Load Matching Rule Matrix dynamically
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RULE_FILE = BASE_DIR / "data" / "rule_matrix.json"

RULE_MATRIX = []
if RULE_FILE.exists():
    with open(RULE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        for d in data:
            RULE_MATRIX.append(
                MatchingRule(
                    d.get("code"),
                    d.get("surface_energy"),
                    d.get("roughness"),
                    d.get("processability_level"),
                    d.get("finish_type")
                )
            )
else:
    import logging
    logging.warning("rule_matrix.json not found! Matching rules are empty.")
def calculate_score(req: MatchingRequest, rule: MatchingRule) -> Tuple[float, Dict[str, float]]:
    # Hard constraint on processability
    # If the product is stiffer (higher level) than required, it fails.
    if rule.processability_level > req.required_processability_level:
        return 0.0, {}
    
    # 20% Processability Score
    proc_score = 100.0 - (req.required_processability_level - rule.processability_level) * 10
    proc_score = max(0.0, min(100.0, proc_score))
    
    # 60% Surface Energy Score
    se_diff = abs(req.surface_energy - rule.surface_energy)
    se_score = max(0.0, 100.0 - se_diff * 2)
    
    # 20% Roughness Score
    r_diff = abs(req.roughness - rule.roughness)
    r_score = max(0.0, 100.0 - r_diff * 20)
    
    total = 0.6 * se_score + 0.2 * r_score + 0.2 * proc_score
    
    return total, {
        "surface_energy_score": round(se_score * 0.6, 2),
        "roughness_score": round(r_score * 0.2, 2),
        "processability_score": round(proc_score * 0.2, 2)
    }

def match_products(req: MatchingRequest) -> List[ProductRecommendation]:
    recommendations = []
    
    for rule in RULE_MATRIX:
        score, reason = calculate_score(req, rule)
        if score > 0:
            recommendations.append(
                ProductRecommendation(
                    product_code=rule.code,
                    match_score=round(score, 2),
                    match_reason=reason
                )
            )
            
    # Sort by score descending and take top 3
    recommendations.sort(key=lambda x: x.match_score, reverse=True)
    return recommendations[:3]
