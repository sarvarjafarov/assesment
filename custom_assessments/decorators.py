"""
Decorators for Custom Assessments access control.
"""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def premium_required(view_func):
    """
    Decorator to restrict access to pro/enterprise plan users.

    Redirects non-pro users to dashboard with a message.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return redirect("clients:login")

        if not hasattr(request.user, "client_account"):
            return redirect("clients:login")

        account = request.user.client_account

        # Check if user has pro or enterprise plan
        if account.plan_slug not in ("pro", "enterprise"):
            messages.warning(
                request,
                "Custom Assessments require a Pro or Enterprise plan. "
                "Please upgrade to access this feature."
            )
            return redirect("clients:dashboard")

        return view_func(request, *args, **kwargs)

    return wrapper


def check_custom_assessment_limit(view_func):
    """
    Decorator to check if user has reached their custom assessment limit.

    Pro users: 10 assessments
    Enterprise users: Unlimited
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, "client_account"):
            return redirect("clients:login")

        account = request.user.client_account

        # Enterprise has unlimited
        if account.plan_slug == "enterprise":
            return view_func(request, *args, **kwargs)

        # Pro has limit of 10
        if account.plan_slug == "pro":
            from .models import CustomAssessment

            current_count = CustomAssessment.objects.filter(
                client=account
            ).exclude(status="archived").count()

            if current_count >= 10:
                messages.warning(
                    request,
                    "You've reached the maximum of 10 custom assessments. "
                    "Archive existing assessments or upgrade to Enterprise for unlimited."
                )
                return redirect("custom_assessments:list")

        return view_func(request, *args, **kwargs)

    return wrapper
