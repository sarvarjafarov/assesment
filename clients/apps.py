import time

from django.apps import AppConfig


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
            state, _ = payload
            cache.delete(_oauth_state_cache_key(state_id))
    except Exception:
        pass
    return state


class ClientsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clients'

    def ready(self):
        from allauth.socialaccount.internal import statekit
        statekit.stash_state = _patched_stash_state
        statekit.unstash_state = _patched_unstash_state
