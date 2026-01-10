"""
Management command to manually send welcome email to an approved client.
Usage: python manage.py send_welcome_email <email>
"""

from django.core.management.base import BaseCommand, CommandError
from clients.models import ClientAccount
from clients.services import send_welcome_email


class Command(BaseCommand):
    help = 'Manually send welcome email to an approved client'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address of the client account')

    def handle(self, *args, **options):
        email = options['email']

        try:
            account = ClientAccount.objects.get(email=email)
        except ClientAccount.DoesNotExist:
            raise CommandError(f'ClientAccount with email "{email}" does not exist')

        # Check if account is approved
        if account.status != 'approved':
            self.stdout.write(
                self.style.WARNING(
                    f'Account status is "{account.status}", not "approved". '
                    'Welcome emails should only be sent to approved accounts.'
                )
            )
            confirm = input('Send welcome email anyway? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write('Cancelled')
                return

        # Check if email is verified
        if not account.is_email_verified:
            self.stdout.write(
                self.style.WARNING(
                    f'Account email is not verified yet. '
                    'User should verify email before receiving welcome email.'
                )
            )
            confirm = input('Send welcome email anyway? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write('Cancelled')
                return

        # Check if they have approved assessments
        if not account.allowed_assessments:
            self.stdout.write(
                self.style.WARNING(
                    'Account has NO allowed assessments set! '
                    'Set allowed_assessments in admin before sending welcome email.'
                )
            )
            confirm = input('Send welcome email anyway? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write('Cancelled')
                return

        self.stdout.write('')
        self.stdout.write('Account Details:')
        self.stdout.write(f'  Email: {account.email}')
        self.stdout.write(f'  Company: {account.company_name}')
        self.stdout.write(f'  Full Name: {account.full_name}')
        self.stdout.write(f'  Status: {account.status}')
        self.stdout.write(f'  Email Verified: {account.is_email_verified}')
        self.stdout.write(f'  Allowed Assessments: {", ".join(account.allowed_assessments) if account.allowed_assessments else "None"}')
        self.stdout.write(f'  Plan: {account.plan_details()["label"]}')
        self.stdout.write('')

        self.stdout.write('Sending welcome email...')

        try:
            email_sent = send_welcome_email(account)

            if email_sent:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Welcome email sent successfully to {account.email}')
                )
                self.stdout.write('')
                self.stdout.write('The email includes:')
                self.stdout.write('  - Personal greeting')
                self.stdout.write('  - Dashboard access link')
                self.stdout.write('  - Account details (plan, quotas)')
                self.stdout.write('  - Approved assessments list')
                self.stdout.write('  - 3-step getting started guide')
                self.stdout.write('  - Support resources')
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to send welcome email to {account.email}')
                )
                self.stdout.write('')
                self.stdout.write('Possible issues:')
                self.stdout.write('  - Check Brevo SMTP credentials in .env')
                self.stdout.write('  - Verify SITE_URL is set correctly')
                self.stdout.write('  - Check if email address is valid')
                self.stdout.write('  - Review server logs for detailed error')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error sending welcome email: {str(e)}')
            )
            raise
