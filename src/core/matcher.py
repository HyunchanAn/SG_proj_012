from typing import List, Tuple, Dict
from src.models.schemas import MatchingRequest, ProductRecommendation

class MatchingRule:
    def __init__(self, code: str, se: float, rough: float, proc: int, finish: str):
        self.code = code
        self.surface_energy = se
        self.roughness = rough
        self.processability_level = proc
        self.finish_type = finish

import httpx
import os

# 004 DB API URL from env
MODULE_004_URL = os.getenv("MODULE_004_URL", "http://004-db:8004")

async def load_rule_matrix() -> List[MatchingRule]:
    """Fetch products from 004 DB and convert to MatchingRule."""
    matrix = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{MODULE_004_URL}/products")
            if res.status_code == 200:
                products = res.json()
                for p in products:
                    # Filter out products that don't have matching targets defined
                    if p.get("target_surface_energy") is not None:
                        matrix.append(
                            MatchingRule(
                                p.get("product_name") or p.get("category", "UNKNOWN"),
                                p.get("target_surface_energy"),
                                p.get("target_roughness", 0.0),
                                p.get("target_processability_level", 3),
                                p.get("target_finish_type", "Any")
                            )
                        )
    except Exception as e:
        import logging
        logging.error(f"Failed to fetch products from 004 DB: {e}")
    return matrix
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

async def match_products(req: MatchingRequest) -> List[ProductRecommendation]:
    recommendations = []
    
    rule_matrix = await load_rule_matrix()
    
    for rule in rule_matrix:
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
