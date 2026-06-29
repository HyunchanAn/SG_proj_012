from typing import List, Tuple, Dict
from src.models.schemas import MatchingRequest, ProductRecommendation

class MatchingRule:
    def __init__(self, code: str, se: float, rough: float, proc: int, finish: str):
        self.code = code
        self.surface_energy = se
        self.roughness = rough
        self.processability_level = proc
        self.finish_type = finish

# Matching Rule Matrix for Our Products
RULE_MATRIX = [
    MatchingRule("SGV225", 38.6, 0.8, 2, "2B"),
    MatchingRule("SGV250", 40.0, 1.0, 3, "2B"),
    MatchingRule("SGV201", 42.5, 0.2, 1, "BA"),
    MatchingRule("SGV202", 40.0, 0.5, 2, "BA"),
    MatchingRule("SGV218ME", 37.5, 0.3, 4, "Hairline"),
    MatchingRule("SGV220", 35.0, 0.4, 3, "Hairline"),
]

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
