"""
Custom social account adapter for django-allauth.
Integrates social authentication with the ClientAccount model.
"""
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter

from .models import ClientAccount

User = get_user_model()


class ClientSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter to handle social account signups and logins.
    Creates or links ClientAccount records for social auth users.
    """

    def is_open_for_signup(self, request, sociallogin):
        """Allow social signup."""
        return True

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

        # Check if a User exists with this email
        try:
            existing_user = User.objects.get(email__iexact=email)
            # Connect this social account to the existing user
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        """
        Called when creating a new user from social login.
        Creates the associated ClientAccount record.
        """
        user = super().save_user(request, sociallogin, form)

        # IMPORTANT: Keep user active for social auth (they need to complete profile)
        user.is_active = True
        user.save(update_fields=['is_active'])

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
                # Use update to avoid triggering save() which would deactivate user
                ClientAccount.objects.filter(pk=client.pk).update(
                    user=user, auth_provider=auth_provider
                )
            # Re-activate user after ClientAccount link
            user.is_active = True
            user.save(update_fields=['is_active'])
        except ClientAccount.DoesNotExist:
            # Create new ClientAccount with placeholder data
            # Use direct insert to avoid save() deactivating the user
            client = ClientAccount(
                user=user,
                email=email,
                full_name=full_name or email.split('@')[0],
                company_name='',  # Will be completed in profile
                phone_number='',  # Will be completed in profile
                employee_size='1-10',  # Default, will be updated
                auth_provider=auth_provider,
                status='pending',  # Still requires admin approval
            )
            # Save without triggering the user deactivation
            client.save()
            # Re-activate user after ClientAccount creation
            user.is_active = True
            user.save(update_fields=['is_active'])
            # Mark email as verified (social providers verify emails)
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

    def is_open_for_signup(self, request):
        """Allow signup."""
        return True

    def get_login_redirect_url(self, request):
        """Redirect after login based on profile completion status."""
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
