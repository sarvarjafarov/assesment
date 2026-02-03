"""
Custom social account adapter for django-allauth.
Integrates social authentication with the ClientAccount model.
"""
import logging

from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter

from .models import ClientAccount

User = get_user_model()
logger = logging.getLogger(__name__)


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

        email = (sociallogin.account.extra_data or {}).get('email')
        if not email:
            return

        # Check if a User exists with this email (at most one)
        try:
            existing_user = User.objects.filter(email__iexact=email).first()
            if existing_user:
                sociallogin.connect(request, existing_user)
        except Exception as e:
            logger.warning("pre_social_login: could not link by email %s: %s", email, e)

    def save_user(self, request, sociallogin, form=None):
        """
        Called when creating a new user from social login.
        Creates the associated ClientAccount record.
        """
        try:
            user = super().save_user(request, sociallogin, form)
        except Exception as e:
            logger.exception("Social signup: save_user failed: %s", e)
            raise

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

        # Extract user info: allauth often sets user.email from the provider; fall back to extra_data
        extra_data = sociallogin.account.extra_data or {}
        email = (
            getattr(user, 'email', None)
            or extra_data.get('email')
            or (getattr(user, 'username', None) if getattr(user, 'username', None) and '@' in str(getattr(user, 'username', '')) else None)
        )
        if not email or not str(email).strip():
            logger.error("Social signup: no email from provider %s for user id=%s", provider, getattr(user, 'pk', None))
            raise ValueError("Your account did not provide an email address. Please sign up with email instead.")
        email = str(email).strip().lower()
        full_name = self._get_full_name(extra_data, provider)

        # Check if ClientAccount already exists (edge case)
        try:
            client = ClientAccount.objects.get(email__iexact=email)
            # Link to the new user if not linked
            if not client.user:
                client.user = user
                client.auth_provider = auth_provider
                ClientAccount.objects.filter(pk=client.pk).update(
                    user=user, auth_provider=auth_provider
                )
            user.is_active = True
            user.save(update_fields=['is_active'])
        except ClientAccount.DoesNotExist:
            # Create new ClientAccount with placeholder data
            client = ClientAccount(
                user=user,
                email=email,
                full_name=full_name or (email.split('@')[0] if email else ''),
                company_name='',  # Will be completed in profile
                phone_number='',  # Will be completed in profile
                employee_size='1-10',  # Default, will be updated
                auth_provider=auth_provider,
                status='pending',  # Still requires admin approval
            )
            try:
                client.save()
            except Exception as e:
                logger.exception("Social signup: ClientAccount save failed: %s", e)
                raise
            user.is_active = True
            user.save(update_fields=['is_active'])
            client.mark_email_verified()

        return user

    def on_authentication_error(
        self, request, provider, error=None, exception=None, extra_context=None
    ):
        """Log the error and add troubleshooting context for site owners."""
        provider_id = getattr(provider, "id", str(provider))
        logger.warning(
            "Social auth error: provider=%s error=%s exception=%s",
            provider_id,
            error,
            exception,
            exc_info=exception is not None,
        )
        if extra_context is None:
            extra_context = {}
        # Surface the actual error so site owners can fix it (e.g. invalid_grant, missing env)
        if exception is not None:
            extra_context["error_summary"] = str(exception)
        elif error is not None:
            extra_context["error_summary"] = str(error)
        # Add troubleshooting hint for Google OAuth (common: redirect_uri / credentials)
        if provider_id == "google":
            # Use the request so we show the exact callback URL that was used
            callback_url = request.build_absolute_uri("/accounts/google/login/callback/")
            extra_context["oauth_troubleshooting"] = {
                "provider": "Google",
                "callback_url": callback_url,
                "hint": "Ensure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set on Heroku, and that the Authorized redirect URI in Google Cloud Console includes this exact URL.",
            }
        super().on_authentication_error(
            request, provider, error=error, exception=exception, extra_context=extra_context
        )

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
