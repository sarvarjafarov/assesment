"""
Management command to manually verify a client's email (bypass email verification).
Usage: python manage.py verify_email_manual <email>
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from clients.models import ClientAccount


class Command(BaseCommand):
    help = 'Manually verify a client account email (bypass verification email)'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address of the client account')

    def handle(self, *args, **options):
        email = options['email']

        try:
            account = ClientAccount.objects.get(email=email)
        except ClientAccount.DoesNotExist:
            raise CommandError(f'ClientAccount with email "{email}" does not exist')

        if account.is_email_verified:
            self.stdout.write(
                self.style.WARNING(f'Account {email} is already verified at {account.email_verified_at}')
            )
        else:
            account.mark_email_verified()
            self.stdout.write(
                self.style.SUCCESS(f'✓ Email verified for {email}')
            )

        # Show account details
        self.stdout.write('')
        self.stdout.write('Account Details:')
        self.stdout.write(f'  Company: {account.company_name}')
        self.stdout.write(f'  Full Name: {account.full_name}')
        self.stdout.write(f'  Email: {account.email}')
        self.stdout.write(f'  Status: {account.status}')
        self.stdout.write(f'  Email Verified: {"Yes" if account.is_email_verified else "No"}')
        self.stdout.write(f'  Email Verified At: {account.email_verified_at or "Not verified"}')
        self.stdout.write(f'  Created: {account.created_at}')
        self.stdout.write('')

        if account.status == 'pending':
            self.stdout.write(
                self.style.WARNING(
                    'Account is verified but still PENDING approval. '
                    'Change status to "approved" in Django admin to activate the account.'
                )
            )
        elif account.status == 'approved':
            self.stdout.write(
                self.style.SUCCESS(
                    'Account is verified and APPROVED! User can now login.'
                )
            )
