from django.shortcuts import render

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
    return render(
        request,
        "pages/home.html",
        {
            "features": FEATURES,
            "articles": ARTICLES,
        },
    )
