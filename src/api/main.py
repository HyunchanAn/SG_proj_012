from fastapi import FastAPI
from src.models.schemas import MatchingRequest, MatchingResponse
from src.core.matcher import match_products

app = FastAPI(title="SG_proj_012: Product Matching")

@app.post("/match", response_model=MatchingResponse)
def match(request: MatchingRequest) -> MatchingResponse:
    recommendations = match_products(request)
    is_successful = len(recommendations) > 0
    return MatchingResponse(
        recommendations=recommendations,
        is_successful=is_successful
    )
