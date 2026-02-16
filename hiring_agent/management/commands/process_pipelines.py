"""
Management command to process all active hiring pipelines.
Designed to be run by Heroku Scheduler every 10 minutes.

Usage:
    python manage.py process_pipelines
    python manage.py process_pipelines --pipeline-id 123
"""
from django.core.management.base import BaseCommand

from hiring_agent.models import HiringPipeline
from hiring_agent.services import process_pipeline


class Command(BaseCommand):
    help = 'Process all active hiring pipelines through the AI state machine'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pipeline-id',
            type=int,
            help='Process only a specific pipeline by ID',
        )

    def handle(self, *args, **options):
        pipeline_id = options.get('pipeline_id')

        if pipeline_id:
            pipelines = HiringPipeline.objects.filter(id=pipeline_id)
        else:
            pipelines = HiringPipeline.objects.filter(status='active')

        total = pipelines.count()
        if total == 0:
            self.stdout.write('No active pipelines to process.')
            return

        self.stdout.write(f'Processing {total} pipeline(s)...\n')
        has_errors = False

        for pipeline in pipelines:
            self.stdout.write(f'  Pipeline: {pipeline.title} (ID={pipeline.id})')
            try:
                stats = process_pipeline(pipeline)
                if stats.get('skipped'):
                    self.stdout.write(f'    Skipped: {stats["reason"]}')
                else:
                    self.stdout.write(
                        f'    Screened={stats["screened"]} '
                        f'Shortlisted={stats["shortlisted"]} '
                        f'Rejected={stats["rejected_at_screen"]} '
                        f'Sent={stats["assessments_sent"]} '
                        f'Checked={stats["results_checked"]} '
                        f'Decisions={stats["decisions_made"]} '
                        f'Finalized={stats["finalized"]} '
                        f'Errors={stats["errors"]}'
                    )
                    if stats.get('errors'):
                        has_errors = True
            except Exception as exc:
                self.stderr.write(f'    ERROR: {exc}')
                has_errors = True

        if has_errors:
            self.stderr.write(self.style.ERROR(f'\nDone with errors. Processed {total} pipeline(s).'))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS(f'\nDone! Processed {total} pipeline(s).'))
