import pytest

from app.models.medicine import Medicine
from app.services.ocr_matching_service import match_medicines_from_ocr
from app.services.tfidf_matching_service import match_medicines_tfidf


@pytest.fixture
def catalogue(db_session):
    rows = [
        ("Calmora", "Paracetamol", "Tablet", "500 mg"),
        ("Omeprol", "Omeprazole", "Capsule", "20 mg"),
        ("Loratex", "Loratadine", "Tablet", "10 mg"),
    ]
    for index, (brand, generic, form, strength) in enumerate(rows, start=1):
        db_session.add(
            Medicine(
                brand_name=brand,
                generic_name=generic,
                dosage_form=form,
                source_display_name=(
                    f"BDDrugBank ID: {index} | Generic: {generic} | "
                    f"Strength: {strength} | Slug: {brand.lower()}"
                ),
            )
        )
    db_session.commit()


@pytest.mark.parametrize("matcher", [match_medicines_from_ocr, match_medicines_tfidf])
def test_every_ocr_candidate_requires_confirmation(db_session, catalogue, matcher):
    results = matcher(db=db_session, extracted_text="CALMORA tablet 500 mg", limit=3)

    assert results
    assert all(item["needs_confirmation"] is True for item in results)
    assert all(0 <= item["match_score"] <= 100 for item in results)


def test_rapidfuzz_ranks_the_printed_brand_first(db_session, catalogue):
    results = match_medicines_from_ocr(
        db=db_session, extracted_text="Calrnora tablet 500 mg paracetamol", limit=3
    )

    assert results[0]["brand_name"] == "Calmora"


def test_unreadable_text_returns_no_candidates(db_session, catalogue):
    assert match_medicines_from_ocr(db=db_session, extracted_text="zzzz qqqq", limit=3) == []
    assert match_medicines_from_ocr(db=db_session, extracted_text="   ", limit=3) == []
