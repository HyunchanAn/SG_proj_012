from fastapi import FastAPI
from src.models.schemas import MatchingRequest, MatchingResponse
from src.core.matcher import match_products

app = FastAPI(title="SG_proj_012 - Product Matching Engine")

@app.post("/match", response_model=MatchingResponse)
async def match(req: MatchingRequest):
    recommendations = await match_products(req)
    return MatchingResponse(
        recommendations=recommendations,
        is_successful=len(recommendations) > 0
    )

