"""
Test signup form validation with different email domains.
"""

from django.core.management.base import BaseCommand
from clients.forms import ClientSignupForm


class Command(BaseCommand):
    help = 'Test signup form validation with various email domains'

    def handle(self, *args, **options):
        test_emails = [
            'test@gmail.com',
            'user@yahoo.com',
            'person@outlook.com',
            'someone@hotmail.com',
            'admin@company.com',
            'info@evalon.tech',
        ]

        self.stdout.write('Testing email validation...')
        self.stdout.write('')

        for email in test_emails:
            form_data = {
                'full_name': 'Test User',
                'company_name': 'Test Company',
                'email': email,
                'phone_number': '+1 (555) 123-4567',
                'employee_size': '1-10',
                'requested_assessments': ['marketing'],
                'password1': 'testpass123',
                'password2': 'testpass123',
            }

            form = ClientSignupForm(data=form_data)

            # Check email field specifically
            if form.is_valid():
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {email} - ALLOWED')
                )
            else:
                email_errors = form.errors.get('email', [])
                if email_errors:
                    self.stdout.write(
                        self.style.ERROR(f'✗ {email} - BLOCKED: {email_errors[0]}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'? {email} - Other errors: {form.errors}')
                    )

        self.stdout.write('')
        self.stdout.write('All email domains should be ALLOWED now.')
