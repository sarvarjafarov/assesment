"""
Management command to set up the Site for allauth.
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = 'Set up the Site model for django-allauth'

    def handle(self, *args, **options):
        # Get the site URL from settings or use default
        site_url = getattr(settings, 'SITE_URL', 'https://www.evalon.tech')
        domain = site_url.replace('https://', '').replace('http://', '').rstrip('/')

        # Update or create the default site
        site, created = Site.objects.update_or_create(
            id=settings.SITE_ID,
            defaults={
                'domain': domain,
                'name': 'Evalon',
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created site: {domain}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated site to: {domain}'))
