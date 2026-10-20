
from datetime import datetime, timezone

from sqlalchemy import select

import scripts.import_rxnorm as rxnorm_importer
from app.models.medicine import (
    ActiveIngredient,
    Medicine,
    MedicineIngredient,
)
from scripts.import_rxnorm import SOURCE_NAME, save_medicine


def test_import_saves_ingredient_provenance(db_session):
    medicine_data = {
        "rxcui": "TEST-RXCUI-100",
        "brand_name": "Test Brand",
        "display_name": "test ingredient 100 MG Oral Tablet [Test Brand]",
    }
    ingredients = [
        {"rxcui": "TEST-ING-100", "name": "test imported ingredient"}
    ]

    save_medicine(db_session, medicine_data, ingredients)
    db_session.commit()

    medicine = db_session.scalar(
        select(Medicine).where(
            Medicine.rxnorm_rxcui == "TEST-RXCUI-100"
        )
    )
    ingredient = db_session.scalar(
        select(ActiveIngredient).where(
            ActiveIngredient.rxnorm_rxcui == "TEST-ING-100"
        )
    )

    assert medicine is not None
    assert ingredient is not None

    link = db_session.scalar(
        select(MedicineIngredient).where(
            MedicineIngredient.medicine_id == medicine.id,
            MedicineIngredient.ingredient_id == ingredient.id,
        )
    )

    assert link is not None
    assert link.source_name == SOURCE_NAME
    assert link.source_record_id == "TEST-RXCUI-100"
    assert link.source_url is not None
    assert "/rxcui/TEST-RXCUI-100/related.json?tty=IN" in link.source_url
    assert link.retrieved_at is not None


def test_import_is_idempotent_for_existing_ingredient_link(db_session):
    medicine_data = {
        "rxcui": "TEST-RXCUI-200",
        "brand_name": "Test Brand Two",
        "display_name": "test ingredient 200 MG Oral Tablet [Test Brand Two]",
    }
    ingredients = [
        {"rxcui": "TEST-ING-200", "name": "another test ingredient"}
    ]

    save_medicine(db_session, medicine_data, ingredients)
    db_session.commit()

    save_medicine(db_session, medicine_data, ingredients)
    db_session.commit()

    medicine = db_session.scalar(
        select(Medicine).where(
            Medicine.rxnorm_rxcui == "TEST-RXCUI-200"
        )
    )
    links = db_session.scalars(
        select(MedicineIngredient).where(
            MedicineIngredient.medicine_id == medicine.id
        )
    ).all()

    assert len(links) == 1
    assert links[0].source_name == SOURCE_NAME
    assert links[0].retrieved_at is not None


def test_reimport_refreshes_provenance_and_preserves_amount(
    db_session,
    monkeypatch,
):
    medicine_data = {
        "rxcui": "TEST-RXCUI-300",
        "brand_name": "Test Brand Three",
        "display_name": "test ingredient 300 MG Oral Tablet [Test Brand Three]",
    }
    ingredients = [
        {"rxcui": "TEST-ING-300", "name": "refresh test ingredient"}
    ]

    first_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
    second_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    class FirstDateTime:
        @staticmethod
        def now(tz=None):
            return first_time

    class SecondDateTime:
        @staticmethod
        def now(tz=None):
            return second_time

    monkeypatch.setattr(rxnorm_importer, "datetime", FirstDateTime)

    save_medicine(db_session, medicine_data, ingredients)
    db_session.commit()

    medicine = db_session.scalar(
        select(Medicine).where(
            Medicine.rxnorm_rxcui == "TEST-RXCUI-300"
        )
    )

    link = db_session.scalar(
        select(MedicineIngredient).where(
            MedicineIngredient.medicine_id == medicine.id
        )
    )

    assert link is not None

    original_link_id = link.id

    # Simulate an amount/unit added by a separately verified data source.
    link.amount = 300
    link.unit = "mg"
    db_session.commit()

    monkeypatch.setattr(rxnorm_importer, "datetime", SecondDateTime)

    save_medicine(db_session, medicine_data, ingredients)
    db_session.commit()
    db_session.refresh(link)

    assert link.id == original_link_id
    assert link.retrieved_at is not None
    assert link.retrieved_at.replace(tzinfo=timezone.utc) == second_time
    assert link.amount == 300
    assert link.unit == "mg"

    links = db_session.scalars(
        select(MedicineIngredient).where(
            MedicineIngredient.medicine_id == medicine.id
        )
    ).all()

    assert len(links) == 1
