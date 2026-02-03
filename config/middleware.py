"""
Middleware to fix session cookie domain for Google OAuth on www.evalon.tech.

When the request host is evalon.tech or www.evalon.tech, we ensure the session
cookie is set with Domain=.evalon.tech so it is sent when Google redirects back
(same cookie works for both www and non-www). This fixes "session lost" for both
login and sign-up with Google without requiring SESSION_COOKIE_DOMAIN in Heroku config.
"""
import re


# Hosts that should get session cookie with domain .evalon.tech
EVALON_HOST_RE = re.compile(r"^(www\.)?evalon\.tech$", re.I)


class SessionCookieDomainMiddleware:
    """
    Run after SessionMiddleware. If the request host is evalon.tech or www.evalon.tech,
    rewrite the session Set-Cookie header to include Domain=.evalon.tech.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return self._patch_session_cookie(request, response)

    def _patch_session_cookie(self, request, response):
        from django.conf import settings as django_settings

        host = request.get_host().split(":")[0]
        if not EVALON_HOST_RE.match(host):
            return response

        session_cookie_name = django_settings.SESSION_COOKIE_NAME
        cookie_domain = ".evalon.tech"

        # Find Set-Cookie header for the session
        set_cookie = response.cookies.get(session_cookie_name)
        if set_cookie is None:
            return response

        # Force the cookie to be set with Domain=.evalon.tech so it's sent on callback
        set_cookie["domain"] = cookie_domain
        return response
