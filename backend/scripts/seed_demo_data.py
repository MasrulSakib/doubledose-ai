
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.medicine import (
    ActiveIngredient,
    Medicine,
    MedicineIngredient,
)


# Fictional development data only.
# These are NOT real medicines or medical ingredient mappings.
DEMO_DATA = [
    {
        "brand_name": "Demo Product A",
        "generic_name": "Demo Compound A",
        "ingredients": [
            {"name": "demo ingredient alpha", "amount": 100, "unit": "mg"},
        ],
    },
    {
        "brand_name": "Demo Product B",
        "generic_name": "Demo Compound B",
        "ingredients": [
            {"name": "demo ingredient alpha", "amount": 50, "unit": "mg"},
            {"name": "demo ingredient beta", "amount": 20, "unit": "mg"},
        ],
    },
]


def seed_demo_data() -> None:
    with SessionLocal() as db:
        try:
            for item in DEMO_DATA:
                medicine = db.scalar(
                    select(Medicine).where(
                        Medicine.brand_name == item["brand_name"]
                    )
                )

                if medicine is None:
                    medicine = Medicine(
                        brand_name=item["brand_name"],
                        generic_name=item["generic_name"],
                    )
                    db.add(medicine)
                    db.flush()

                for ingredient_data in item["ingredients"]:
                    ingredient = db.scalar(
                        select(ActiveIngredient).where(
                            ActiveIngredient.name
                            == ingredient_data["name"]
                        )
                    )

                    if ingredient is None:
                        ingredient = ActiveIngredient(
                            name=ingredient_data["name"]
                        )
                        db.add(ingredient)
                        db.flush()

                    existing_link = db.scalar(
                        select(MedicineIngredient).where(
                            MedicineIngredient.medicine_id == medicine.id,
                            MedicineIngredient.ingredient_id == ingredient.id,
                        )
                    )

                    if existing_link is None:
                        db.add(
                            MedicineIngredient(
                                medicine_id=medicine.id,
                                ingredient_id=ingredient.id,
                                amount=ingredient_data["amount"],
                                unit=ingredient_data["unit"],
                            )
                        )

            db.commit()
            print("Demo data seeded successfully.")

        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    seed_demo_data()
