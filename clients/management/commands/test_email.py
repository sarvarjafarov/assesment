"""
Management command to test email configuration.
Usage: python manage.py test_email <recipient_email>
"""

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Recipient email address')

    def handle(self, *args, **options):
        recipient = options['email']

        self.stdout.write('Testing email configuration...')
        self.stdout.write(f'  Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'  Host: {settings.EMAIL_HOST}')
        self.stdout.write(f'  Port: {settings.EMAIL_PORT}')
        self.stdout.write(f'  From: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'  To: {recipient}')
        self.stdout.write('')

        try:
            send_mail(
                subject='Evalon Email Test',
                message='This is a test email from Evalon. If you received this, your email configuration is working!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )

            self.stdout.write(
                self.style.SUCCESS(f'✓ Test email sent successfully to {recipient}')
            )
            self.stdout.write('  Check the inbox (and spam folder) for the test email')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to send test email')
            )
            self.stdout.write(f'  Error: {str(e)}')
            self.stdout.write('')
            self.stdout.write('Common issues:')
            self.stdout.write('  1. Invalid SendGrid API key')
            self.stdout.write('  2. Sender email not verified in SendGrid')
            self.stdout.write('  3. SendGrid account suspended or limited')
            self.stdout.write('  4. Firewall blocking SMTP port 587')
