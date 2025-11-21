from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django import forms

from assessments.forms import AssessmentInviteForm
from assessments.services import send_invite_email
from blog.models import BlogPost

def home(request):
    """Render the marketing landing page."""
    assessment_suite = [
        {
            "slug": "marketing",
            "label": "Marketing IQ",
            "title": "Digital marketing",
            "summary": "Scenario-based prompts spanning paid media, SEO, analytics, and GTM strategy.",
            "focus": ["Paid media", "SEO", "Analytics"],
            "stats": [
                {"label": "Question bank", "value": "40 curated scenes"},
                {"label": "Avg completion", "value": "32 min"},
                {"label": "Benchmarks", "value": "Role-based"},
            ],
        },
        {
            "slug": "product",
            "label": "Product Sense",
            "title": "Product management",
            "summary": "Reasoning, estimation, prioritization, and UX critiques calibrated for ICs and leads.",
            "focus": ["Prioritization", "Estimation", "UX critique"],
            "stats": [
                {"label": "Prompts", "value": "Reasoning + scenario mix"},
                {"label": "Difficulty", "value": "Ladders by seniority"},
                {"label": "Profile views", "value": "Power-user vs broad"},
            ],
        },
        {
            "slug": "behavioral",
            "label": "Behavioral DNA",
            "title": "Leadership & soft skills",
            "summary": "Adaptive block inventory highlighting collaboration style, risk posture, and coaching needs.",
            "focus": ["Collaboration", "Risk posture", "Coaching"],
            "stats": [
                {"label": "Duration", "value": "15 minutes"},
                {"label": "Signals", "value": "Integrity + engagement"},
                {"label": "Deliverable", "value": "Guided debrief points"},
            ],
        },
    ]

    features = [
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

    live_events = [
        {"company": "Latitude Labs", "assessment": "PM scope challenge", "ago": "2 min ago"},
        {"company": "Northwind", "assessment": "Behavioral inventory", "ago": "7 min ago"},
        {"company": "Copper Build", "assessment": "Growth marketing scenario", "ago": "12 min ago"},
    ]

    case_studies = [
        {
            "slug": "atlas",
            "company": "Atlas CRM",
            "headline": "37% faster time-to-offer for product hires.",
            "result": "Centralized PM assessments with automated scoring and shared highlights.",
            "metric_label": "Hiring speed",
            "metric_value": "-37%",
        },
        {
            "slug": "northwind",
            "company": "Northwind Commerce",
            "headline": "2x more signal from marketing assignments.",
            "result": "Introduced scenario prompts + integrity signals for remote candidates.",
            "metric_label": "Signal depth",
            "metric_value": "2x",
        },
        {
            "slug": "aster",
            "company": "Aster Care",
            "headline": "Candidate NPS jumped to 4.9 / 5.",
            "result": "Behavioral inventory + guided portal kept clinical leaders engaged.",
            "metric_label": "Candidate CSAT",
            "metric_value": "4.9",
        },
    ]

    articles = list(
        BlogPost.objects.published().order_by("-is_featured", "-published_at")[:3]
    )

    testimonials = [
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
            "avatar": "img/avatar-lauren.svg",
        },
        {
            "name": "Priya",
            "role": "Head of Talent, Aster Care",
            "quote": "Auto scoring shaved days off each search. Candidates stay informed while our team sees a clear, auditable shortlist.",
            "avatar": "img/avatar-savannah.svg",
        },
    ]

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
            "features": features,
            "suite": assessment_suite,
            "articles": articles,
            "testimonials": testimonials,
            "invite_form": form,
            "live_events": live_events,
            "case_studies": case_studies,
        },
    )
