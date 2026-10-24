
import re
from collections import defaultdict

from app.models.medicine import Medicine
from app.schemas.medicine import SameClassWarning
from app.services.ingredient_normalizer import canonical_ingredient_key


def normalize_ingredient_name(name: str) -> str:
    """Normalize a recorded ingredient name for a conservative class lookup."""
    normalized = re.sub(r"\([^)]*\)", " ", name.casefold())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    # Treat salt forms (e.g. "Esomeprazole Magnesium") as the base ingredient.
    return canonical_ingredient_key(normalized)


# Explicitly curated ingredient-to-class mapping.
# Extend only with reviewed mappings from a reliable drug reference.
THERAPEUTIC_CLASS_BY_INGREDIENT = {
    "omeprazole": "Proton pump inhibitors (PPIs)",
    "esomeprazole": "Proton pump inhibitors (PPIs)",
    "lansoprazole": "Proton pump inhibitors (PPIs)",
    "pantoprazole": "Proton pump inhibitors (PPIs)",
    "rabeprazole": "Proton pump inhibitors (PPIs)",
    "dexlansoprazole": "Proton pump inhibitors (PPIs)",
}


def build_same_class_warnings(
    medicines: list[Medicine],
) -> list[SameClassWarning]:
    """
    Identify selected medicines containing different known active
    ingredients from the same curated therapeutic class.
    """
    classes = defaultdict(
        lambda: defaultdict(
            lambda: {
                "ingredient_name": "",
                "medicine_ids": [],
                "medicine_names": [],
            }
        )
    )

    for medicine in medicines:
        for association in medicine.ingredients:
            ingredient_name = association.ingredient.name
            normalized = normalize_ingredient_name(ingredient_name)
            therapeutic_class = THERAPEUTIC_CLASS_BY_INGREDIENT.get(
                normalized
            )

            if therapeutic_class is None:
                continue

            entry = classes[therapeutic_class][normalized]
            entry["ingredient_name"] = ingredient_name

            if medicine.id not in entry["medicine_ids"]:
                entry["medicine_ids"].append(medicine.id)
                entry["medicine_names"].append(medicine.brand_name)

    warnings: list[SameClassWarning] = []

    for therapeutic_class, ingredients in classes.items():
        # A same-class warning requires at least two distinct active
        # ingredients represented across selected medicines.
        if len(ingredients) < 2:
            continue

        ingredient_names: list[str] = []
        medicine_ids: list[int] = []
        medicine_names: list[str] = []

        for entry in ingredients.values():
            ingredient_names.append(entry["ingredient_name"])

            for medicine_id in entry["medicine_ids"]:
                if medicine_id not in medicine_ids:
                    medicine_ids.append(medicine_id)

            for medicine_name in entry["medicine_names"]:
                if medicine_name not in medicine_names:
                    medicine_names.append(medicine_name)

        if len(medicine_ids) < 2:
            continue

        warnings.append(
            SameClassWarning(
                therapeutic_class=therapeutic_class,
                ingredient_names=ingredient_names,
                medicine_ids=medicine_ids,
                medicine_names=medicine_names,
                message=(
                    "Different active ingredients from the same therapeutic "
                    "class appear in the selected medicines. Ask a qualified "
                    "pharmacist or prescriber to review whether both are "
                    "intended. This finding does not establish that the "
                    "combination is unsafe."
                ),
            )
        )

    return warnings
