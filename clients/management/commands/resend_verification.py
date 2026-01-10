"""
Management command to resend verification email to a client account.
Usage: python manage.py resend_verification <email>
"""

from django.core.management.base import BaseCommand, CommandError
from clients.models import ClientAccount
from clients.services import send_verification_email


class Command(BaseCommand):
    help = 'Resend verification email to a client account'

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
                self.style.WARNING(f'Account {email} is already verified')
            )
            confirm = input('Send verification email anyway? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write('Cancelled')
                return

        self.stdout.write(f'Sending verification email to {email}...')

        try:
            success = send_verification_email(account)

            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Verification email sent successfully to {email}')
                )
                self.stdout.write(f'  Token: {account.verification_token}')
                self.stdout.write(f'  Sent at: {account.verification_sent_at}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to send verification email to {email}')
                )
                self.stdout.write('  Check your email configuration and SendGrid API key')
        except Exception as e:
            raise CommandError(f'Error sending email: {str(e)}')
