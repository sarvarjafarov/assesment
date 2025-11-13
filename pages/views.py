from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django import forms

from assessments.forms import AssessmentInviteForm
from assessments.models import RoleCategory
from assessments.services import send_invite_email

FEATURES = [
    {
        "slug": "scheduling",
        "title": "Employee Scheduling",
        "description": "Visual shift planning with automated compliance guardrails.",
    },
    {
        "slug": "time",
        "title": "Time Tracking",
        "description": "Precise clock-ins with GPS verification and overtime alerts.",
    },
    {
        "slug": "operations",
        "title": "Daily Operations",
        "description": "Dispatch tasks, capture field updates, and keep everyone aligned.",
    },
    {
        "slug": "communications",
        "title": "Internal Communication",
        "description": "Secure, threaded conversations for every job site.",
    },
    {
        "slug": "payroll",
        "title": "Payroll",
        "description": "Push-button payroll exports with automatic deductions.",
    },
    {
        "slug": "hr",
        "title": "HR Management",
        "description": "Manage onboarding through offboarding with ease.",
    },
]

ARTICLES = [
    {
        "pill": "HR Insights",
        "pill_class": "accent",
        "title": "The 5 Best HR Software Solutions for Construction Companies in 2025",
        "summary": "Discover the top HR software platforms built for construction, from automation to enterprise-grade compliance.",
        "author": "Nathan Belaye",
        "date": "October 13, 2025",
    },
    {
        "pill": "Best Practices",
        "pill_class": "success",
        "title": "Time Tracking Software for Landscaping: Streamline Your Field Teams",
        "summary": "Landscaping crews waste hours juggling disconnected tools. See how Sira unifies tracking and payroll.",
        "author": "Nathan Belay",
        "date": "October 6, 2025",
    },
    {
        "pill": "Product News",
        "pill_class": "neutral",
        "title": "Connecteam vs. Sira: The Age of Voice AI",
        "summary": "Learn how Sira's voice AI office manager keeps admins updated and workers empowered in the field.",
        "author": "Business Owner's Guide",
        "date": "October 5, 2025",
    },
]


def home(request):
    """Render the marketing landing page."""
    assessment_categories = (
        RoleCategory.objects.filter(is_active=True)
        .prefetch_related("assessments")
        .order_by("name")
    )

    if request.method == "POST":
        form = AssessmentInviteForm(request.POST)
        if form.is_valid():
            try:
                result = form.save(invited_by="Site CTA")
                session_link = request.build_absolute_uri(
                    reverse("candidate:session-entry", args=[result.session.uuid])
                )
                send_invite_email(
                    candidate=result.candidate,
                    assessment=result.assessment,
                    session=result.session,
                    session_link=session_link,
                    invited_by="Site CTA",
                    notes=form.cleaned_data.get("notes", ""),
                )
                messages.success(
                    request,
                    f"Invite created for {result.candidate.first_name} "
                    f"({result.assessment.title}).",
                )
                return redirect(f"{reverse('pages:home')}#cta")
            except forms.ValidationError as exc:
                form.add_error(None, exc)
    else:
        form = AssessmentInviteForm()

    return render(
        request,
        "pages/home.html",
        {
            "features": FEATURES,
            "articles": ARTICLES,
            "assessment_categories": assessment_categories,
            "invite_form": form,
        },
    )
