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
        "badge": "Built for modern hiring teams",
        "title": "Run <span class=\"highlight\">marketing, product, and behavioral</span> assessments in one simple workspace.",
        "subtitle": "Evalon gives recruiting teams ready-made skill tests, live progress tracking, and plain-language scorecards so everyone understands each candidate.",
        "primary_label": "Get started",
        "primary_url": "#cta",
        "secondary_label": "See platform tour",
        "secondary_url": "#suite",
    }

    suite_heading = {
        "title": "Choose the right assessment for every role.",
        "subtitle": "Curated banks cover marketing, product, and leadership roles with fresh prompts, scoring guides, and downloadable rubrics.",
        "instructions": "Tap a card to check the metrics or grab the rubric.",
    }

    assessment_suite = [
        {
            "slug": "marketing",
            "label": "Marketing IQ",
            "title": "Digital marketing",
            "summary": "Real scenarios covering paid media, SEO, analytics, and copywriting.",
            "focus": ["Paid media", "SEO", "Analytics"],
            "stats": [
                {"label": "Question bank", "value": "40 real scenes"},
                {"label": "Avg completion", "value": "32 minutes"},
                {"label": "Benchmarks", "value": "Marketing & growth roles"},
            ],
        },
        {
            "slug": "product",
            "label": "Product Sense",
            "title": "Product management",
            "summary": "Hands-on reasoning, estimation, prioritization, and UX critiques for PM hires.",
            "focus": ["Prioritization", "Estimation", "UX critique"],
            "stats": [
                {"label": "Prompt mix", "value": "Reasoning + scenario"},
                {"label": "Difficulty", "value": "Adjusts by seniority"},
                {"label": "Perspectives", "value": "Power-user & broad view"},
            ],
        },
        {
            "slug": "behavioral",
            "label": "Behavioral DNA",
            "title": "Leadership & soft skills",
            "summary": "Short reflections that show teamwork style, risk comfort, and coaching needs.",
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
            "title": "Plan each assignment",
            "description": "Match a role to a template or create your own in minutes.",
            "panel_title": "Assessment designer",
            "panel_subtitle": "Pick the skills, attach examples, and set due dates before sending invites.",
            "panel_points": [
                "Start from 25+ ready-made templates or copy the ones you love.",
                "Choose reviewers, reminders, and file requirements in a friendly form.",
                "Collect uploads, screen recordings, or written answers in one place.",
            ],
        },
        {
            "slug": "invite",
            "title": "Invite & align",
            "description": "Send a clear briefing to every candidate and collaborator.",
            "panel_title": "Branded candidate briefing",
            "panel_subtitle": "Each invite includes a branded page with rules, a timeline, and a start button.",
            "panel_points": [
                "Personalized landing page with recruiter notes and FAQs.",
                "Live status signals show when invites are opened, started, or submitted.",
                "Secure share links for hiring panels, agencies, or hiring managers.",
            ],
        },
        {
            "slug": "score",
            "title": "Score automatically",
            "description": "Translate responses into ranked shortlists with zero spreadsheets.",
            "panel_title": "Scoring console",
            "panel_subtitle": "Structured rubrics and bias controls show how each person performed.",
            "panel_points": [
                "Score per question with calibration tips everyone can follow.",
                "Set auto-advance rules when someone hits a standout score.",
                "Share summary packs with hiring managers instantly.",
            ],
        },
        {
            "slug": "decide",
            "title": "Decide & hand off",
            "description": "Advance winners to interviews or offers with context for the team.",
            "panel_title": "Decision workspace",
            "panel_subtitle": "Log the why, notify candidates, and sync everything to your ATS without copy-paste.",
            "panel_points": [
                "Advance or decline with pre-written, editable messages.",
                "Share highlight reels and prep notes for interviewers.",
                "Automatic audit trail keeps every reviewer action documented.",
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
            "result": "Centralized PM tests with auto scoring and a simple highlight reel for interviewers.",
            "metric_label": "Hiring speed",
            "metric_value": "-37%",
        },
        {
            "slug": "northwind",
            "company": "Northwind Commerce",
            "headline": "2x more signal from marketing assignments.",
            "result": "Scenario prompts plus honesty checks gave remote candidates a fair shot.",
            "metric_label": "Signal depth",
            "metric_value": "2x",
        },
        {
            "slug": "aster",
            "company": "Aster Care",
            "headline": "Candidate NPS jumped to 4.9 / 5.",
            "result": "Behavioral reflections and a guided portal kept clinical leaders engaged.",
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
            "role": "Founder, Hailo",
            "quote": "Evalon replaced messy docs with one calm workspace. Every teammate knows what a great submission looks like.",
            "avatar": "img/avatar-savannah.svg",
        },
        {
            "name": "Marcus",
            "role": "VP People, Copper Build",
            "quote": "Our pods scope projects, invite candidates, and move finalists without leaving Evalon. Offers now go out days faster.",
            "avatar": "img/avatar-lauren.svg",
        },
        {
            "name": "Priya",
            "role": "Head of Talent, Aster Care",
            "quote": "Auto scoring shaved days off each search. Candidates stay informed while our team sees a clear shortlist we can trust.",
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
            "description": "Try Evalon with two active roles and a small pool of candidates.",
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
            "description": "Run multiple searches with richer reporting and simple branding.",
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
            "slug": "enterprise",
            "badge": "Custom",
            "name": "Enterprise",
            "price": "Custom",
            "frequency": "contact us",
            "description": "Unlimited projects and invites, tailor-made assessments, SSO, and hands-on rollout.",
            "projects": "Unlimited projects",
            "invites": "Unlimited invites",
            "overage": None,
            "cta_label": "Request a quote",
            "cta_url": reverse("pages:contact"),
            "highlighted": False,
            "features": [
                "Dedicated CSM + success playbooks",
                "Custom assessments & security reviews",
                "SLA, SSO/SAML, and SOC 2 readiness",
            ],
        },
    ]

    pricing_helper = {
        "headline": "Clear pricing for every hiring plan.",
        "subline": "Each plan includes the assessments and invites you need. Upgrade or add invites whenever your team grows.",
        "footnote": "All paid plans include unlimited reviewers. Save 20% with annual billing on Pro.",
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
            "lede": "Whether you’re evaluating Evalon, onboarding a team, or requesting a security review, we’ll route you to the right humans.",
        },
        "sections": [
            {
                "badge": "Sales & demos",
                "title": "hello@evalon.so",
                "body": "Replies within 1 business day.",
                "list": [
                    "Live product walkthroughs",
                    "Pricing & implementation help",
                    "Vendor security responses",
                ],
            },
            {
                "badge": "Support",
                "title": "support@evalon.so",
                "body": "Replies within 4 business hours.",
                "list": [
                    "Assessment troubleshooting",
                    "Candidate portal assistance",
                    "Account & billing changes",
                ],
            },
            {
                "badge": "Partnerships",
                "title": "partners@evalon.so",
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
                "title": "security@evalon.so",
                "body": "Visit https://status.evalon.so for live uptime. Email us for questionnaires or penetration test reports.",
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
            "lede": "Evalon handles candidate responses and hiring notes with care. Here’s how we collect, use, and protect your information.",
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
                "title": "Operate & improve Evalon",
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
                    "Customers can export, modify, or delete data via the admin console or by contacting privacy@evalon.so.",
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
            "lede": "By using Evalon, you agree to the principles below. Reach out if you need a signed copy or custom language.",
        },
        "sections": [
            {
                "badge": "Use of the service",
                "title": "License",
                "body": "Evalon grants you a non-exclusive, revocable license to use the platform for internal hiring purposes. You agree to safeguard candidate data and comply with all applicable laws.",
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
