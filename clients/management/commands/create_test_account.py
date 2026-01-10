"""
Management command to create a test client account.
Usage: python manage.py create_test_account
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from clients.models import ClientAccount

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a test client account for sarvar@pethoven.com'

    def handle(self, *args, **options):
        email = 'sarvar@pethoven.com'

        # Check if account already exists
        if ClientAccount.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'Account with email {email} already exists')
            )
            return

        self.stdout.write(f'Creating test account for {email}...')

        try:
            # Create user
            user = User.objects.create_user(
                username=email,
                email=email,
                password='testpass123',  # You can change this
                first_name='Sarvar',
            )
            user.is_active = False  # Will be activated when approved
            user.save()

            # Create client account
            account = ClientAccount.objects.create(
                user=user,
                full_name='Sarvar Jafarov',
                company_name='Test Company',
                email=email,
                phone_number='+1 (555) 123-4567',
                employee_size='1-10',
                requested_assessments=['marketing', 'product'],
                allowed_assessments=[],  # Admin will set this
                status='pending',
                notes='Test account created via management command',
                plan_slug='starter',
            )

            self.stdout.write(
                self.style.SUCCESS(f'✓ Account created successfully!')
            )
            self.stdout.write('')
            self.stdout.write('Account Details:')
            self.stdout.write(f'  Email: {account.email}')
            self.stdout.write(f'  Password: testpass123')
            self.stdout.write(f'  Company: {account.company_name}')
            self.stdout.write(f'  Status: {account.status}')
            self.stdout.write(f'  Email Verified: {account.is_email_verified}')
            self.stdout.write('')
            self.stdout.write('Next steps:')
            self.stdout.write('  1. Run: python manage.py verify_email_manual sarvar@pethoven.com')
            self.stdout.write('  2. Approve account in Django admin')
            self.stdout.write('  3. Login at /clients/login/ with email and password above')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to create account: {str(e)}')
            )
            raise
