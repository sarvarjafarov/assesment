"""
Custom social account adapter for django-allauth.
Integrates social authentication with the ClientAccount model.
"""
from django.shortcuts import redirect
from django.urls import reverse

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter

from .models import ClientAccount


class ClientSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter to handle social account signups and logins.
    Creates or links ClientAccount records for social auth users.
    """

    def pre_social_login(self, request, sociallogin):
        """
        Called after social auth but before login.
        Links social account to existing ClientAccount if email matches.
        """
        if sociallogin.is_existing:
            return

        email = sociallogin.account.extra_data.get('email')
        if not email:
            return

        # Check if a ClientAccount exists with this email
        try:
            client = ClientAccount.objects.get(email__iexact=email)
            if client.user:
                # Link this social account to the existing user
                sociallogin.connect(request, client.user)
        except ClientAccount.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        """
        Called when creating a new user from social login.
        Creates the associated ClientAccount record.
        """
        user = super().save_user(request, sociallogin, form)

        # Determine auth provider
        provider = sociallogin.account.provider
        if provider == 'google':
            auth_provider = 'google'
        elif provider == 'linkedin_oauth2':
            auth_provider = 'linkedin'
        else:
            auth_provider = 'email'

        # Extract user info from social account
        extra_data = sociallogin.account.extra_data
        email = extra_data.get('email', user.email)
        full_name = self._get_full_name(extra_data, provider)

        # Check if ClientAccount already exists (edge case)
        try:
            client = ClientAccount.objects.get(email__iexact=email)
            # Link to the new user if not linked
            if not client.user:
                client.user = user
                client.auth_provider = auth_provider
                client.save(update_fields=['user', 'auth_provider'])
        except ClientAccount.DoesNotExist:
            # Create new ClientAccount with placeholder data
            # User will complete profile after signup
            ClientAccount.objects.create(
                user=user,
                email=email,
                full_name=full_name or email.split('@')[0],
                company_name='',  # Will be completed in profile
                phone_number='',  # Will be completed in profile
                employee_size='1-10',  # Default, will be updated
                auth_provider=auth_provider,
                status='pending',  # Still requires admin approval
            )
            # Mark email as verified (social providers verify emails)
            client = ClientAccount.objects.get(email__iexact=email)
            client.mark_email_verified()

        return user

    def _get_full_name(self, extra_data, provider):
        """Extract full name from social provider data."""
        if provider == 'google':
            return extra_data.get('name', '')
        elif provider == 'linkedin_oauth2':
            first = extra_data.get('given_name', '') or extra_data.get('firstName', '')
            last = extra_data.get('family_name', '') or extra_data.get('lastName', '')
            return f"{first} {last}".strip()
        return ''

    def get_login_redirect_url(self, request):
        """
        Redirect after successful social login.
        If profile incomplete, redirect to profile completion page.
        """
        user = request.user
        if not user.is_authenticated:
            return reverse('clients:login')

        try:
            client = user.client_account
            # Check if profile needs completion (missing company info)
            if not client.company_name:
                return reverse('clients:complete_profile')
            # Check if account is approved
            if client.status != 'approved':
                return reverse('clients:pending_approval')
            return reverse('clients:dashboard')
        except ClientAccount.DoesNotExist:
            return reverse('clients:complete_profile')


class ClientAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter for email-based auth.
    Ensures compatibility with social auth flow.
    """

    def get_login_redirect_url(self, request):
        """Redirect to dashboard after login."""
        user = request.user
        if not user.is_authenticated:
            return reverse('clients:login')

        try:
            client = user.client_account
            if not client.company_name:
                return reverse('clients:complete_profile')
            if client.status != 'approved':
                return reverse('clients:pending_approval')
            return reverse('clients:dashboard')
        except ClientAccount.DoesNotExist:
            return reverse('clients:complete_profile')
