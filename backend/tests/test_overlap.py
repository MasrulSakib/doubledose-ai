
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
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
    )
    medicine_b = Medicine(
        brand_name="Test Product B",
        generic_name="Test Compound B",
    )
    medicine_c = Medicine(
        brand_name="Test Product C",
        generic_name="Test Compound C",
    )

    shared = ActiveIngredient(name="test shared ingredient")
    unique_a = ActiveIngredient(name="test unique ingredient A")
    unique_c = ActiveIngredient(name="test unique ingredient C")

    db_session.add_all([
        medicine_a,
        medicine_b,
        medicine_c,
        shared,
        unique_a,
        unique_c,
    ])
    db_session.flush()

    db_session.add_all([
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
    ])

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


def test_detects_shared_ingredient(
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
    assert data["has_overlap"] is True
    assert len(data["overlapping_ingredients"]) == 1
    assert (
        data["overlapping_ingredients"][0]["name"]
        == "test shared ingredient"
    )


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
