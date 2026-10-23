
from typing import Literal

from pydantic import BaseModel, Field


class OverlapIngredientInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    medicine_names: list[str] = Field(
        default_factory=list,
        max_length=5,
    )


class AIExplanationIngredientInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    amount: float | None = None
    unit: str | None = Field(default=None, max_length=30)
    source_name: str | None = Field(default=None, max_length=100)
    source_record_id: str | None = Field(default=None, max_length=200)
    source_url: str | None = Field(default=None, max_length=500)
    retrieved_at: str | None = None


class AIExplanationMedicineInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    generic_name: str | None = Field(default=None, max_length=500)
    source_details: str | None = Field(default=None, max_length=1000)
    dosage_form: str | None = Field(default=None, max_length=100)
    manufacturer: str | None = Field(default=None, max_length=200)
    ingredients: list[AIExplanationIngredientInput] = Field(
        default_factory=list,
        max_length=50,
    )
    side_effects: list[str] = Field(
        default_factory=list,
        max_length=30,
    )
    daily_dose: str | None = Field(default=None, max_length=300)


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
