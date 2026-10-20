
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.medicine import (
    ActiveIngredient,
    Medicine,
    MedicineIngredient,
)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    with TestingSessionLocal() as session:
        yield session

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_medicines(db_session):
    medicine_a = Medicine(
        brand_name="Test Product A",
        generic_name="Test Compound A",
        source_display_name=(
            "test compound A 325 MG Oral Tablet [Test Product A]"
        ),
    )

    medicine_b = Medicine(
        brand_name="Test Product B",
        generic_name="Test Compound B",
        source_display_name=(
            "test compound B 50 MG Oral Capsule [Test Product B]"
        ),
    )

    medicine_c = Medicine(
        brand_name="Test Product C",
        generic_name="Test Compound C",
        source_display_name=(
            "test compound C 10 MG Oral Solution [Test Product C]"
        ),
    )

    shared = ActiveIngredient(name="test shared ingredient")
    unique_a = ActiveIngredient(name="test unique ingredient A")
    unique_c = ActiveIngredient(name="test unique ingredient C")

    db_session.add_all(
        [
            medicine_a,
            medicine_b,
            medicine_c,
            shared,
            unique_a,
            unique_c,
        ]
    )
    db_session.flush()

    db_session.add_all(
        [
            MedicineIngredient(
                medicine_id=medicine_a.id,
                ingredient_id=shared.id,
                amount=100,
                unit="mg",
            ),
            MedicineIngredient(
                medicine_id=medicine_a.id,
                ingredient_id=unique_a.id,
                amount=25,
                unit="mg",
            ),
            MedicineIngredient(
                medicine_id=medicine_b.id,
                ingredient_id=shared.id,
                amount=50,
                unit="mg",
            ),
            MedicineIngredient(
                medicine_id=medicine_c.id,
                ingredient_id=unique_c.id,
                amount=10,
                unit="mg",
            ),
        ]
    )

    db_session.commit()

    return {
        "a": medicine_a.id,
        "b": medicine_b.id,
        "c": medicine_c.id,
    }


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_medicine_search_endpoint(client, sample_medicines):
    response = client.get(
        "/api/v1/medicines",
        params={"q": "Test Product"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_medicine_search_by_strength(client, sample_medicines):
    response = client.get(
        "/api/v1/medicines",
        params={"q": "325 MG"},
    )

    assert response.status_code == 200

    results = response.json()

    assert len(results) == 1
    assert results[0]["brand_name"] == "Test Product A"
    assert "325 MG" in results[0]["source_display_name"]


def test_medicine_search_by_dosage_form(client, sample_medicines):
    response = client.get(
        "/api/v1/medicines",
        params={"q": "Oral Tablet"},
    )

    assert response.status_code == 200

    results = response.json()

    assert len(results) == 1
    assert results[0]["brand_name"] == "Test Product A"
    assert "Oral Tablet" in results[0]["source_display_name"]


def test_detects_shared_ingredient(client, sample_medicines):
    response = client.post(
        "/api/v1/medicines/check-overlap",
        json={
            "medicine_ids": [
                sample_medicines["a"],
                sample_medicines["b"],
            ]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["has_overlap"] is True
    assert len(data["overlapping_ingredients"]) == 1
    assert (
        data["overlapping_ingredients"][0]["name"]
        == "test shared ingredient"
    )
    assert data["result_status"] == "overlap_found"
    assert data["has_incomplete_data"] is False


def test_overlap_response_includes_medicine_display_names(
    client,
    sample_medicines,
):
    response = client.post(
        "/api/v1/medicines/check-overlap",
        json={
            "medicine_ids": [
                sample_medicines["a"],
                sample_medicines["b"],
            ]
        },
    )

    assert response.status_code == 200

    data = response.json()
    medicines = {
        medicine["id"]: medicine
        for medicine in data["medicines"]
    }

    assert (
        medicines[sample_medicines["a"]]["source_display_name"]
        == "test compound A 325 MG Oral Tablet [Test Product A]"
    )

    assert (
        medicines[sample_medicines["b"]]["source_display_name"]
        == "test compound B 50 MG Oral Capsule [Test Product B]"
    )


def test_overlap_response_includes_data_status(
    client,
    sample_medicines,
):
    medicine_ids = [
        sample_medicines["a"],
        sample_medicines["b"],
    ]

    response = client.post(
        "/api/v1/medicines/check-overlap",
        json={"medicine_ids": medicine_ids},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["result_status"] == "overlap_found"
    assert data["has_incomplete_data"] is False
    assert data["medicines_without_ingredient_data"] == []


def test_missing_ingredient_data_is_reported(
    client,
    db_session,
    sample_medicines,
):
    medicine_ids = [
        sample_medicines["a"],
        sample_medicines["b"],
    ]
    medicine_without_data_id = medicine_ids[0]

    db_session.execute(
        delete(MedicineIngredient).where(
            MedicineIngredient.medicine_id == medicine_without_data_id
        )
    )
    db_session.commit()

    response = client.post(
        "/api/v1/medicines/check-overlap",
        json={"medicine_ids": medicine_ids},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["has_incomplete_data"] is True
    assert medicine_without_data_id in (
        data["medicines_without_ingredient_data"]
    )

    # Medicine B still has the shared ingredient, but medicine A
    # has no ingredient records. Therefore, no overlap can be
    # established from the remaining data.
    assert data["has_overlap"] is False
    assert data["result_status"] == "incomplete_data"


def test_returns_no_overlap_for_distinct_ingredients(
    client,
    sample_medicines,
):
    response = client.post(
        "/api/v1/medicines/check-overlap",
        json={
            "medicine_ids": [
                sample_medicines["a"],
                sample_medicines["c"],
            ]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["has_overlap"] is False
    assert data["overlapping_ingredients"] == []
    assert data["result_status"] == "no_overlap_found"
    assert data["has_incomplete_data"] is False


def test_rejects_duplicate_medicine_ids(client):
    response = client.post(
        "/api/v1/medicines/check-overlap",
        json={"medicine_ids": [1, 1]},
    )

    assert response.status_code == 422


def test_rejects_too_few_medicine_ids(client):
    response = client.post(
        "/api/v1/medicines/check-overlap",
        json={"medicine_ids": [1]},
    )

    assert response.status_code == 422


def test_returns_404_for_unknown_medicine_ids(client):
    response = client.post(
        "/api/v1/medicines/check-overlap",
        json={"medicine_ids": [999998, 999999]},
    )

    assert response.status_code == 404


def test_ingredient_provenance_fields_are_saved(db_session):
    from datetime import datetime, timezone

    medicine = Medicine(
        brand_name="Provenance Test Medicine",
        generic_name="Test Compound",
    )
    ingredient = ActiveIngredient(name="provenance test ingredient")

    db_session.add_all([medicine, ingredient])
    db_session.flush()

    retrieved_at = datetime.now(timezone.utc)

    link = MedicineIngredient(
        medicine_id=medicine.id,
        ingredient_id=ingredient.id,
        amount=325,
        unit="mg",
        source_name="Test Source",
        source_record_id="TEST-123",
        source_url="https://example.com/test-record",
        retrieved_at=retrieved_at,
    )

    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)

    assert link.source_name == "Test Source"
    assert link.source_record_id == "TEST-123"
    assert link.source_url == "https://example.com/test-record"
    assert link.retrieved_at is not None
    assert (
        link.retrieved_at.replace(tzinfo=timezone.utc)
        == retrieved_at
    )


def test_ingredient_provenance_fields_can_be_empty(db_session):
    medicine = Medicine(
        brand_name="Optional Provenance Test",
        generic_name="Test Compound",
    )
    ingredient = ActiveIngredient(
        name="optional provenance ingredient"
    )

    db_session.add_all([medicine, ingredient])
    db_session.flush()

    link = MedicineIngredient(
        medicine_id=medicine.id,
        ingredient_id=ingredient.id,
    )

    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)

    assert link.source_name is None
    assert link.source_record_id is None
    assert link.source_url is None
    assert link.retrieved_at is None
