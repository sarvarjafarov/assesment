import json

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django import forms
from django.utils.text import slugify
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404

from blog.models import BlogPost
from console.models import SiteContentBlock, ResourceAsset
from .forms import DemoRequestForm
from django.db.models import Count, Prefetch
from .models import NewsletterSubscriber, PublicAssessment, Role, InterviewQuestion

def home(request):
    """Render the marketing landing page."""
    hero_content = {
        "badge": "Hiring Assessment Platform",
        "title": "Hire better candidates with",
        "title_accent": "structured assessments",
        "subtitle": "Pre-built skill tests for every role \u2014 with automated scoring, progress tracking, and reports your team can trust.",
        "primary_label": "Get Started Free",
        "primary_url": reverse("clients:signup"),
        "secondary_link_label": "See how it works \u2192",
        "secondary_link_url": "#how-it-works",
    }

    suite_heading = {
        "title": "Assessments for every role",
        "subtitle": "Six ready-made question banks with scoring rubrics and real-world scenarios.",
        "instructions": "Click any assessment to see sample questions and download the scoring rubric.",
    }

    assessment_suite = [
        {
            "slug": "marketing",
            "label": "Marketing IQ",
            "title": "Digital Marketing",
            "summary": "Paid media, SEO, analytics, and copywriting scenarios.",
            "duration": "32 min",
        },
        {
            "slug": "product",
            "label": "Product Sense",
            "title": "Product Management",
            "summary": "Reasoning, estimation, prioritization, and UX critiques.",
            "duration": "30 min",
        },
        {
            "slug": "behavioral",
            "label": "Behavioral DNA",
            "title": "Leadership & Culture",
            "summary": "Teamwork style, risk comfort, and coaching reflections.",
            "duration": "15 min",
        },
        {
            "slug": "ux_design",
            "label": "Design Eye",
            "title": "UX/UI Design",
            "summary": "User research, interaction design, and accessibility.",
            "duration": "35 min",
        },
        {
            "slug": "hr",
            "label": "People Ops",
            "title": "HR & People Strategy",
            "summary": "Talent acquisition, compliance, and people strategy.",
            "duration": "35 min",
        },
        {
            "slug": "finance",
            "label": "Finance IQ",
            "title": "Finance Management",
            "summary": "Budgeting, risk management, and strategic finance.",
            "duration": "35 min",
        },
    ]

    features = [
        {
            "slug": "create",
            "title": "Create project",
            "description": "Pick an assessment, set deadlines, and customize instructions in minutes.",
        },
        {
            "slug": "invite",
            "title": "Invite candidates",
            "description": "Candidates get a clear email with a link to start at their own pace.",
        },
        {
            "slug": "review",
            "title": "Auto-score & review",
            "description": "Structured rubrics score every submission so you can compare side-by-side.",
        },
        {
            "slug": "decide",
            "title": "Make decisions",
            "description": "Download clean reports and track all hiring decisions in one place.",
        },
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

    testimonials = [
        {
            "name": "Marcus Chen",
            "role": "VP of People, Copper Build",
            "company": "Copper Build",
            "quote": "Evalon cut our marketing hiring cycle from 3 weeks to 12 days. The automated scoring meant we could focus on top candidates instead of reviewing every submission manually.",
            "metric": "60% faster hiring",
            "avatar": "img/avatar-lauren.svg",
        },
        {
            "name": "Priya Sharma",
            "role": "Head of Talent, Aster Care",
            "company": "Aster Care",
            "quote": "Our candidates actually enjoy the process now. The clear instructions and progress tracking reduced our drop-off rate by half.",
            "metric": "50% better completion",
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
                "All 6 assessment banks included",
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
        "headline": "Simple, transparent pricing",
        "subline": "Start free, upgrade when you need more projects and invites. All plans include all six assessment types.",
        "footnote": "All plans include unlimited team members. Annual billing saves 20% on Pro plan.",
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
                # title_accent not yet CMS-overridable
                "subtitle": hero_block.body or hero_content["subtitle"],
                "primary_label": hero_block.cta_label or hero_content["primary_label"],
                "primary_url": hero_block.cta_url or hero_content["primary_url"],
                "secondary_link_label": hero_block.secondary_cta_label or hero_content["secondary_link_label"],
                "secondary_link_url": hero_block.secondary_cta_url or hero_content["secondary_link_url"],
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

    # Try database-driven assessments first
    db_assessments = PublicAssessment.objects.filter(
        is_active=True, is_featured=True
    ).order_by('order')[:6]
    if db_assessments.exists():
        assessment_suite = [
            {
                "slug": a.slug,
                "label": a.label,
                "title": a.title,
                "summary": a.summary,
                "focus": a.focus_list,
                "stats": a.stats if isinstance(a.stats, list) else [],
                "icon_svg": a.icon_svg,
                "url": a.get_absolute_url(),
            }
            for a in db_assessments
        ]
    else:
        # Fallback to SiteContentBlock CMS overrides
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
        form = DemoRequestForm(request.POST)
        if form.is_valid():
            demo_request = form.save()
            messages.success(
                request,
                f"Thanks {demo_request.full_name.split()[0]}! We've received your demo request and will be in touch within 1 business day.",
            )
            return redirect(f"{reverse('pages:home')}#cta")
    else:
        form = DemoRequestForm()

    return render(
        request,
        "pages/home.html",
        {
            "features": features,
            "suite": assessment_suite,
            "suite_heading": suite_heading,
            "testimonials": testimonials,
            "pricing_tiers": pricing_tiers,
            "pricing_helper": pricing_helper,
            "hero_content": hero_content,
            "invite_form": form,
            "case_studies": case_studies,
        },
    )


def pricing(request):
    tiers = [
        {
            "slug": "starter",
            "name": "Starter",
            "price": "$0",
            "frequency": "forever",
            "desc": "Try Evalon with two active roles and a small candidate pool.",
            "limits": "2 projects · 20 invites/mo",
            "cta_label": "Create free account",
            "cta_url": reverse("clients:signup"),
            "highlighted": False,
            "features": [
                "All 6 assessment banks",
                "Up to 2 active projects",
                "20 candidate invites per month",
                "Basic score reports",
                "CSV export",
                "Email support",
            ],
        },
        {
            "slug": "pro",
            "name": "Pro",
            "price": "$59",
            "frequency": "per month",
            "desc": "Run multiple searches with richer reporting, branding, and pipeline tools.",
            "limits": "10 projects · 250 invites/mo",
            "cta_label": "Start 14-day free trial",
            "cta_url": reverse("clients:signup"),
            "highlighted": True,
            "features": [
                "Everything in Starter, plus:",
                "Up to 10 active projects",
                "250 candidate invites per month",
                "Pipeline kanban & top-candidate spotlights",
                "Custom branding & shareable reports",
                "Overage at $0.40 per extra invite",
                "Priority chat & email support",
            ],
        },
        {
            "slug": "enterprise",
            "name": "Enterprise",
            "price": "Custom",
            "frequency": "contact us",
            "desc": "Unlimited everything, tailor-made assessments, SSO, and hands-on rollout.",
            "limits": "Unlimited projects & invites",
            "cta_label": "Request a quote",
            "cta_url": reverse("pages:contact"),
            "highlighted": False,
            "features": [
                "Everything in Pro, plus:",
                "Unlimited projects & invites",
                "Custom assessment design",
                "Dedicated customer success manager",
                "SSO / SAML integration",
                "SLA guarantee & SOC 2 readiness",
                "Full API access",
                "On-site training & rollout support",
            ],
        },
    ]

    comparison = [
        {"feature": "Active projects", "starter": "2", "pro": "10", "enterprise": "Unlimited"},
        {"feature": "Monthly invites", "starter": "20", "pro": "250", "enterprise": "Unlimited"},
        {"feature": "All 6 assessment banks", "starter": True, "pro": True, "enterprise": True},
        {"feature": "Basic score reports", "starter": True, "pro": True, "enterprise": True},
        {"feature": "CSV export", "starter": True, "pro": True, "enterprise": True},
        {"feature": "Pipeline kanban", "starter": False, "pro": True, "enterprise": True},
        {"feature": "Top-candidate spotlights", "starter": False, "pro": True, "enterprise": True},
        {"feature": "Custom branding", "starter": False, "pro": True, "enterprise": True},
        {"feature": "Shareable reports", "starter": False, "pro": True, "enterprise": True},
        {"feature": "Priority support", "starter": False, "pro": True, "enterprise": True},
        {"feature": "Custom assessments", "starter": False, "pro": False, "enterprise": True},
        {"feature": "SSO / SAML", "starter": False, "pro": False, "enterprise": True},
        {"feature": "Dedicated CSM", "starter": False, "pro": False, "enterprise": True},
        {"feature": "SLA guarantee", "starter": False, "pro": False, "enterprise": True},
        {"feature": "API access", "starter": False, "pro": False, "enterprise": True},
        {"feature": "On-site training", "starter": False, "pro": False, "enterprise": True},
    ]

    assessments = [
        {"name": "Marketing", "desc": "Paid media, SEO, analytics, and campaign strategy."},
        {"name": "Product Management", "desc": "Strategy, execution, roadmaps, and product sense."},
        {"name": "Behavioral", "desc": "Psychometric-backed signals for culture and role fit."},
        {"name": "UX/UI Design", "desc": "User research, interaction design, and prototyping."},
        {"name": "HR", "desc": "Talent acquisition, employee relations, and compliance."},
        {"name": "Finance", "desc": "Financial planning, budgeting, and analysis."},
    ]

    faqs = [
        {
            "q": "Can I switch plans at any time?",
            "a": "Yes. Upgrade or downgrade whenever you like — changes take effect on your next billing cycle. If you upgrade mid-cycle, we prorate the difference.",
        },
        {
            "q": "What happens when I exceed my invite limit?",
            "a": "On the Pro plan, additional invites cost $0.40 each. On the Starter plan, you'll need to wait for next month's refresh or upgrade to Pro.",
        },
        {
            "q": "Do all plans include all 6 assessment types?",
            "a": "Yes. Every plan — including the free Starter — gives you access to all six assessment banks: Marketing, Product, Behavioral, UX/UI, HR, and Finance.",
        },
        {
            "q": "Is there a discount for annual billing?",
            "a": "Yes. Annual billing on the Pro plan saves you 20%, bringing the price to $47/month billed annually.",
        },
        {
            "q": "What payment methods do you accept?",
            "a": "We accept all major credit cards (Visa, Mastercard, Amex) and can arrange invoicing for Enterprise customers.",
        },
        {
            "q": "Can I cancel anytime?",
            "a": "Absolutely. There are no long-term contracts. Cancel from your dashboard settings and you'll retain access until the end of your current billing period.",
        },
        {
            "q": "How does the free trial work?",
            "a": "The Pro trial gives you full Pro features for 14 days. No credit card required. At the end of the trial, you can subscribe or revert to the Starter plan.",
        },
        {
            "q": "Is my data secure?",
            "a": "Yes. We use AES-256 encryption at rest, TLS 1.3 in transit, and undergo regular third-party security audits. Enterprise customers can request our SOC 2 report.",
        },
    ]

    return render(request, "pages/pricing.html", {
        "active": "pricing",
        "tiers": tiers,
        "comparison": comparison,
        "assessments": assessments,
        "faqs": faqs,
    })


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


@csrf_exempt
@require_POST
def newsletter_subscribe(request):
    """Handle newsletter subscription via AJAX."""
    try:
        data = json.loads(request.body)
        email = data.get("email", "").strip().lower()
    except (json.JSONDecodeError, AttributeError):
        email = request.POST.get("email", "").strip().lower()

    if not email:
        return JsonResponse({"success": False, "error": "Email is required."}, status=400)

    # Basic email validation
    if "@" not in email or "." not in email.split("@")[-1]:
        return JsonResponse({"success": False, "error": "Please enter a valid email."}, status=400)

    # Check if already subscribed
    existing = NewsletterSubscriber.objects.filter(email=email).first()
    if existing:
        if existing.status == "active":
            return JsonResponse({
                "success": True,
                "message": "You're already subscribed! Thanks for being part of our community."
            })
        else:
            # Reactivate subscription
            existing.status = "active"
            existing.unsubscribed_at = None
            existing.save(update_fields=["status", "unsubscribed_at"])
            return JsonResponse({
                "success": True,
                "message": "Welcome back! Your subscription has been reactivated."
            })

    # Create new subscription
    source = data.get("source", "footer") if isinstance(data, dict) else "footer"
    NewsletterSubscriber.objects.create(email=email, source=source)

    return JsonResponse({
        "success": True,
        "message": "Thanks for subscribing! You'll receive monthly updates on product releases and hiring best practices."
    })


@require_GET
@cache_page(60 * 60 * 24)  # Cache for 24 hours
def robots_txt(request):
    """
    Generate robots.txt for search engine crawlers.
    Includes sitemap location and disallows private areas.
    """
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "# Private areas",
        "Disallow: /admin/",
        "Disallow: /console/",
        "Disallow: /clients/",
        "Disallow: /candidate/",
        "Disallow: /api/",
        "Disallow: /accounts/",
        "",
        "# Sitemap",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def assessment_list(request):
    """List all active public assessments with search."""
    assessments = PublicAssessment.objects.filter(is_active=True)

    query = request.GET.get('q', '').strip()
    if query:
        assessments = assessments.filter(
            Q(title__icontains=query) |
            Q(label__icontains=query) |
            Q(summary__icontains=query) |
            Q(description__icontains=query)
        ).distinct()

    paginator = Paginator(assessments, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'pages/assessments/list.html', {
        'assessments': page_obj,
        'page_obj': page_obj,
        'query': query,
        'is_paginated': page_obj.has_other_pages(),
    })


def assessment_detail(request, slug):
    """Display detailed public assessment information."""
    assessment = get_object_or_404(PublicAssessment, slug=slug, is_active=True)

    # Get related assessments (excluding current)
    related = PublicAssessment.objects.filter(
        is_active=True
    ).exclude(pk=assessment.pk).order_by('order')[:4]

    return render(request, 'pages/assessments/detail.html', {
        'assessment': assessment,
        'related_assessments': related,
    })


def assessment_preview(request, slug, token):
    """Preview assessment before publishing (requires valid token or staff)."""
    try:
        assessment = PublicAssessment.objects.get(slug=slug)
    except PublicAssessment.DoesNotExist:
        raise Http404

    # Check token or staff access
    if str(assessment.preview_key) != str(token) and not request.user.is_staff:
        raise Http404

    related = PublicAssessment.objects.filter(
        is_active=True
    ).exclude(pk=assessment.pk).order_by('order')[:4]

    return render(request, 'pages/assessments/detail.html', {
        'assessment': assessment,
        'related_assessments': related,
        'preview_mode': True,
    })


# ── Programmatic SEO: Interview Questions ──────────────────────────


def interview_questions_list(request):
    """List all roles that have interview questions."""
    roles = Role.objects.filter(
        is_active=True,
        interview_questions__is_active=True,
    ).annotate(
        question_count=Count(
            'interview_questions',
            filter=Q(interview_questions__is_active=True),
        )
    ).filter(question_count__gt=0).distinct()

    department = request.GET.get('department', '').strip()
    if department:
        roles = roles.filter(department__iexact=department)

    query = request.GET.get('q', '').strip()
    if query:
        roles = roles.filter(
            Q(title__icontains=query)
            | Q(department__icontains=query)
            | Q(description__icontains=query)
        )

    departments = (
        Role.objects.filter(is_active=True)
        .values_list('department', flat=True)
        .distinct()
        .order_by('department')
    )

    paginator = Paginator(roles, 24)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'pages/interview_questions/list.html', {
        'roles': page_obj,
        'page_obj': page_obj,
        'query': query,
        'department': department,
        'departments': departments,
        'is_paginated': page_obj.has_other_pages(),
    })


def interview_questions_detail(request, slug):
    """Show interview questions for a specific role."""
    role = get_object_or_404(Role, slug=slug, is_active=True)

    questions = (
        role.interview_questions.filter(is_active=True)
        .select_related('assessment_type')
        .order_by('category', 'order')
    )

    # Group questions by category
    categories = {}
    for q in questions:
        cat_display = q.get_category_display()
        if cat_display not in categories:
            categories[cat_display] = []
        categories[cat_display].append(q)

    # Related roles: same department, have questions
    related_roles = (
        Role.objects.filter(
            is_active=True,
            department=role.department,
            interview_questions__is_active=True,
        )
        .exclude(pk=role.pk)
        .annotate(
            question_count=Count(
                'interview_questions',
                filter=Q(interview_questions__is_active=True),
            )
        )
        .filter(question_count__gt=0)
        .distinct()[:4]
    )

    recommended_assessments = role.assessment_types.filter(is_active=True)

    return render(request, 'pages/interview_questions/detail.html', {
        'role': role,
        'questions': questions,
        'categories': categories,
        'question_count': questions.count(),
        'related_roles': related_roles,
        'recommended_assessments': recommended_assessments,
    })


# ── Programmatic SEO: Role Assessment Pages ────────────────────────


def role_assessment_list(request):
    """List all roles with their recommended assessments."""
    roles = Role.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            'assessment_types',
            queryset=PublicAssessment.objects.filter(is_active=True),
        )
    )

    department = request.GET.get('department', '').strip()
    if department:
        roles = roles.filter(department__iexact=department)

    query = request.GET.get('q', '').strip()
    if query:
        roles = roles.filter(
            Q(title__icontains=query)
            | Q(department__icontains=query)
            | Q(description__icontains=query)
        )

    departments = (
        Role.objects.filter(is_active=True)
        .values_list('department', flat=True)
        .distinct()
        .order_by('department')
    )

    paginator = Paginator(roles, 24)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'pages/roles/list.html', {
        'roles': page_obj,
        'page_obj': page_obj,
        'query': query,
        'department': department,
        'departments': departments,
        'is_paginated': page_obj.has_other_pages(),
    })


def role_assessment_detail(request, slug):
    """Show assessment recommendations for a role."""
    role = get_object_or_404(Role, slug=slug, is_active=True)

    recommended_assessments = role.assessment_types.filter(is_active=True).order_by('order')

    related_roles = (
        Role.objects.filter(is_active=True, department=role.department)
        .exclude(pk=role.pk)[:4]
    )

    has_interview_questions = role.interview_questions.filter(is_active=True).exists()

    return render(request, 'pages/roles/detail.html', {
        'role': role,
        'recommended_assessments': recommended_assessments,
        'related_roles': related_roles,
        'has_interview_questions': has_interview_questions,
    })
