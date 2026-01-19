"""
Management command to distribute difficulty levels across behavioral questions.

This ensures that questions are available for all assessment levels (Junior, Mid, Senior).
"""
from django.core.management.base import BaseCommand

from behavioral_assessments.models import BehavioralQuestion


class Command(BaseCommand):
    help = "Distribute difficulty levels across behavioral questions for level-based filtering"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        questions = list(BehavioralQuestion.objects.filter(is_active=True).order_by("block_id"))
        total = len(questions)

        if total == 0:
            self.stdout.write(self.style.WARNING("No active behavioral questions found."))
            return

        self.stdout.write(f"Found {total} active behavioral questions")

        # Distribution strategy:
        # - 20% at level 1-2 (Junior: foundational)
        # - 40% at level 2-4 (Mid: applied knowledge)
        # - 40% at level 3-5 (Senior: strategic)
        # We'll create overlap to ensure each level has enough questions

        # Assign levels based on position in the list
        # First 30% -> levels 1-2 (Junior focused)
        # Middle 40% -> levels 2-4 (Mid focused)
        # Last 30% -> levels 4-5 (Senior focused)

        junior_end = int(total * 0.3)
        mid_end = int(total * 0.7)

        updated = 0
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        for i, question in enumerate(questions):
            if i < junior_end:
                # Junior range: alternate between 1 and 2
                new_level = 1 if i % 2 == 0 else 2
            elif i < mid_end:
                # Mid range: alternate between 2, 3, and 4
                new_level = 2 + (i % 3)
            else:
                # Senior range: alternate between 4 and 5
                new_level = 4 if i % 2 == 0 else 5

            distribution[new_level] += 1

            if question.difficulty_level != new_level:
                if dry_run:
                    self.stdout.write(
                        f"  Would update question {question.block_id}: "
                        f"level {question.difficulty_level} -> {new_level}"
                    )
                else:
                    question.difficulty_level = new_level
                    question.save(update_fields=["difficulty_level"])
                updated += 1

        self.stdout.write("")
        self.stdout.write("Distribution summary:")
        for level, count in distribution.items():
            self.stdout.write(f"  Difficulty {level}: {count} questions")

        self.stdout.write("")
        self.stdout.write("Level coverage:")
        self.stdout.write(f"  Junior (1-2): {distribution[1] + distribution[2]} questions")
        self.stdout.write(f"  Mid (2-4): {distribution[2] + distribution[3] + distribution[4]} questions")
        self.stdout.write(f"  Senior (3-5): {distribution[3] + distribution[4] + distribution[5]} questions")

        if dry_run:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING(f"DRY RUN: Would update {updated} questions"))
            self.stdout.write("Run without --dry-run to apply changes")
        else:
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS(f"Updated {updated} questions"))
