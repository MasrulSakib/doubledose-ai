
import asyncio
import logging
import re
import time
from typing import Any
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

OPENFDA_LABEL_URL = "https://api.fda.gov/drug/label.json"
REQUEST_TIMEOUT = 8.0
CACHE_TTL_SECONDS = 6 * 60 * 60
MAX_FIELD_LENGTH = 1800

# Handle common ingredient naming differences between Bangladesh records
# and US product labels.
INGREDIENT_ALIASES = {
    "paracetamol": "acetaminophen",
    "acetaminophen": "acetaminophen",
    "omeprazole": "omeprazole",
    "esomeprazole": "esomeprazole",
}

# In-memory cache: canonical ingredient -> (expiry time, reference).
_reference_cache: dict[str, tuple[float, dict[str, Any]]] = {}


def _normalize_ingredient(value: str) -> str:
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(r"\s+", " ", value).strip().casefold()
    return INGREDIENT_ALIASES.get(value, value)


def _text(value: Any, max_length: int = MAX_FIELD_LENGTH) -> str | None:
    """Convert an API field into bounded plain text."""
    if isinstance(value, list):
        parts = [str(item).strip() for item in value if item]
        value = "\n".join(parts)
    elif value is not None:
        value = str(value).strip()

    if not value:
        return None

    if len(value) > max_length:
        value = value[:max_length].rsplit(" ", 1)[0] + "…"

    return value


def _matches_single_ingredient(
    record: dict[str, Any],
    canonical_ingredient: str,
) -> bool:
    """Avoid using a combination-drug label as a single-ingredient label."""
    openfda = record.get("openfda") or {}
    generic_names = openfda.get("generic_name") or []

    if isinstance(generic_names, str):
        generic_names = [generic_names]

    if not generic_names:
        return False

    # Prefer records that identify only the requested ingredient.
    for value in generic_names:
        normalized = _normalize_ingredient(str(value))

        if normalized == canonical_ingredient:
            return True

    # If the API returned a strength/form decorated generic name, reject
    # obvious combination products rather than risking a false match.
    for value in generic_names:
        normalized = str(value).casefold()

        if (
            canonical_ingredient in normalized
            and not any(separator in normalized for separator in (" / ", " + ", " and "))
        ):
            return True

    return False


async def _fetch_one_ingredient(
    client: httpx.AsyncClient,
    requested_ingredient: str,
) -> dict[str, Any] | None:
    canonical = _normalize_ingredient(requested_ingredient)

    if not canonical:
        return None

    cached = _reference_cache.get(canonical)
    if cached and cached[0] > time.monotonic():
        return {
            **cached[1],
            "requested_ingredient": requested_ingredient,
        }

    params = {
        "search": f'openfda.generic_name:"{canonical.upper()}"',
        "limit": 10,
    }

    source_url = f"{OPENFDA_LABEL_URL}?{urlencode(params)}"

    try:
        response = await client.get(OPENFDA_LABEL_URL, params=params)

        if response.status_code == 404:
            return None

        response.raise_for_status()
        body = response.json()
        records = body.get("results", [])

    except (httpx.HTTPError, ValueError) as exc:
        logger.warning(
            "openFDA lookup failed for ingredient %r: %s",
            requested_ingredient,
            type(exc).__name__,
        )
        return None

    candidates = [
        record
        for record in records
        if _matches_single_ingredient(record, canonical)
    ]

    if not candidates:
        return None

    # Prefer a record containing both adverse-reaction and warning sections.
    candidates.sort(
        key=lambda record: sum(
            bool(record.get(field))
            for field in (
                "adverse_reactions",
                "warnings",
                "dosage_and_administration",
                "contraindications",
            )
        ),
        reverse=True,
    )

    record = candidates[0]
    product = record.get("openfda") or {}

    reference = {
        "requested_ingredient": requested_ingredient,
        "matched_ingredient": canonical,
        "source_name": "openFDA drug labeling",
        "source_url": source_url,
        "source_country": "United States",
        "reference_scope": (
            "Ingredient-level US product-label reference. The selected "
            "Bangladeshi brand, manufacturer, formulation, and strength "
            "have not been verified against this label."
        ),
        "label_effective_date": _text(record.get("effective_time"), 30),
        "label_product_brand": _text(product.get("brand_name"), 200),
        "label_product_generic": _text(product.get("generic_name"), 300),
        "label_manufacturer": _text(product.get("manufacturer_name"), 300),
        "label_dosage_form": _text(product.get("dosage_form"), 200),
        "adverse_reactions": _text(record.get("adverse_reactions")),
        "warnings": _text(record.get("warnings")),
        "contraindications": _text(record.get("contraindications")),
        "dosage_and_administration": _text(
            record.get("dosage_and_administration")
        ),
    }

    _reference_cache[canonical] = (
        time.monotonic() + CACHE_TTL_SECONDS,
        reference,
    )

    return reference


async def fetch_medicine_references(
    ingredients: list[str],
) -> list[dict[str, Any]]:
    """
    Fetch supplementary US drug-label references for unique ingredients.

    Failure to retrieve a reference never blocks the medicine comparison.
    These records must not be presented as verified local product leaflets.
    """
    unique_ingredients: dict[str, str] = {}

    for ingredient in ingredients:
        canonical = _normalize_ingredient(ingredient)

        if canonical and canonical not in unique_ingredients:
            unique_ingredients[canonical] = ingredient

    if not unique_ingredients:
        return []

    limits = httpx.Limits(
        max_connections=4,
        max_keepalive_connections=2,
    )

    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
        limits=limits,
        headers={"User-Agent": "DoubleDoseAI/1.0"},
    ) as client:
        tasks = [
            _fetch_one_ingredient(client, ingredient)
            for ingredient in unique_ingredients.values()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

    references: list[dict[str, Any]] = []

    for result in results:
        if isinstance(result, Exception):
            logger.warning(
                "Medicine reference lookup failed: %s",
                type(result).__name__,
            )
            continue

        if result:
            references.append(result)

    return references
