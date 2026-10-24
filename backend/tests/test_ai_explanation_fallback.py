import asyncio

import pytest
from groq import GroqError

from app.core.config import settings
from app.schemas.ai_explanation import (
    AIExplanationMedicineInput,
    AIExplanationRequest,
    OverlapIngredientInput,
)
from app.services import ai_explanation_service as service


def _payload():
    return AIExplanationRequest(
        result_status="overlap_found",
        medicine_names=["Calmora", "Rhinoclear"],
        medicines=[
            AIExplanationMedicineInput(name="Calmora"),
            AIExplanationMedicineInput(name="Rhinoclear"),
        ],
        overlapping_ingredients=[
            OverlapIngredientInput(name="Paracetamol", medicine_names=["Calmora", "Rhinoclear"])
        ],
    )


def _report(extra=""):
    return (
        '{"explanation": "' + (
            "### 1. Summary\\nParacetamol appears in Calmora and Rhinoclear.\\n"
            "### 2. Medicine comparison\\n| Medicine | Ingredients |\\n|---|---|\\n"
            "| Calmora | Paracetamol |\\n| Rhinoclear | Paracetamol |\\n"
            "### 3. What the result means\\nThis is an ingredient overlap, not a confirmed interaction. " + extra +
            "\\n### 4. Limitations and next steps\\nAsk a pharmacist to review the packages. " + "Records may be incomplete. " * 12 +
            "\\n### 5. Available data sources\\nDatabase records only."
        ) + '", "limitations": ["Records may be incomplete."], "disclaimer": "x"}'
    )


class _FakeClient:
    def __init__(self, behaviour):
        self.behaviour = behaviour
        self.calls = 0
        self.chat = self
        self.completions = self

    async def create(self, **kwargs):
        self.calls += 1
        result = self.behaviour()
        if isinstance(result, Exception):
            raise result

        class _Message:
            content = result

        class _Choice:
            message = _Message()

        class _Response:
            choices = [_Choice()]

        return _Response()

    async def close(self):
        return None


@pytest.fixture
def run(monkeypatch):
    async def no_references(_payload):
        return []

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(service, "_retrieve_references", no_references)
    monkeypatch.setattr(service.asyncio, "sleep", no_sleep)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")

    def _run(behaviour):
        client = _FakeClient(behaviour)
        monkeypatch.setattr(service, "AsyncGroq", lambda **kwargs: client)
        result = asyncio.run(service.generate_overlap_explanation(_payload()))
        return result, client

    return _run


def test_valid_grounded_report_is_returned_as_is(run):
    result, client = run(lambda: _report())

    assert client.calls == 1
    assert "Groq did not return" not in " ".join(result.limitations)
    assert result.disclaimer == service.DISCLAIMER


def test_groq_error_falls_back_to_data_only_report(run):
    result, client = run(lambda: GroqError("boom"))

    assert client.calls == 2
    assert "Paracetamol" in result.explanation
    assert "Calmora" in result.explanation and "Rhinoclear" in result.explanation
    assert "Groq did not return" in result.limitations[0]


def test_invalid_json_falls_back(run):
    result, _ = run(lambda: "not json at all")

    assert "Groq did not return" in result.limitations[0]


def test_medicine_change_advice_is_rejected(run):
    result, _ = run(lambda: _report("You should stop taking Calmora."))

    assert "Groq did not return" in result.limitations[0]


def test_negated_advice_is_allowed(run):
    result, client = run(lambda: _report("Do not stop taking any medicine because of this report."))

    assert client.calls == 1
    assert "Groq did not return" not in result.limitations[0]


def test_report_missing_database_overlap_is_rejected(run):
    text = _report().replace("Paracetamol", "the active ingredient")

    result, _ = run(lambda: text)

    assert "Groq did not return" in result.limitations[0]


def test_missing_api_key_returns_fallback_instead_of_error(monkeypatch):
    async def no_references(_payload):
        return []

    monkeypatch.setattr(service, "_retrieve_references", no_references)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")

    result = asyncio.run(service.generate_overlap_explanation(_payload()))

    assert "Paracetamol" in result.explanation
    assert result.disclaimer == service.DISCLAIMER
