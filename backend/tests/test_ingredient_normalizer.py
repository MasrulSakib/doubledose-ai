import pytest

from app.models.medicine import ActiveIngredient, Medicine, MedicineIngredient
from app.services.ingredient_normalizer import canonical_ingredient_key
from app.services.overlap_service import check_ingredient_overlap


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("Amoxicillin", "Amoxicillin Trihydrate"),
        ("Atorvastatin", "Atorvastatin Calcium"),
        ("Tramadol Hydrochloride", "Tramadol Hydrochloride"),
        ("Tamsulosin  Hydrochloride", "Tamsulosin Hydrochloride"),
        ("Diclofenac Sodium", "Diclofenac Potassium"),
        ("Neomycin Sulfate", "Neomycin Sulphate"),
        ("Zinc Sulfate", "Zinc Sulfate Monohydrate"),
        ("Betamethasone", "Betamethasone Sodium Phosphate"),
    ],
)
def test_variants_share_a_key(first, second):
    assert canonical_ingredient_key(first) == canonical_ingredient_key(second)


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("Calcium", "Calcium Acetate"),
        ("Zinc", "Zinc Sulfate"),
        ("Zinc Sulfate", "Zinc Acetate"),
        ("Ferrous Fumarate", "Ferrous Sulfate"),
        ("Omeprazole", "Esomeprazole"),
        ("Cefixime Trihydrate", "Cefuroxime Axetil"),
    ],
)
def test_different_ingredients_keep_different_keys(first, second):
    assert canonical_ingredient_key(first) != canonical_ingredient_key(second)


def _add_medicine(db, brand, ingredient_names):
    medicine = Medicine(brand_name=brand)
    db.add(medicine)
    db.flush()

    for name in ingredient_names:
        ingredient = db.query(ActiveIngredient).filter_by(name=name).first()
        if ingredient is None:
            ingredient = ActiveIngredient(name=name)
            db.add(ingredient)
            db.flush()
        db.add(MedicineIngredient(medicine_id=medicine.id, ingredient_id=ingredient.id))

    db.flush()
    return medicine


def test_overlap_found_across_salt_variants(db_session):
    first = _add_medicine(db_session, "Brand A", ["Amoxicillin Trihydrate"])
    second = _add_medicine(db_session, "Brand B", ["Amoxicillin", "Clavulanic Acid"])

    result = check_ingredient_overlap(db_session, [first.id, second.id])

    assert result.result_status == "overlap_found"
    assert [item.name for item in result.overlapping_ingredients] == ["Amoxicillin"]
    assert result.overlapping_ingredients[0].medicine_ids == [first.id, second.id]


def test_different_zinc_salts_are_not_reported_as_overlap(db_session):
    first = _add_medicine(db_session, "Brand A", ["Zinc Sulfate"])
    second = _add_medicine(db_session, "Brand B", ["Zinc Acetate"])

    result = check_ingredient_overlap(db_session, [first.id, second.id])

    assert result.result_status == "no_overlap_found"


def test_medicines_are_returned_in_request_order(db_session):
    first = _add_medicine(db_session, "Brand A", ["Paracetamol"])
    second = _add_medicine(db_session, "Brand B", ["Omeprazole"])
    third = _add_medicine(db_session, "Brand C", ["Loratadine"])

    requested = [third.id, first.id, second.id]
    result = check_ingredient_overlap(db_session, requested)

    assert [medicine.id for medicine in result.medicines] == requested
