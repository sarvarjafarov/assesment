from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from pm_assessments.models import ProductQuestion

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = BASE_DIR / "data" / "pm_question_bank.json"

CATEGORY_MAP = {
    "product_sense": ProductQuestion.CATEGORY_PRODUCT,
    "execution": ProductQuestion.CATEGORY_EXECUTION,
    "strategy": ProductQuestion.CATEGORY_STRATEGY,
    "analytics": ProductQuestion.CATEGORY_ANALYTICS,
    "technical": ProductQuestion.CATEGORY_TECHNICAL,
    "ux": ProductQuestion.CATEGORY_DESIGN,
    "behavioral": ProductQuestion.CATEGORY_BEHAVIORAL,
    "executive": ProductQuestion.CATEGORY_STRATEGY,
}


def normalize_question_type(raw_value: str) -> str:
    normalized = (raw_value or "").strip().lower()
    if not normalized:
        return ProductQuestion.TYPE_OPEN_ENDED
    normalized = normalized.replace("_advanced", "")
    if normalized == "mcq":
        return ProductQuestion.TYPE_MULTIPLE
    if normalized == "estimation":
        return ProductQuestion.TYPE_ESTIMATION
    if normalized == "prioritization":
        return ProductQuestion.TYPE_PRIORITIZATION
    if normalized == "reasoning":
        return ProductQuestion.TYPE_REASONING
    return ProductQuestion.TYPE_OPEN_ENDED


class Command(BaseCommand):
    help = "Import the supplied PM assessment dataset with normalized fields."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            default=str(DEFAULT_DATASET),
            help="Path to the JSON dataset exported from the user's sheet.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and normalize the dataset without writing to the database.",
        )

    def handle(self, *args, **options):
        dataset_path = Path(options["path"])
        if not dataset_path.exists():
            raise CommandError(f"Dataset not found: {dataset_path}")
        try:
            payload = json.loads(dataset_path.read_text())
        except json.JSONDecodeError as exc:  # pragma: no cover - surfaced to CLI
            raise CommandError(f"Invalid JSON dataset: {exc}") from exc
        if not isinstance(payload, list):
            raise CommandError("Dataset must be a JSON array of question objects")

        created = updated = 0
        dry_run = options["dry_run"]
        for idx, row in enumerate(payload, start=1):
            normalized = self._normalize_row(row, idx)
            question_text = normalized.pop("question_text")
            if dry_run:
                continue
            _, was_created = ProductQuestion.objects.update_or_create(
                question_text=question_text,
                defaults=normalized,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(f"Validated {len(payload)} records (dry run)."))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Imported {created} new and {updated} existing product questions."
                )
            )

    def _normalize_row(self, row: dict, idx: int) -> dict:
        try:
            category_key = (row.get("category") or "").strip().lower()
            category = CATEGORY_MAP[category_key]
        except KeyError as exc:
            raise CommandError(f"Row {idx}: unsupported category '{row.get('category')}'") from exc

        question_type = normalize_question_type(row.get("question_type", ""))
        question_text = (row.get("question_text") or "").strip()
        if not question_text:
            raise CommandError(f"Row {idx}: question_text is required")

        difficulty = row.get("difficulty") or row.get("difficulty_level") or 3
        try:
            difficulty_level = int(difficulty)
        except (TypeError, ValueError) as exc:
            raise CommandError(f"Row {idx}: invalid difficulty '{difficulty}'") from exc

        scoring_weight = Decimal(str(difficulty_level))
        raw_options = row.get("options") or []
        if question_type == ProductQuestion.TYPE_MULTIPLE:
            if not isinstance(raw_options, list) or not raw_options:
                raise CommandError(f"Row {idx}: multiple choice questions need an options list")
            options = [str(option).strip() for option in raw_options]
            correct_answer = row.get("correct_answer")
            if correct_answer is None:
                raise CommandError(f"Row {idx}: multiple choice questions need a correct_answer")
        else:
            options = []
            correct_answer = None

        normalized = {
            "question_text": question_text,
            "question_type": question_type,
            "difficulty_level": difficulty_level,
            "category": category,
            "options": options,
            "correct_answer": correct_answer,
            "scoring_weight": scoring_weight,
            "is_active": True,
        }
        return normalized
