from pydantic import BaseModel, Field


class MatcherComparisonRequest(BaseModel):
    extracted_text: str = Field(min_length=1, max_length=10000)
    limit: int = Field(default=10, ge=1, le=20)


class MatcherComparisonResponse(BaseModel):
    rapidfuzz: list[dict]
    tfidf: list[dict]
    extracted_text: str