
from pydantic import BaseModel, ConfigDict, Field, field_validator


class MedicineResponse(BaseModel):
    id: int
    brand_name: str
    source_display_name: str | None = None
    generic_name: str | None = None
    dosage_form: str | None = None
    manufacturer: str | None = None

    model_config = ConfigDict(from_attributes=True)

class IngredientResponse(BaseModel):
    id: int
    name: str
    amount: float | None = None
    unit: str | None = None

class OverlapCheckRequest(BaseModel):
    medicine_ids: list[int] = Field(
        min_length=2,
        max_length=5,
        description="IDs of 2 to 5 medicines to compare",
    )

    @field_validator("medicine_ids")
    @classmethod
    def validate_unique_medicine_ids(cls, value: list[int]) -> list[int]:
        if len(value) != len(set(value)):
            raise ValueError("Medicine IDs must be unique")
        return value

class OverlappingIngredient(BaseModel):
    ingredient_id: int
    name: str
    medicine_ids: list[int]
    medicine_names: list[str]

class OverlapCheckResponse(BaseModel):
    medicines: list[MedicineResponse]
    has_overlap: bool
    overlapping_ingredients: list[OverlappingIngredient]
