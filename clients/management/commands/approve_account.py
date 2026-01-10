"""
Management command to approve a client account.
Usage: python manage.py approve_account <email>
"""

from django.core.management.base import BaseCommand, CommandError
from clients.models import ClientAccount
from clients.services import send_welcome_email


class Command(BaseCommand):
    help = 'Approve a client account and send welcome email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address of the client account')
        parser.add_argument(
            '--assessments',
            nargs='+',
            help='Allowed assessments (marketing, product, behavioral)',
            default=['marketing', 'product', 'behavioral']
        )

    def handle(self, *args, **options):
        email = options['email']
        assessments = options['assessments']

        try:
            account = ClientAccount.objects.get(email=email)
        except ClientAccount.DoesNotExist:
            raise CommandError(f'ClientAccount with email "{email}" does not exist')

        # Update account
        account.status = 'approved'
        account.allowed_assessments = assessments
        account.save()

        self.stdout.write(
            self.style.SUCCESS(f'✓ Account approved for {email}')
        )
        self.stdout.write(f'  Allowed assessments: {", ".join(assessments)}')

        # Send welcome email
        self.stdout.write('')
        self.stdout.write('Sending welcome email...')
        try:
            email_sent = send_welcome_email(account)
            if email_sent:
                self.stdout.write(
                    self.style.SUCCESS('✓ Welcome email sent successfully')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Failed to send welcome email')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error sending welcome email: {str(e)}')
            )

        self.stdout.write('')
        self.stdout.write('Account Details:')
        self.stdout.write(f'  Email: {account.email}')
        self.stdout.write(f'  Company: {account.company_name}')
        self.stdout.write(f'  Status: {account.status}')
        self.stdout.write(f'  User Active: {account.user.is_active if account.user else "No user"}')
        self.stdout.write(f'  Allowed Assessments: {", ".join(account.allowed_assessments)}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✓ User can now login at /clients/login/'))
