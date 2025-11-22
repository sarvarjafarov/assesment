from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django import forms
from django.utils.text import slugify

from assessments.forms import AssessmentInviteForm
from assessments.services import send_invite_email
from blog.models import BlogPost
from console.models import SiteContentBlock, ResourceAsset

def home(request):
    """Render the marketing landing page."""
    hero_content = {
        "badge": "Purpose-built for <span>B2B hiring</span>",
        "title": "Launch <span class=\"highlight\">marketing, PM, and behavioral</span> assessments from one console.",
        "subtitle": "Sira calibrates every assignment for B2B hiring—scope roles, benchmark real work, and share a defensible report with stakeholders in under an hour.",
        "primary_label": "Book a walkthrough",
        "primary_url": "#cta",
        "secondary_label": "See reporting tour",
        "secondary_url": "#suite",
    }

    suite_heading = {
        "title": "Pick the right instrument for every role.",
        "subtitle": "Three calibrated banks cover GTM, product, and leadership signals—each with fresh questions, scoring rubrics, and reporting templates.",
        "instructions": "Select a card to see scoring metrics & download the rubric.",
    }

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

    pricing_tiers = [
        {
            "slug": "starter",
            "badge": "Free",
            "name": "Starter",
            "price": "$0",
            "frequency": "Forever",
            "description": "Test Sira with two active roles and a handful of candidates.",
            "projects": "2 active projects",
            "invites": "20 invites / month",
            "overage": None,
            "cta_label": "Create free account",
            "cta_url": reverse("clients:signup"),
            "highlighted": False,
            "features": [
                "Marketing, PM, and behavioral banks",
                "Basic reports & CSV export",
                "Email support",
            ],
        },
        {
            "slug": "pro",
            "badge": "Most popular",
            "name": "Pro",
            "price": "$59",
            "frequency": "per month",
            "description": "Run multiple searches with richer reporting and branding.",
            "projects": "10 active projects",
            "invites": "250 invites / month",
            "overage": "$0.40 per additional invite",
            "cta_label": "Start Pro trial",
            "cta_url": reverse("clients:signup"),
            "highlighted": True,
            "features": [
                "Pipeline kanban & top-candidate spotlights",
                "Custom branding + shareable reports",
                "Priority chat + email support",
            ],
        },
        {
            "slug": "growth",
            "badge": "Scale teams",
            "name": "Growth",
            "price": "$149",
            "frequency": "per month",
            "description": "For in-house talent teams rolling assessments across departments.",
            "projects": "25 active projects",
            "invites": "750 invites / month",
            "overage": "$0.30 per additional invite",
            "cta_label": "Talk to sales",
            "cta_url": "#cta",
            "highlighted": False,
            "features": [
                "Advanced analytics & integrity signals",
                "API access + multi-role permissions",
                "Dedicated onboarding specialist",
            ],
        },
        {
            "slug": "enterprise",
            "badge": "Custom",
            "name": "Enterprise",
            "price": "Custom",
            "frequency": "contact us",
            "description": "Unlimited projects and invites, bespoke assessments, SSO, and white-glove rollout.",
            "projects": "Unlimited projects",
            "invites": "Unlimited invites",
            "overage": None,
            "cta_label": "Request a quote",
            "cta_url": reverse("pages:contact"),
            "highlighted": False,
            "features": [
                "Dedicated CSM + success playbooks",
                "Bespoke assessments & security reviews",
                "SLA, SSO/SAML, and SOC 2 readiness",
            ],
        },
    ]

    pricing_helper = {
        "headline": "Simple pricing that scales with your searches.",
        "subline": "Plans anchor around active projects and included invites. Upgrade any time or add extra invites in-product.",
        "footnote": "All paid plans include unlimited reviewers. Save 20% with annual billing on Pro and Growth.",
    }

    # Apply CMS overrides if blocks exist
    hero_block = (
        SiteContentBlock.objects.filter(
            page=SiteContentBlock.PAGE_HOME, slot=SiteContentBlock.SLOT_HERO, is_active=True
        )
        .order_by("order")
        .first()
    )
    if hero_block:
        hero_content.update(
            {
                "badge": hero_block.badge or hero_content["badge"],
                "title": hero_block.title or hero_content["title"],
                "subtitle": hero_block.body or hero_content["subtitle"],
                "primary_label": hero_block.cta_label or hero_content["primary_label"],
                "primary_url": hero_block.cta_url or hero_content["primary_url"],
                "secondary_label": hero_block.secondary_cta_label or hero_content["secondary_label"],
                "secondary_url": hero_block.secondary_cta_url or hero_content["secondary_url"],
            }
        )

    heading_block = (
        SiteContentBlock.objects.filter(
            page=SiteContentBlock.PAGE_HOME,
            slot=SiteContentBlock.SLOT_SUITE_HEADING,
            is_active=True,
        )
        .order_by("order")
        .first()
    )
    if heading_block:
        suite_heading.update(
            {
                "title": heading_block.title or suite_heading["title"],
                "subtitle": heading_block.body or suite_heading["subtitle"],
                "instructions": heading_block.cta_label or suite_heading["instructions"],
            }
        )

    suite_blocks = SiteContentBlock.objects.filter(
        page=SiteContentBlock.PAGE_HOME, slot=SiteContentBlock.SLOT_SUITE, is_active=True
    ).order_by("order")
    if suite_blocks:
        assessment_suite = [
            {
                "slug": slugify(block.title) or f"suite-{block.pk}",
                "label": block.badge or block.title,
                "title": block.title,
                "summary": block.body,
                "focus": block.list_values(),
                "stats": block.meta_pairs(),
            }
            for block in suite_blocks
        ]

    feature_blocks = SiteContentBlock.objects.filter(
        page=SiteContentBlock.PAGE_HOME, slot=SiteContentBlock.SLOT_FEATURE, is_active=True
    ).order_by("order")
    if feature_blocks:
        features = [
            {
                "slug": slugify(block.title) or f"feature-{block.pk}",
                "title": block.title,
                "description": block.body,
                "panel_title": block.subtitle or block.title,
                "panel_subtitle": block.cta_label,
                "panel_points": block.list_values(),
            }
            for block in feature_blocks
        ]

    testimonial_blocks = SiteContentBlock.objects.filter(
        page=SiteContentBlock.PAGE_HOME, slot=SiteContentBlock.SLOT_TESTIMONIAL, is_active=True
    ).order_by("order")
    if testimonial_blocks:
        testimonials = [
            {
                "name": block.title,
                "role": block.subtitle,
                "quote": block.body,
                "avatar": block.cta_url or "img/avatar-savannah.svg",
            }
            for block in testimonial_blocks
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
            "suite_heading": suite_heading,
            "articles": articles,
            "testimonials": testimonials,
            "pricing_tiers": pricing_tiers,
            "pricing_helper": pricing_helper,
            "hero_content": hero_content,
            "invite_form": form,
            "live_events": live_events,
            "case_studies": case_studies,
        },
    )


def contact(request):
    fallback = {
        "hero": {
            "eyebrow": "Contact us",
            "title": "We respond faster than most ticket portals.",
            "lede": "Whether you’re evaluating Sira, onboarding a team, or requesting a security review, we’ll route you to the right humans.",
        },
        "sections": [
            {
                "badge": "Sales & demos",
                "title": "hello@sira.so",
                "body": "Replies within 1 business day.",
                "list": [
                    "Live product walkthroughs",
                    "Pricing & implementation help",
                    "Vendor security responses",
                ],
            },
            {
                "badge": "Support",
                "title": "support@sira.so",
                "body": "Replies within 4 business hours.",
                "list": [
                    "Assessment troubleshooting",
                    "Candidate portal assistance",
                    "Account & billing changes",
                ],
            },
            {
                "badge": "Partnerships",
                "title": "partners@sira.so",
                "body": "Replies within 2 business days.",
                "list": [
                    "ATS & HRIS integrations",
                    "Research collaborations",
                    "Content & event requests",
                ],
            },
            {
                "badge": "Headquarters",
                "title": "85 2nd Street, San Francisco, CA 94105",
                "body": "Monday–Friday · 9am–6pm PT · +1 (415) 555-0143",
            },
        ],
    }
    return render(
        request,
        "pages/page_builder.html",
        _page_builder_context(SiteContentBlock.PAGE_CONTACT, fallback),
    )


def careers(request):
    fallback = {
        "hero": {
            "eyebrow": "Careers",
            "title": "Build assessment infrastructure hiring teams actually love.",
            "lede": "We’re a distributed team of builders, researchers, and talent nerds shipping fast and supporting each other along the way.",
        },
        "sections": [
            {
                "badge": "Values",
                "title": "Ship with empathy",
                "body": "We build around the candidate experience and respect the time of every recruiter.",
            },
            {
                "badge": "Values",
                "title": "Bias-aware decisions",
                "body": "We hold ourselves to the same standard we enable: structured, fair assessment.",
            },
            {
                "badge": "Values",
                "title": "Progress over polish",
                "body": "We launch thoughtful experiments weekly and learn fast.",
            },
            {
                "badge": "Benefits",
                "title": "Designed for focus and longevity.",
                "list": [
                    "Fully remote with quarterly in-person team weeks",
                    "Competitive equity, 401(k) match, & learning stipend",
                    "12 weeks paid parental leave + flexible time off",
                ],
            },
        ],
    }
    return render(
        request,
        "pages/page_builder.html",
        _page_builder_context(SiteContentBlock.PAGE_CAREERS, fallback),
    )


def security(request):
    fallback = {
        "hero": {
            "eyebrow": "Security",
            "title": "Assessment data deserves enterprise-grade safeguards.",
            "lede": "From SOC 2 controls to proactive monitoring, we treat candidate responses and hiring signals like the crown jewels.",
        },
        "sections": [
            {
                "badge": "Trust & compliance",
                "title": "Audited controls",
                "list": [
                    "SOC 2 Type II controls, audited annually",
                    "GDPR-ready data processing agreements",
                    "SSO via Okta, Azure AD, and Google Workspace",
                ],
            },
            {
                "badge": "Data protection",
                "title": "Encryption + retention",
                "list": [
                    "Encryption in transit (TLS 1.3) and at rest (AES-256)",
                    "Hourly backups with 35-day retention",
                    "Role-based permissions with audit trails",
                ],
            },
            {
                "badge": "Product security",
                "title": "Testing + disclosure",
                "list": [
                    "Feature flags + staged rollouts to reduce risk",
                    "Independent penetration testing twice per year",
                    "Responsible disclosure program for researchers",
                ],
            },
            {
                "badge": "Need to report something?",
                "title": "security@sira.so",
                "body": "Visit https://status.sira.so for live uptime. Email us for questionnaires or penetration test reports.",
            },
        ],
    }
    return render(
        request,
        "pages/page_builder.html",
        _page_builder_context(SiteContentBlock.PAGE_SECURITY, fallback),
    )


def privacy(request):
    fallback = {
        "hero": {
            "eyebrow": "Privacy Policy",
            "title": "Your data belongs to you.",
            "lede": "Sira handles candidate responses and hiring notes with care. Here’s how we collect, use, and protect your information.",
        },
        "sections": [
            {
                "badge": "What we collect",
                "title": "Minimal data for assessments",
                "list": [
                    "Account data (name, email, role) when customers onboard.",
                    "Assessment activity (timestamps, reviewer notes) stored for 24 months by default.",
                    "Platform telemetry (browser, device, IP) used for security and performance.",
                ],
            },
            {
                "badge": "How we use data",
                "title": "Operate & improve Sira",
                "list": [
                    "Deliver assessment experiences and share results with authorized users.",
                    "Improve scoring models and product workflows.",
                    "Communicate updates, notify candidates, and provide support.",
                ],
            },
            {
                "badge": "Your rights",
                "title": "Control your data",
                "list": [
                    "Customers can export, modify, or delete data via the admin console or by contacting privacy@sira.so.",
                    "We enter DPAs and SCCs upon request.",
                    "Data residency options are available for enterprise plans.",
                ],
            },
        ],
    }
    return render(
        request,
        "pages/page_builder.html",
        _page_builder_context(SiteContentBlock.PAGE_PRIVACY, fallback),
    )


def terms(request):
    fallback = {
        "hero": {
            "eyebrow": "Terms of Service",
            "title": "The legal bits, written for humans.",
            "lede": "By using Sira, you agree to the principles below. Reach out if you need a signed copy or custom language.",
        },
        "sections": [
            {
                "badge": "Use of the service",
                "title": "License",
                "body": "Sira grants you a non-exclusive, revocable license to use the platform for internal hiring purposes. You agree to safeguard candidate data and comply with all applicable laws.",
            },
            {
                "badge": "Payment & renewal",
                "title": "Billing",
                "body": "Subscription fees are invoiced annually unless otherwise agreed. Plans auto-renew unless canceled in writing 30 days prior to renewal.",
            },
            {
                "badge": "Limitation of liability",
                "title": "Liability cap",
                "body": "Our total liability will not exceed fees paid in the prior 12 months. We are not liable for consequential or indirect damages.",
            },
            {
                "badge": "Termination",
                "title": "Data & access",
                "body": "Either party may terminate for material breach with 30 days’ notice. Upon termination, you may export your data for 30 days.",
            },
        ],
    }
    return render(
        request,
        "pages/page_builder.html",
        _page_builder_context(SiteContentBlock.PAGE_TERMS, fallback),
    )


def resources(request):
    fallback = {
        "hero": {
            "eyebrow": "Resources",
            "title": "Download-ready playbooks for hiring teams.",
            "lede": "Guides and templates we share with customers during assessments, now available to you.",
        },
    }
    context = _page_builder_context(SiteContentBlock.PAGE_RESOURCES, fallback)
    assets = ResourceAsset.objects.filter(is_active=True).order_by("order")
    context["assets"] = assets
    return render(request, "pages/resources.html", context)


def _page_builder_context(page_slug, fallback):
    hero_block = (
        SiteContentBlock.objects.filter(page=page_slug, slot=SiteContentBlock.SLOT_PAGE_HERO, is_active=True)
        .order_by("order")
        .first()
    )
    hero = {
        "eyebrow": fallback["hero"].get("eyebrow"),
        "title": fallback["hero"].get("title"),
        "lede": fallback["hero"].get("lede"),
    }
    if hero_block:
        hero.update(
            {
                "eyebrow": hero_block.badge or hero["eyebrow"],
                "title": hero_block.title or hero["title"],
                "lede": hero_block.body or hero["lede"],
            }
        )
    section_blocks = SiteContentBlock.objects.filter(
        page=page_slug, slot=SiteContentBlock.SLOT_PAGE_SECTION, is_active=True
    ).order_by("order")
    if section_blocks:
        sections = [
            {
                "badge": block.badge,
                "title": block.title,
                "body": block.body,
                "list": block.list_values(),
                "meta": block.meta_pairs(),
                "cta_label": block.cta_label,
                "cta_url": block.cta_url,
            }
            for block in section_blocks
        ]
    else:
        sections = fallback.get("sections", [])
    return {"hero": hero, "sections": sections}
