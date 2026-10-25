
from pydantic import BaseModel, Field


class MatcherComparisonRequest(BaseModel):
    extracted_text: str = Field(min_length=1, max_length=10000)
    limit: int = Field(default=10, ge=1, le=20)


class MatcherCandidate(BaseModel):
    medicine_id: int
    brand_name: str
    generic_name: str | None = None
    strength: str | None = None
    match_score: float = Field(ge=0, le=100)
    needs_confirmation: bool
    ranking_score: float | None = Field(default=None, ge=0, le=100)


class MatcherComparisonResponse(BaseModel):
    rapidfuzz: list[MatcherCandidate]
    tfidf: list[MatcherCandidate]
    extracted_text: str
