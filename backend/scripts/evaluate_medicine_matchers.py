import argparse
import csv
import json
import math
import random
import re
import time
from collections import defaultdict
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.medicine import Medicine
from app.services.ocr_matching_service import match_medicines_from_ocr
from app.services.tfidf_matching_service import match_medicines_tfidf

BASE_DIR = Path(__file__).resolve().parents[1]
MIN_BRAND_LENGTH = 4  # shortest brand the RapidFuzz matcher will consider
TOP_K = 3
SCORE_BINS = [(0, 45), (45, 65), (65, 80), (80, 101)]

MATCHERS = {
    "rapidfuzz": match_medicines_from_ocr,
    "tfidf": match_medicines_tfidf,
}

# Planned matcher that is not implemented in this repository yet.
BLOCKED_MATCHERS = {
    "sentence_transformers_faiss": (
        "not implemented in the repo; the Hugging Face model host was also "
        "unreachable from the assessment sandbox"
    ),
}

# Small initial set typed by hand (clean text, not real OCR output).
LEGACY_CASES = [
    ("A-Cof Syrup Dextromethorphan Pseudoephedrine Triprolidine", "A-Cof"),
    ("E-Cof syrup Pseudoephedrine Guaiphenasine Triprolidine", "E-Cof"),
    ("A-Cold syrup Bromhexine Hydrochloride", "A-Cold"),
    ("A-Clox capsule 500 mg Cloxacillin Sodium", "A-Clox"),
    ("Syrup Zinc Zinc Sulfate Monohydrate", "Syrup Zinc"),
]

OCR_CONFUSIONS = {
    "o": "0", "0": "o", "l": "1", "1": "l", "i": "l", "s": "5", "5": "s",
    "b": "6", "e": "c", "c": "e", "a": "o", "m": "rn", "n": "h", "u": "v",
    "g": "9", "t": "f",
}
NOISE_LEVELS = {"low": 0.03, "medium": 0.08, "high": 0.15}
JUNK_LINES = [
    "Store below 30 C. Keep out of reach of children.",
    "Batch No. A2317 Exp. 08/2028",
    "Manufactured by",
    "For oral use only",
]


# ---------------------------------------------------------------- helpers

def wilson(successes: int, total: int, z: float = 1.96) -> list[float]:
    if total == 0:
        return [0.0, 0.0]
    p = successes / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return [round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3)]


def strength_of(medicine: Medicine) -> str:
    match = re.search(r"Strength: (.*?) \|", medicine.source_display_name or "")
    value = match.group(1) if match else ""
    return "" if value == "Unknown" else value


def corrupt(text: str, rate: float, rng: random.Random) -> str:
    out = []
    for char in text:
        roll = rng.random()
        if char.isspace():
            out.append(char)
        elif roll < rate * 0.5 and char.lower() in OCR_CONFUSIONS:
            out.append(OCR_CONFUSIONS[char.lower()])
        elif roll < rate * 0.75:
            continue
        elif roll < rate:
            out.append(char + rng.choice("il.,'"))
        else:
            out.append(char)
    return "".join(out)


# ------------------------------------------------------------ case builders

def legacy_cases() -> list[dict]:
    return [
        {"id": f"legacy-{i + 1}", "source": "legacy_manual", "group": "clean",
         "text": text, "expected_brand": brand}
        for i, (text, brand) in enumerate(LEGACY_CASES)
    ]


def csv_cases(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return [
            {"id": row["case_id"], "source": row.get("source") or "csv",
             "group": row.get("group") or "all", "text": row["text"],
             "expected_brand": row["expected_brand"]}
            for row in csv.DictReader(file)
        ]


def sample_medicines(db: Session, count: int, seed: int) -> tuple[list[Medicine], dict]:
    medicines = db.query(Medicine).filter(Medicine.brand_name.isnot(None)).all()
    eligible, seen = [], set()
    for medicine in medicines:
        brand = medicine.brand_name.strip()
        compact = re.sub(r"[^a-z0-9]", "", brand.lower())
        if len(compact) < MIN_BRAND_LENGTH or brand.casefold() in seen:
            continue
        seen.add(brand.casefold())
        eligible.append(medicine)
    all_brands = {m.brand_name.strip().casefold() for m in medicines}
    short = sum(
        1 for b in all_brands if len(re.sub(r"[^a-z0-9]", "", b)) < MIN_BRAND_LENGTH
    )
    info = {
        "distinct_brand_names": len(all_brands),
        "brands_shorter_than_matcher_minimum": short,
        "share_unmatchable_by_length": round(short / len(all_brands), 4),
    }
    rng = random.Random(seed)
    return rng.sample(eligible, count), info


def label_text(medicine: Medicine, variant: str, rng: random.Random) -> str:
    form = (medicine.dosage_form or "").strip()
    parts = [medicine.brand_name.strip(), form, strength_of(medicine)]
    if variant == "brand_generic":
        parts.append((medicine.generic_name or "").replace("+", " "))
        parts += rng.sample(JUNK_LINES, 2)
    return " ".join(p for p in parts if p)


def synthetic_cases(db: Session, per_cell: int, seed: int) -> tuple[list[dict], dict]:
    medicines, info = sample_medicines(db, per_cell, seed)
    rng = random.Random(seed + 1)
    cases = []
    for medicine in medicines:
        for variant in ("brand_only", "brand_generic"):
            clean = label_text(medicine, variant, rng)
            for level, rate in NOISE_LEVELS.items():
                cases.append({
                    "id": f"syn-{medicine.id}-{variant}-{level}",
                    "source": "synthetic_text",
                    "group": f"{variant}/{level}",
                    "text": corrupt(clean, rate, rng),
                    "expected_brand": medicine.brand_name.strip(),
                })
    return cases, info


# ----------------------------------------------------------- image pipeline

def ocr_image(image) -> tuple[str, bool]:
    """Same flow as POST /ocr/extract: label crops first, full image as fallback."""
    from app.api.ocr import _rank_extracted_text
    from app.services.detection_service import detect_label_crops
    from app.services.ocr_service import extract_text_from_image

    candidates = [(extract_text_from_image(c).strip(), True) for c in detect_label_crops(image) or []]
    candidates.append((extract_text_from_image(image).strip(), False))
    candidates = [c for c in candidates if c[0]]
    if not candidates:
        return "", False
    text, used = max(candidates, key=lambda c: _rank_extracted_text(c[0]))
    return text, used


def render_label(medicine: Medicine, degrade: str, rng: random.Random):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    font_dir = "/usr/share/fonts/truetype/dejavu/"
    bold = ImageFont.truetype(font_dir + "DejaVuSans-Bold.ttf", 72)
    regular = ImageFont.truetype(font_dir + "DejaVuSans.ttf", 34)
    image = Image.new("RGB", (1000, 520), (236, 240, 236))
    draw = ImageDraw.Draw(image)
    draw.text((50, 50), medicine.brand_name.strip(), font=bold, fill=(20, 50, 110))
    draw.text((50, 170), f"{medicine.dosage_form or ''} {strength_of(medicine)}".strip(), font=regular, fill=(30, 30, 30))
    draw.text((50, 240), (medicine.generic_name or "")[:48], font=regular, fill=(30, 30, 30))
    draw.text((50, 420), "Keep out of reach of children", font=regular, fill=(90, 90, 90))

    if degrade == "blur_rotate":
        image = image.rotate(rng.uniform(-6, 6), expand=True, fillcolor=(236, 240, 236))
        image = image.filter(ImageFilter.GaussianBlur(1.6))
    elif degrade == "noisy_low_contrast":
        array = np.asarray(image).astype("float32")
        array = 128 + (array - 128) * 0.45
        array += np.random.default_rng(rng.randrange(10**6)).normal(0, 14, array.shape)
        image = Image.fromarray(np.clip(array, 0, 255).astype("uint8"))
        image = image.filter(ImageFilter.GaussianBlur(1.0))
    return image


def image_cases(db: Session, count: int, seed: int) -> tuple[list[dict], dict]:
    medicines, info = sample_medicines(db, count, seed + 2)
    rng = random.Random(seed + 3)
    cases = []
    for medicine in medicines:
        for degrade in ("clean", "blur_rotate", "noisy_low_contrast"):
            text, _ = ocr_image(render_label(medicine, degrade, rng))
            cases.append({
                "id": f"img-{medicine.id}-{degrade}",
                "source": "synthetic_rendered_image",
                "group": degrade,
                "text": text,
                "expected_brand": medicine.brand_name.strip(),
            })
    return cases, info


def real_image_cases(images_dir: Path) -> list[dict]:
    from PIL import Image, ImageOps

    cases = []
    with (images_dir / "labels.csv").open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            image = ImageOps.exif_transpose(Image.open(images_dir / row["image_file"])).convert("RGB")
            text, used = ocr_image(image)
            cases.append({
                "id": row["image_file"], "source": "real_photo",
                "group": "detector" if used else "full_image_fallback",
                "text": text, "expected_brand": row["expected_brand"],
            })
    return cases


# ---------------------------------------------------------------- scoring

def run_matcher(db: Session, name: str, cases: list[dict]) -> list[dict]:
    function = MATCHERS[name]
    rows = []
    for case in cases:
        started = time.perf_counter()
        results = function(db=db, extracted_text=case["text"], limit=TOP_K) if case["text"].strip() else []
        elapsed = time.perf_counter() - started
        brands = [r["brand_name"].casefold() for r in results]
        expected = case["expected_brand"].casefold()
        rank = next((i for i, b in enumerate(brands[:TOP_K], start=1) if b == expected), None)
        rows.append({
            "case": case["id"], "group": case["group"], "rank": rank,
            "empty": not results,
            "top1_score": results[0]["match_score"] if results else None,
            "all_need_confirmation": all(r.get("needs_confirmation") for r in results),
            "seconds": elapsed,
        })
    return rows


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    top1 = sum(1 for r in rows if r["rank"] == 1)
    top3 = sum(1 for r in rows if r["rank"] is not None)
    return {
        "cases": n,
        "top1_accuracy": round(top1 / n, 3) if n else None,
        "top1_ci95": wilson(top1, n),
        "top3_accuracy": round(top3 / n, 3) if n else None,
        "top3_ci95": wilson(top3, n),
        "mrr_at_3": round(sum(1 / r["rank"] for r in rows if r["rank"]) / n, 3) if n else None,
        "no_candidate_rate": round(sum(r["empty"] for r in rows) / n, 3) if n else None,
        "mean_seconds_per_query": round(sum(r["seconds"] for r in rows) / n, 2) if n else None,
    }


def calibration(rows: list[dict]) -> list[dict]:
    table = []
    for low, high in SCORE_BINS:
        in_bin = [r for r in rows if r["top1_score"] is not None and low <= r["top1_score"] < high]
        correct = sum(1 for r in in_bin if r["rank"] == 1)
        table.append({
            "top1_score_range": f"{low}-{min(high, 100)}",
            "cases": len(in_bin),
            "top1_correct": correct,
            "top1_precision": round(correct / len(in_bin), 3) if in_bin else None,
        })
    return table


def evaluate(db: Session, cases: list[dict], matcher_names: list[str]) -> dict:
    report = {}
    for source in sorted({c["source"] for c in cases}):
        subset = [c for c in cases if c["source"] == source]
        report[source] = {}
        for name in matcher_names:
            rows = run_matcher(db, name, subset)
            by_group = defaultdict(list)
            for row in rows:
                by_group[row["group"]].append(row)
            report[source][name] = {
                "overall": summarize(rows),
                "by_group": {g: summarize(r) for g, r in sorted(by_group.items())},
                "top1_score_calibration": calibration(rows),
                "every_result_requires_confirmation": all(r["all_need_confirmation"] for r in rows),
            }
            print(f"{source:26s} {name:10s} {json.dumps(report[source][name]['overall'])}", flush=True)
    return report


def to_markdown(report: dict, meta: dict) -> str:
    lines = ["# Matcher benchmark", "", f"Seed: {meta['seed']}. Sources run: {', '.join(report) or 'none'}.", ""]
    notes = {
        "legacy_manual": "5 hand-typed clean cases. Too small to generalise.",
        "synthetic_text": "Noisy text generated from real database records. A stress test, not real OCR.",
        "synthetic_rendered_image": "Labels rendered with a clean font, degraded, then read by the real Tesseract pipeline. Easier than real photos.",
        "real_photo": "Real labelled photos.",
    }
    for source, matchers in report.items():
        lines += [f"## {source}", "", notes.get(source, ""), "",
                  "| Matcher | Cases | Top-1 (95% CI) | Top-3 (95% CI) | MRR@3 | No candidate | s/query |",
                  "|---|---|---|---|---|---|---|"]
        for name, data in matchers.items():
            o = data["overall"]
            lines.append(f"| {name} | {o['cases']} | {o['top1_accuracy']} {o['top1_ci95']} | {o['top3_accuracy']} {o['top3_ci95']} | {o['mrr_at_3']} | {o['no_candidate_rate']} | {o['mean_seconds_per_query']} |")
        lines += ["", "| Group | " + " | ".join(f"{n} top-1 / top-3" for n in matchers) + " |",
                  "|---|" + "---|" * len(matchers)]
        groups = next(iter(matchers.values()))["by_group"]
        for group in groups:
            cells = [f"{m['by_group'][group]['top1_accuracy']} / {m['by_group'][group]['top3_accuracy']} (n={m['by_group'][group]['cases']})" for m in matchers.values()]
            lines.append(f"| {group} | " + " | ".join(cells) + " |")
        lines += ["", "Top-1 precision by top-1 score (is the score a usable confidence?):", ""]
        for name, data in matchers.items():
            row = ", ".join(f"{b['top1_score_range']}: {b['top1_precision']} (n={b['cases']})" for b in data["top1_score_calibration"])
            lines.append(f"- {name}: {row}")
        lines.append("")
    if meta.get("database"):
        lines += ["## Database facts", "", json.dumps(meta["database"], indent=2), ""]
    lines += ["## Not measured", ""]
    lines += [f"- {name}: {reason}" for name, reason in BLOCKED_MATCHERS.items()]
    lines += ["- Real photos: " + ("run" if "real_photo" in report else "none supplied (pass --images-dir)."),
              "- YOLO detector / mAP: no trained weights or detector-labelled images were available; the full-image OCR fallback is what ran."]
    return "\n".join(lines) + "\n"


def log_to_mlflow(report: dict, meta: dict, out_dir: Path) -> str:
    try:
        import mlflow
    except ImportError:
        return "skipped (mlflow not installed)"

    try:
        mlflow.set_tracking_uri(meta["mlflow_uri"])
        mlflow.set_experiment("doubledose-medicine-matching")
        with mlflow.start_run(run_name=meta["run_name"]):
            mlflow.log_params({"seed": meta["seed"], "top_k": TOP_K, "sources": ",".join(report)})
            for source, matchers in report.items():
                for name, data in matchers.items():
                    for key, value in data["overall"].items():
                        if isinstance(value, (int, float)):
                            mlflow.log_metric(f"{source}.{name}.{key}", value)
            mlflow.log_artifact(str(out_dir / "matcher_report.json"))
            mlflow.log_artifact(str(out_dir / "matcher_report.md"))
    except Exception as exc:  # tracking must never lose the written reports
        return f"failed ({type(exc).__name__}: {exc})"
    return f"logged to {meta['mlflow_uri']}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark medicine matchers.")
    parser.add_argument("--cases", help="CSV with case_id,text,expected_brand[,source,group]")
    parser.add_argument("--synthetic", type=int, default=0, metavar="N", help="N products x 6 noise variants")
    parser.add_argument("--synthetic-images", type=int, default=0, metavar="N", help="N products x 3 image degradations")
    parser.add_argument("--images-dir", help="folder of real photos with labels.csv")
    parser.add_argument("--matchers", default=",".join(MATCHERS))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", default=str(BASE_DIR / "evaluation" / "results"))
    parser.add_argument("--mlflow-uri", default="sqlite:///mlflow.db")
    parser.add_argument("--no-mlflow", action="store_true")
    args = parser.parse_args()

    matcher_names = [m for m in args.matchers.split(",") if m]
    meta = {"seed": args.seed, "mlflow_uri": args.mlflow_uri, "run_name": "matcher-benchmark"}
    cases = legacy_cases()

    with SessionLocal() as db:
        if args.cases:
            cases += csv_cases(Path(args.cases))
        if args.synthetic:
            new, meta["database"] = synthetic_cases(db, args.synthetic, args.seed)
            cases += new
        if args.synthetic_images:
            new, meta["database"] = image_cases(db, args.synthetic_images, args.seed)
            cases += new
        if args.images_dir:
            cases += real_image_cases(Path(args.images_dir))

        report = evaluate(db, cases, matcher_names)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "matcher_report.json").write_text(json.dumps({"meta": meta, "results": report}, indent=2), encoding="utf-8")
    (out_dir / "matcher_report.md").write_text(to_markdown(report, meta), encoding="utf-8")
    print(f"\nReports written to {out_dir}")
    if not args.no_mlflow:
        print("MLflow:", log_to_mlflow(report, meta, out_dir))


if __name__ == "__main__":
    main()
