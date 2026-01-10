"""
Management command to list all client accounts.
Usage: python manage.py list_accounts
"""

from django.core.management.base import BaseCommand
from clients.models import ClientAccount


class Command(BaseCommand):
    help = 'List all client accounts'

    def handle(self, *args, **options):
        accounts = ClientAccount.objects.all().order_by('-created_at')

        if not accounts.exists():
            self.stdout.write(
                self.style.WARNING('No client accounts found in database')
            )
            return

        self.stdout.write(f'Found {accounts.count()} client account(s):')
        self.stdout.write('')

        for i, account in enumerate(accounts, 1):
            self.stdout.write(f'{i}. {account.company_name}')
            self.stdout.write(f'   Email: {account.email}')
            self.stdout.write(f'   Name: {account.full_name}')
            self.stdout.write(f'   Status: {account.status}')
            self.stdout.write(f'   Email Verified: {"Yes" if account.is_email_verified else "No"}')
            self.stdout.write(f'   Created: {account.created_at}')
            self.stdout.write('')
