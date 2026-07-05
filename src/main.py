from fastapi import FastAPI
from src.models.schemas import MatchingRequest, MatchingResponse
from src.core.matcher import match_products
from loguru import logger

app = FastAPI(title="SG_proj_012 - Product Matching Engine")

@app.post("/match", response_model=MatchingResponse)
async def match(req: MatchingRequest):
    logger.info("012 API: Received product matching request.")
    recommendations = await match_products(req)
    return MatchingResponse(
        recommendations=recommendations,
        is_successful=len(recommendations) > 0
    )

