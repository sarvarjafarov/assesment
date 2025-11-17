from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import ProgrammingError

from behavioral_assessments.models import BehavioralQuestion


DATASET_PATH = Path(__file__).resolve().parents[3] / "assessments" / "data" / "behavioral_blocks.json"


class Command(BaseCommand):
    help = "Import behavioral question blocks into the dedicated assessment bank."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            default=str(DATASET_PATH),
            help="Path to the behavioral blocks JSON dataset.",
        )

    def handle(self, *args, **options):
        dataset = Path(options["path"])
        if not dataset.exists():
            raise CommandError(f"Dataset not found at {dataset}")
        try:
            blocks = json.loads(dataset.read_text())
        except json.JSONDecodeError as exc:  # pragma: no cover
            raise CommandError(f"Invalid JSON dataset: {exc}") from exc
        if not isinstance(blocks, list):
            raise CommandError("Dataset must contain a list of blocks")
        created = updated = 0
        for block in blocks:
            block_id = block.get("id")
            statements = block.get("statements") or []
            if not isinstance(block_id, int):
                raise CommandError(f"Invalid block id: {block_id}")
            try:
                _, was_created = BehavioralQuestion.objects.update_or_create(
                    block_id=block_id,
                    defaults={
                        "statements": statements,
                        "prompt": block.get(
                            "prompt",
                            "Select which statement is most and least like you.",
                        ),
                    },
                )
            except ProgrammingError as exc:
                raise CommandError(
                    "Behavioral tables are missing. Run `python manage.py migrate behavioral_assessments` first."
                ) from exc
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {created} new and {updated} existing behavioral blocks."
            )
        )
