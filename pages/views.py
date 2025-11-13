from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django import forms

from assessments.forms import AssessmentInviteForm
from assessments.models import RoleCategory
from assessments.services import send_invite_email

FEATURES = [
    {
        "slug": "scope",
        "title": "Scope & design",
        "description": "Match roles to catalog assignments or build your own criteria.",
        "panel_title": "Assessment designer",
        "panel_subtitle": "Control expertise, competencies, and required artifacts before the invite goes out.",
        "panel_points": [
            "Leverage 25+ ready-to-run templates or clone your own.",
            "Set deadlines, reviewers, and auto-reminders per role.",
            "Collect structured uploads, videos, or case study answers.",
        ],
    },
    {
        "slug": "invite",
        "title": "Invite & align",
        "description": "Send branded instructions to candidates and collaborators.",
        "panel_title": "Branded candidate briefing",
        "panel_subtitle": "Every invite includes a timeline, recruiter notes, and a mobile-friendly start button.",
        "panel_points": [
            "Personalized landing page per candidate.",
            "Live status signals—opened, started, submitted.",
            "Secure share links for hiring panels and agencies.",
        ],
    },
    {
        "slug": "score",
        "title": "Auto score & shortlist",
        "description": "Capture evidence, auto score responses, and surface the standouts.",
        "panel_title": "Scoring console",
        "panel_subtitle": "Structured rubrics transform responses into a ranked slate with bias controls.",
        "panel_points": [
            "Per-question scoring with calibration notes.",
            "Auto advancement rules based on thresholds.",
            "Export-ready summaries for hiring managers.",
        ],
    },
    {
        "slug": "decide",
        "title": "Decide & handoff",
        "description": "Advance shortlisted talent to interviews or offers with context.",
        "panel_title": "Decision workspace",
        "panel_subtitle": "Log the rationale, notify candidates, and sync to your ATS without copy-paste.",
        "panel_points": [
            "One-click advance/reject with templated communications.",
            "Shareable highlight reels for interviewers.",
            "Audit trail covering every reviewer action.",
        ],
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

TESTIMONIALS = [
    {
        "name": "Savannah",
        "role": "Founder of Hailo",
        "quote": "This is the first time our scheduler, time tracker, and team communication are all in one place. It's incredibly simple to use, and I can definitely see us sticking with it for years.",
        "avatar": "img/avatar-savannah.svg",
    },
    {
        "name": "Marcus",
        "role": "VP People, Copper Build",
        "quote": "Sira gave our hiring pods one console to scope assignments, tag reviewers, and advance reliable operators—we ship offers faster than ever.",
        "avatar": "img/avatar-marcus.svg",
    },
    {
        "name": "Priya",
        "role": "Head of Talent, Aster Care",
        "quote": "Auto scoring shaved days off each search. Candidates stay informed while our team sees a clear, auditable shortlist.",
        "avatar": "img/avatar-priya.svg",
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
                intro_link = request.build_absolute_uri(
                    reverse("candidate:session-entry", args=[result.session.uuid])
                )
                start_link = request.build_absolute_uri(
                    reverse("candidate:session-start", args=[result.session.uuid])
                )
                send_invite_email(
                    candidate=result.candidate,
                    assessment=result.assessment,
                    session=result.session,
                    intro_link=intro_link,
                    start_link=start_link,
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
            "testimonials": TESTIMONIALS,
            "assessment_categories": assessment_categories,
            "invite_form": form,
        },
    )
