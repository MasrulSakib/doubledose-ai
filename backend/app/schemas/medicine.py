
from pydantic import BaseModel, ConfigDict


class MedicineResponse(BaseModel):
    id: int
    brand_name: str
    generic_name: str | None = None
    dosage_form: str | None = None
    manufacturer: str | None = None

    model_config = ConfigDict(from_attributes=True)