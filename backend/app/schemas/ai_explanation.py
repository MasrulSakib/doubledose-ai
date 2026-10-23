from typing import Literal

from pydantic import BaseModel, Field


class OverlapIngredientInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    medicine_names: list[str] = Field(default_factory=list, max_length=5)


class AIExplanationMedicineInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    generic_name: str | None = Field(default=None, max_length=500)
    source_details: str | None = Field(default=None, max_length=1000)
    dosage_form: str | None = Field(default=None, max_length=150)
    manufacturer: str | None = Field(default=None, max_length=200)
    side_effects: list[str] = Field(default_factory=list, max_length=30)
    daily_dose: str | None = Field(default=None, max_length=300)
    information_source: str | None = Field(default=None, max_length=500)
    source_url: str | None = Field(default=None, max_length=1000)


class AIExplanationRequest(BaseModel):
    result_status: Literal[
        "overlap_found",
        "no_overlap_found",
        "incomplete_data",
    ]
    medicine_names: list[str] = Field(min_length=1, max_length=5)
    medicines: list[AIExplanationMedicineInput] = Field(
        default_factory=list,
        max_length=5,
    )
    overlapping_ingredients: list[OverlapIngredientInput] = Field(
        default_factory=list,
        max_length=30,
    )
    medicines_without_ingredient_data: list[str] = Field(
        default_factory=list,
        max_length=5,
    )


class AIExplanationResponse(BaseModel):
    explanation: str
    limitations: list[str]
    disclaimer: str
