from fastapi import FastAPI, Header
from loguru import logger
from typing import Optional
from src.core.matcher import match_products
from src.models.schemas import MatchingRequest, MatchingResponse

app = FastAPI(title="SG_proj_012 - Product Matching Engine")

@app.post("/match", response_model=MatchingResponse)
async def match(req: MatchingRequest, x_request_id: Optional[str] = Header(None, alias="X-Request-ID")):
    req_id = x_request_id or "unknown"
    logger.info(f"[{req_id}] 012 API: Received product matching request.")
    recommendations, source = await match_products(req, req_id)
    return MatchingResponse(
        recommendations=recommendations,
        is_successful=len(recommendations) > 0,
        source=source
    )

