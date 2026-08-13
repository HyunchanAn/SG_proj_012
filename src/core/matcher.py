import os

import httpx
from loguru import logger

from src.models.schemas import MatchingRequest, ProductRecommendation


class MatchingRule:
    def __init__(self, code: str, se: float, rough: float, proc: int, finish: str):
        self.code = code
        self.surface_energy = se
        self.roughness = rough
        self.processability_level = proc
        self.finish_type = finish

# 004 DB API URL from env
MODULE_004_URL = os.getenv("MODULE_004_URL", "http://004-db:8004")

async def load_stock_matrix(req_id: str = "unknown") -> dict[int, int]:
    """Fetch adherend stocks from 004 DB."""
    stocks_map: dict[int, int] = {}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"X-Request-ID": req_id}
            res = await client.get(f"{MODULE_004_URL}/adherend-stocks", headers=headers)
            if res.status_code == 200:
                stocks = res.json()
                for st in stocks:
                    prop_id = st.get("adherend_property_id")
                    if prop_id is not None:
                        stocks_map[prop_id] = stocks_map.get(prop_id, 0) + st.get("quantity", 0)
            else:
                logger.error(f"[{req_id}] Failed to fetch stocks. 004 API returned {res.status_code}")
    except Exception as e:
        logger.error(f"[{req_id}] Failed to fetch stocks from 004 DB: {e}")
    return stocks_map

async def load_rule_matrix(req_id: str = "unknown") -> tuple[list[MatchingRule], bool]:
    """Fetch products from 004 DB and convert to MatchingRule."""
    matrix = []
    is_local_fallback = False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"X-Request-ID": req_id}
            res = await client.get(f"{MODULE_004_URL}/products", headers=headers)
            if res.status_code == 200:
                products = res.json()
                for p in products:
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
                    else:
                        logger.warning(f"[{req_id}] 012 Matcher: Product '{p.get('product_name')}' ignored due to null target_surface_energy.")
            else:
                raise RuntimeError(f"004 API returned {res.status_code}")
    except Exception as e:
        logger.error(f"[{req_id}] Failed to fetch products from 004 DB: {e}. Using local fallback.")
        is_local_fallback = True
        matrix = [
            MatchingRule("Fallback-General", 40.0, 1000.0, 3, "Any"),
            MatchingRule("Fallback-Smooth", 35.0, 500.0, 2, "Mirror")
        ]
    return matrix, is_local_fallback
from src.core.mcda import calculate_topsis_scores

async def match_products(req: MatchingRequest, req_id: str = "unknown") -> tuple[list[ProductRecommendation], str]:
    logger.info(f"[{req_id}] 012 Matcher: Start matching. Input SFE: {req.surface_energy:.4f}, Roughness: {req.roughness:.4f}, Required Processability: {req.required_processability_level}")
    
    rule_matrix, is_local_fallback = await load_rule_matrix(req_id)
    
    candidates_to_evaluate = []
    for rule in rule_matrix:
        if rule.processability_level > req.required_processability_level:
            continue
            
        candidates_to_evaluate.append({
            "id": rule.code,
            "se": rule.surface_energy,
            "rough": rule.roughness,
            "proc": rule.processability_level,
            "finish": rule.finish_type
        })
        
    if not candidates_to_evaluate:
        logger.warning(f"[{req_id}] 012 Matcher: No candidates passed the hard processability constraint.")
        return [], "local_fallback" if is_local_fallback else "database"

    scored_candidates = calculate_topsis_scores(
        req_se=req.surface_energy,
        req_rough=req.roughness,
        req_proc=req.required_processability_level,
        req_finish=req.finish_type,
        candidates=candidates_to_evaluate
    )
    
    recommendations = []
    for c in scored_candidates:
        if c["topsis_score"] > 0:
            recommendations.append(
                ProductRecommendation(
                    product_code=c["id"],
                    match_score=round(c["topsis_score"], 2),
                    match_reason=c["details"]
                )
            )
            
    recommendations.sort(key=lambda x: x.match_score, reverse=True)
    logger.info(f"[{req_id}] 012 Matcher: Matching complete. Selected top {len(recommendations[:3])} recommendations.")
    return recommendations[:3], "local_fallback" if is_local_fallback else "database"
