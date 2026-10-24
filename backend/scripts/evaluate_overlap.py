import argparse
import json
from collections import defaultdict
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.medicine import Medicine
from app.services.overlap_service import check_ingredient_overlap

BASE_DIR = Path(__file__).resolve().parents[1]


def resolve_medicine_id(db, brand_id: int) -> int | None:
    prefix = f"BDDrugBank ID: {brand_id} |"
    return db.scalar(
        select(Medicine.id).where(Medicine.source_display_name.startswith(prefix))
    )


def to_moieties(names: list[str], expected: set[str]) -> set[str]:
    """Map predicted ingredient names onto the labelled base moieties."""
    found = set()
    for name in names:
        lowered = " ".join(name.casefold().split())
        match = next((m for m in expected if lowered.startswith(m)), None)
        found.add(match or lowered)
    return found


def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def prf(tp: int, fp: int, fn: int) -> dict:
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(safe_div(2 * precision * recall, precision + recall), 3),
    }


def evaluate(cases_path: Path) -> dict:
    data = json.loads(cases_path.read_text(encoding="utf-8"))
    cases = data["cases"]
    rows = []
    unresolved = []

    with SessionLocal() as db:
        for case in cases:
            ids = [resolve_medicine_id(db, b) for b in case["brand_ids"]]
            if any(i is None for i in ids):
                unresolved.append(case["id"])
                continue

            result = check_ingredient_overlap(db, ids)
            expected = set(case["expected_overlap"])
            predicted = to_moieties(
                [item.name for item in result.overlapping_ingredients],
                expected,
            )
            rows.append(
                {
                    "id": case["id"],
                    "category": case["category"],
                    "note": case["note"],
                    "expected_overlap": sorted(expected),
                    "predicted_overlap": sorted(predicted),
                    "expected_status": case["expected_status"],
                    "predicted_status": result.result_status,
                    "has_incomplete_data": result.has_incomplete_data,
                    "returned_medicine_ids_in_request_order": [
                        m.id for m in result.medicines
                    ] == ids,
                }
            )

    # Combination level: did the tool say "overlap" when (and only when) it exists?
    tp = sum(1 for r in rows if r["expected_overlap"] and r["predicted_overlap"])
    fp = sum(1 for r in rows if not r["expected_overlap"] and r["predicted_overlap"])
    fn = sum(1 for r in rows if r["expected_overlap"] and not r["predicted_overlap"])
    tn = sum(1 for r in rows if not r["expected_overlap"] and not r["predicted_overlap"])

    # Ingredient level: each (case, moiety) pair is one decision.
    itp = ifp = ifn = 0
    for r in rows:
        exp, pred = set(r["expected_overlap"]), set(r["predicted_overlap"])
        itp += len(exp & pred)
        ifp += len(pred - exp)
        ifn += len(exp - pred)

    by_category = defaultdict(lambda: {"cases": 0, "status_correct": 0})
    for r in rows:
        bucket = by_category[r["category"]]
        bucket["cases"] += 1
        bucket["status_correct"] += r["expected_status"] == r["predicted_status"]

    return {
        "cases_file": str(cases_path.name),
        "cases_total": len(cases),
        "cases_evaluated": len(rows),
        "cases_unresolved_brand_ids": unresolved,
        "combination_level": {**prf(tp, fp, fn), "tn": tn},
        "ingredient_level": prf(itp, ifp, ifn),
        "status_accuracy": round(
            safe_div(sum(r["expected_status"] == r["predicted_status"] for r in rows), len(rows)),
            3,
        ),
        "request_order_preserved": sum(
            r["returned_medicine_ids_in_request_order"] for r in rows
        ),
        "by_category": dict(by_category),
        "failures": [
            r
            for r in rows
            if r["expected_overlap"] != r["predicted_overlap"]
            or r["expected_status"] != r["predicted_status"]
        ],
        "label_caveat": data["description"],
    }


def to_markdown(report: dict) -> str:
    c, i = report["combination_level"], report["ingredient_level"]
    lines = [
        "# Overlap assessment",
        "",
        f"Cases evaluated: {report['cases_evaluated']} of {report['cases_total']}"
        + (
            f" (unresolved brand ids in: {', '.join(report['cases_unresolved_brand_ids'])})"
            if report["cases_unresolved_brand_ids"]
            else ""
        ),
        "",
        "| Level | TP | FP | FN | Precision | Recall | F1 |",
        "|---|---|---|---|---|---|---|",
        f"| Combination (overlap yes/no) | {c['tp']} | {c['fp']} | {c['fn']} | {c['precision']} | {c['recall']} | {c['f1']} |",
        f"| Ingredient (moiety shared) | {i['tp']} | {i['fp']} | {i['fn']} | {i['precision']} | {i['recall']} | {i['f1']} |",
        "",
        f"Result-status accuracy (overlap_found / no_overlap_found / incomplete_data): {report['status_accuracy']}",
        f"Medicines returned in request order: {report['request_order_preserved']} of {report['cases_evaluated']} cases",
        "",
        "| Category | Cases | Status correct |",
        "|---|---|---|",
    ]
    for name, b in report["by_category"].items():
        lines.append(f"| {name} | {b['cases']} | {b['status_correct']} |")
    lines += ["", "## Failures", ""]
    if not report["failures"]:
        lines.append("None.")
    for r in report["failures"]:
        lines.append(
            f"- {r['id']} ({r['note']}): expected {r['expected_overlap'] or 'none'}"
            f" / {r['expected_status']}, got {r['predicted_overlap'] or 'none'}"
            f" / {r['predicted_status']}"
        )
    lines += ["", f"Label caveat: {report['label_caveat']}", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate overlap detection.")
    parser.add_argument("--cases", default=str(BASE_DIR / "evaluation" / "overlap_cases.json"))
    parser.add_argument("--out-dir", default=str(BASE_DIR / "evaluation" / "results"))
    args = parser.parse_args()

    report = evaluate(Path(args.cases))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "overlap_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "overlap_report.md").write_text(to_markdown(report), encoding="utf-8")
    print(to_markdown(report))


if __name__ == "__main__":
    main()
