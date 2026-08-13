from pydantic import BaseModel, Field

class MatchingRequest(BaseModel):
    substrate_id: str
    surface_energy: float
    roughness: float
    finish_type: str
    required_processability_level: int

class ProductRecommendation(BaseModel):
    product_code: str
    match_score: float
    match_reason: dict  # {"surface_energy_norm": 0.9, "roughness_norm": 0.8, ...}

class MatchingResponse(BaseModel):
    recommendations: list[ProductRecommendation] = Field(default_factory=list, max_length=3)
    is_successful: bool
    source: str = "database"
