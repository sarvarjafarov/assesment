"""
Admin dashboard analytics — monkey-patches AdminSite.index to inject
business KPIs, chart data, and recent activity into the admin index page.
"""

import json
from datetime import timedelta

from django.contrib import admin
from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth


def _get_dashboard_context():
    """Gather all analytics data for the admin dashboard."""
    from clients.models import ClientAccount, ClientProject
    from assessments.models import AssessmentSession, CandidateProfile
    from marketing_assessments.models import DigitalMarketingAssessmentSession
    from pm_assessments.models import ProductAssessmentSession
    from behavioral_assessments.models import BehavioralAssessmentSession
    from custom_assessments.models import CustomAssessmentSession
    from ux_assessments.models import UXDesignAssessmentSession
    from hr_assessments.models import HRAssessmentSession
    from finance_assessments.models import FinanceAssessmentSession
    from pages.models import DemoRequest, NewsletterSubscriber
    from candidate.models import CandidateSupportRequest

    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    six_months_ago = now - timedelta(days=180)

    # --- KPI metrics ---
    total_clients = ClientAccount.objects.count()
    new_clients_month = ClientAccount.objects.filter(created_at__gte=thirty_days_ago).count()
    total_candidates = CandidateProfile.objects.count()
    total_projects = ClientProject.objects.count()
    active_projects = ClientProject.objects.filter(status="active").count()

    # Core assessment sessions
    core_sessions = AssessmentSession.objects.all()
    core_completed = core_sessions.filter(status="completed").count()
    core_completed_month = core_sessions.filter(
        status="completed", submitted_at__gte=thirty_days_ago
    ).count()
    core_active = core_sessions.filter(status__in=["invited", "in_progress"]).count()

    # Specialized assessment counts
    # (label, Model, completed_date_field)
    SESSION_MODELS = [
        ("Marketing", DigitalMarketingAssessmentSession, "submitted_at"),
        ("Product", ProductAssessmentSession, "submitted_at"),
        ("Behavioral", BehavioralAssessmentSession, "submitted_at"),
        ("Custom", CustomAssessmentSession, "completed_at"),
        ("UX Design", UXDesignAssessmentSession, "submitted_at"),
        ("HR", HRAssessmentSession, "submitted_at"),
        ("Finance", FinanceAssessmentSession, "submitted_at"),
    ]

    specialized_total = 0
    specialized_completed = 0
    specialized_completed_month = 0
    specialized_active = 0
    assessment_type_counts = []

    for label, Model, date_field in SESSION_MODELS:
        total = Model.objects.count()
        completed = Model.objects.filter(status="submitted").count()
        completed_m = Model.objects.filter(
            **{"status": "submitted", f"{date_field}__gte": thirty_days_ago}
        ).count()
        active = Model.objects.filter(status__in=["in_progress", "draft"]).count()

        specialized_total += total
        specialized_completed += completed
        specialized_completed_month += completed_m
        specialized_active += active
        assessment_type_counts.append({"label": label, "total": total, "completed": completed})

    all_completed = core_completed + specialized_completed
    all_completed_month = core_completed_month + specialized_completed_month
    all_active = core_active + specialized_active
    all_sessions = core_sessions.count() + specialized_total

    # Pages / Leads
    pending_demos = DemoRequest.objects.filter(status="new").count()
    total_demos = DemoRequest.objects.count()
    newsletter_active = NewsletterSubscriber.objects.filter(status="active").count()

    # Support
    open_tickets = CandidateSupportRequest.objects.filter(status="new").count()

    # Hiring Agent
    try:
        from hiring_agent.models import HiringPipeline, PipelineCandidate
        active_pipelines = HiringPipeline.objects.filter(status="active").count()
        pipeline_candidates = PipelineCandidate.objects.count()
        pipeline_hired = PipelineCandidate.objects.filter(stage="hired").count()
    except Exception:
        active_pipelines = 0
        pipeline_candidates = 0
        pipeline_hired = 0

    # --- Chart data ---

    # 1. Clients by plan (doughnut)
    clients_by_plan = list(
        ClientAccount.objects.values("plan_slug")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    plan_labels = [c["plan_slug"].title() if c["plan_slug"] else "None" for c in clients_by_plan]
    plan_counts = [c["count"] for c in clients_by_plan]

    # 2. Monthly client signups (last 6 months)
    monthly_clients = list(
        ClientAccount.objects.filter(created_at__gte=six_months_ago)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    client_months = [m["month"].strftime("%b %Y") for m in monthly_clients]
    client_month_counts = [m["count"] for m in monthly_clients]

    # 3. Monthly assessment completions (last 6 months, core sessions only)
    monthly_completions = list(
        AssessmentSession.objects.filter(
            status="completed", submitted_at__gte=six_months_ago
        )
        .annotate(month=TruncMonth("submitted_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    completion_months = [m["month"].strftime("%b %Y") for m in monthly_completions]
    completion_counts = [m["count"] for m in monthly_completions]

    # 4. Core session status breakdown (doughnut)
    session_statuses = list(
        AssessmentSession.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    status_labels = [s["status"].replace("_", " ").title() for s in session_statuses]
    status_counts = [s["count"] for s in session_statuses]

    # 5. Demo request statuses
    demo_statuses = list(
        DemoRequest.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    demo_labels = [d["status"].replace("_", " ").title() for d in demo_statuses]
    demo_counts = [d["count"] for d in demo_statuses]

    # --- Recent activity ---
    recent_clients = list(
        ClientAccount.objects.order_by("-created_at")[:8].values(
            "id", "company_name", "plan_slug", "status", "created_at"
        )
    )
    for c in recent_clients:
        c["created_at"] = c["created_at"].strftime("%b %d, %Y") if c["created_at"] else ""

    recent_demos = list(
        DemoRequest.objects.order_by("-created_at")[:8].values(
            "id", "full_name", "email", "company", "status", "created_at"
        )
    )
    for d in recent_demos:
        d["created_at"] = d["created_at"].strftime("%b %d, %Y") if d["created_at"] else ""

    recent_tickets = list(
        CandidateSupportRequest.objects.filter(status="new")
        .order_by("-created_at")[:8]
        .values("id", "topic", "status", "created_at")
    )
    for t in recent_tickets:
        t["created_at"] = t["created_at"].strftime("%b %d, %Y") if t["created_at"] else ""

    return {
        # KPIs
        "total_clients": total_clients,
        "new_clients_month": new_clients_month,
        "total_candidates": total_candidates,
        "total_projects": total_projects,
        "active_projects": active_projects,
        "all_sessions": all_sessions,
        "all_completed": all_completed,
        "all_completed_month": all_completed_month,
        "all_active": all_active,
        "pending_demos": pending_demos,
        "total_demos": total_demos,
        "newsletter_active": newsletter_active,
        "open_tickets": open_tickets,
        "active_pipelines": active_pipelines,
        "pipeline_candidates": pipeline_candidates,
        "pipeline_hired": pipeline_hired,
        # Chart data (JSON)
        "plan_labels": json.dumps(plan_labels),
        "plan_counts": json.dumps(plan_counts),
        "client_months": json.dumps(client_months),
        "client_month_counts": json.dumps(client_month_counts),
        "completion_months": json.dumps(completion_months),
        "completion_counts": json.dumps(completion_counts),
        "status_labels": json.dumps(status_labels),
        "status_counts": json.dumps(status_counts),
        "demo_labels": json.dumps(demo_labels),
        "demo_counts": json.dumps(demo_counts),
        "assessment_type_counts": json.dumps(assessment_type_counts),
        # Recent activity
        "recent_clients": recent_clients,
        "recent_demos": recent_demos,
        "recent_tickets": recent_tickets,
    }


# Monkey-patch AdminSite.index to inject analytics context
_original_index = admin.sites.AdminSite.index


def _patched_index(self, request, extra_context=None):
    extra_context = extra_context or {}
    try:
        extra_context.update(_get_dashboard_context())
    except Exception:
        pass  # Fail gracefully — show default dashboard if queries error
    return _original_index(self, request, extra_context=extra_context)


admin.sites.AdminSite.index = _patched_index
