from django.core.management.base import BaseCommand
from seo.models import SeoPage


class Command(BaseCommand):
    help = 'Audit SEO pages for missing metadata and duplicate paths.'

    def handle(self, *args, **options):
        pages = list(SeoPage.objects.all())
        duplicates: dict[tuple[str, str], list[SeoPage]] = {}
        for page in pages:
            key = (page.path or '', page.match_type)
            duplicates.setdefault(key, []).append(page)
        warnings = []
        for key, entries in duplicates.items():
            if len(entries) > 1:
                warnings.append(f"Multiple SEO pages share path {key[0]!r} ({key[1]}): {', '.join(p.slug for p in entries)}")
        for page in pages:
            if not page.title:
                warnings.append(f"{page.slug}: missing title")
            if not page.description:
                warnings.append(f"{page.slug}: missing description")
            if page.match_type == SeoPage.MATCH_REGEX and not page.path:
                warnings.append(f"{page.slug}: regex match requires a pattern")
        if warnings:
            self.stdout.write(self.style.WARNING('SEO audit found issues:'))
            for warning in warnings:
                self.stdout.write(f'  • {warning}')
        else:
            self.stdout.write(self.style.SUCCESS('SEO audit passed with no issues.'))
