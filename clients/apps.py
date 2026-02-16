import time

from django.apps import AppConfig


# ---------------------------------------------------------------------------
# LinkedIn OIDC patches
# LinkedIn deprecated /v2/me and /v2/emailAddress in 2024.
# allauth 65.x still hits those endpoints → 403.  We monkey-patch the
# adapter to call /v2/userinfo (OpenID Connect) and update the provider
# to parse the OIDC response format.
# ---------------------------------------------------------------------------

_LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"


def _linkedin_get_user_info(self, token):
    """Fetch user data from LinkedIn's OIDC userinfo endpoint."""
    from allauth.socialaccount.adapter import get_adapter

    headers = {"Authorization": f"Bearer {token.token}"}
    with get_adapter().get_requests_session() as session:
        resp = session.get(_LINKEDIN_USERINFO_URL, headers=headers)
        resp.raise_for_status()
        return resp.json()


def _linkedin_extract_uid(self, data):
    """OIDC returns 'sub' as the unique identifier."""
    return str(data.get("sub", data.get("id", "")))


def _linkedin_extract_common_fields(self, data):
    """OIDC returns given_name/family_name/email at top level."""
    return {
        "first_name": data.get("given_name", ""),
        "last_name": data.get("family_name", ""),
        "email": data.get("email", ""),
    }


def _linkedin_get_default_scope(self):
    return ["openid", "profile", "email"]


def _oauth_state_cache_key(state_id):
    return f"oauth_state:{state_id}"


def _patched_stash_state(request, state, state_id=None):
    """Stash state in session (original) AND in cache so callback can find it if session is lost."""
    from allauth.socialaccount.adapter import get_adapter
    from allauth.socialaccount.internal import statekit

    states = statekit.get_states(request)
    statekit.gc_states(states)
    if state_id is None:
        state_id = get_adapter().generate_state_param(state)
    states[state_id] = (state, time.time())
    request.session[statekit.STATES_SESSION_KEY] = states

    # Also store in cache so callback can restore state when session cookie is not sent
    try:
        from django.core.cache import caches
        cache = caches["oauth_state"]
        payload = (state, time.time())
        cache.set(_oauth_state_cache_key(state_id), payload, timeout=600)
    except Exception:
        pass
    return state_id


def _patched_unstash_state(request, state_id):
    """Unstash from session first; if missing, try cache (fixes session lost on redirect)."""
    from allauth.socialaccount.internal import statekit

    state = None
    states = statekit.get_states(request)
    state_ts = states.get(state_id)
    if state_ts is not None:
        state = state_ts[0]
        del states[state_id]
        request.session[statekit.STATES_SESSION_KEY] = states
        return state

    # Session lost (cookie not sent on redirect) — try cache
    try:
        from django.core.cache import caches
        cache = caches["oauth_state"]
        payload = cache.get(_oauth_state_cache_key(state_id))
        if payload is not None:
            state, ts = payload
            cache.delete(_oauth_state_cache_key(state_id))
            # Reject stale states older than 5 minutes
            if time.time() - ts > 300:
                return None
    except Exception:
        pass
    return state


class ClientsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clients'
    verbose_name = 'Clients & Accounts'

    def ready(self):
        from allauth.socialaccount.internal import statekit
        statekit.stash_state = _patched_stash_state
        statekit.unstash_state = _patched_unstash_state

        # Patch LinkedIn adapter to use OIDC /v2/userinfo
        from allauth.socialaccount.providers.linkedin_oauth2.views import (
            LinkedInOAuth2Adapter,
        )
        from allauth.socialaccount.providers.linkedin_oauth2.provider import (
            LinkedInOAuth2Provider,
        )

        LinkedInOAuth2Adapter.get_user_info = _linkedin_get_user_info
        LinkedInOAuth2Provider.extract_uid = _linkedin_extract_uid
        LinkedInOAuth2Provider.extract_common_fields = _linkedin_extract_common_fields
        LinkedInOAuth2Provider.get_default_scope = _linkedin_get_default_scope
