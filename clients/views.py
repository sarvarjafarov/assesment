from __future__ import annotations

import csv
import io
import json
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.forms.models import model_to_dict
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import FormView, TemplateView

from assessments.constants import PIPELINE_STAGE_CHOICES
from behavioral_assessments.models import BehavioralAssessmentSession
from marketing_assessments.models import DigitalMarketingAssessmentSession
from pm_assessments.models import ProductAssessmentSession
from ux_assessments.models import UXDesignAssessmentSession
from hr_assessments.models import HRAssessmentSession
from finance_assessments.models import FinanceAssessmentSession

from .forms import (
    ClientLogoForm,
    ClientPasswordChangeForm,
    ClientProjectForm,
    ClientBehavioralInviteForm,
    ClientBulkInviteForm,
    ClientLoginForm,
    ClientMarketingInviteForm,
    ClientProductInviteForm,
    ClientUXDesignInviteForm,
    ClientHRInviteForm,
    ClientFinanceInviteForm,
    ClientSignupForm,
    ClientSessionNoteForm,
    EmailPreferencesForm,
    HiringProjectForm,
    SocialProfileCompleteForm,
)
from .models import ClientAccount, ClientNotification, ClientProject, ClientSessionNote, HiringProject, PositionApplication, SupportRequest
from .services import send_verification_email, send_approval_notification, send_welcome_email, is_ssrf_target

logger = logging.getLogger(__name__)

_LOGIN_MAX_ATTEMPTS = 10
_LOGIN_WINDOW_SECONDS = 900  # 15 minutes


def _get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _is_login_rate_limited(request):
    from django.core.cache import cache
    ip = _get_client_ip(request)
    key = f"login_ratelimit:{ip}"
    attempts = cache.get(key, 0)
    return attempts >= _LOGIN_MAX_ATTEMPTS


def _record_failed_login(request):
    from django.core.cache import cache
    ip = _get_client_ip(request)
    key = f"login_ratelimit:{ip}"
    attempts = cache.get(key, 0)
    cache.set(key, attempts + 1, _LOGIN_WINDOW_SECONDS)

ACTIVITY_STATUS_CHOICES = {"all", "draft", "in_progress", "submitted"}
ACTIVITY_ASSESSMENT_CHOICES = {"all"} | {choice[0] for choice in ClientAccount.ASSESSMENT_CHOICES}
ACTIVITY_WINDOWS = {"7": 7, "30": 30, "90": 90}
ACTIVITY_PRESETS = {
    "needs_review": {"status": "in_progress", "assessment": "all"},
    "completed_last_7": {"status": "submitted", "window": "7"},
}


def parse_activity_filters(params):
    assessment = params.get("assessment", "all")
    status = params.get("status", "all")
    window = params.get("window", "30")
    preset = params.get("preset", "")
    if assessment not in ACTIVITY_ASSESSMENT_CHOICES:
        assessment = "all"
    if status not in ACTIVITY_STATUS_CHOICES:
        status = "all"
    if window not in ACTIVITY_WINDOWS:
        window = "30"
    result = {"assessment": assessment, "status": status, "window": window, "preset": ""}
    if preset in ACTIVITY_PRESETS:
        result.update(ACTIVITY_PRESETS[preset])
        result["preset"] = preset
    return result


def send_client_verification_email(account: ClientAccount, request):
    # Rate limit: don't resend if last verification was sent within 2 minutes
    if account.verification_sent_at:
        elapsed = (timezone.now() - account.verification_sent_at).total_seconds()
        if elapsed < 120:
            logger.info("Verification email rate-limited for %s (sent %ds ago)", account.email, elapsed)
            return
    try:
        token = account.generate_verification_token()
        verify_url = request.build_absolute_uri(reverse("clients:verify-email", args=[account.pk, token]))
        subject = "Confirm your Evalon workspace email"
        message = (
            f"Hi {account.full_name},\n\n"
            "Thanks for requesting an Evalon workspace. Please confirm your email so we can finish reviewing your request:\n"
            f"{verify_url}\n\n"
            "Once you're verified, our team will notify you as soon as your workspace is approved."
        )
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [account.email])
    except Exception as exc:  # pragma: no cover - fallback logging
        logger.warning("Failed to send verification email to %s: %s", account.email, exc)


def build_dataset_map(account: ClientAccount):
    return {
        "marketing": DigitalMarketingAssessmentSession.objects.filter(client=account).select_related("project"),
        "product": ProductAssessmentSession.objects.filter(client=account).select_related("project"),
        "behavioral": BehavioralAssessmentSession.objects.filter(client=account).select_related("project"),
        "ux_design": UXDesignAssessmentSession.objects.filter(client=account).select_related("project"),
        "hr": HRAssessmentSession.objects.filter(client=account).select_related("project"),
        "finance": FinanceAssessmentSession.objects.filter(client=account).select_related("project"),
    }


PIPELINE_STAGE_LABELS = dict(PIPELINE_STAGE_CHOICES)
PIPELINE_STAGE_KEYS = [choice[0] for choice in PIPELINE_STAGE_CHOICES]
PIPELINE_STAGE_DEFAULT = PIPELINE_STAGE_KEYS[0]


def normalize_pipeline_stage(session) -> str:
    stage = getattr(session, "pipeline_stage", None) or PIPELINE_STAGE_DEFAULT
    if stage not in PIPELINE_STAGE_LABELS:
        stage = PIPELINE_STAGE_DEFAULT
    status = getattr(session, "status", "")
    if status == "submitted" and stage in {"invited", "in_progress"}:
        return "submitted"
    if status == "in_progress" and stage == "invited":
        return "in_progress"
    return stage


ASSESSMENT_MODEL_MAP = {
    "marketing": DigitalMarketingAssessmentSession,
    "product": ProductAssessmentSession,
    "behavioral": BehavioralAssessmentSession,
    "ux_design": UXDesignAssessmentSession,
    "hr": HRAssessmentSession,
    "finance": FinanceAssessmentSession,
}


def build_session_report(session, assessment_type: str):
    if assessment_type == "behavioral":
        return {
            "score": session.eligibility_score,
            "label": session.eligibility_label,
            "traits": session.trait_scores or {},
            "flags": session.risk_flags or [],
        }
    recommendations = session.recommendations or {}
    categories = session.category_breakdown or {}
    baseline = getattr(settings, "ASSESSMENT_PASSING_SCORE", 70)
    heatmap = []
    for label, value in categories.items():
        try:
            score = float(value)
        except (TypeError, ValueError):
            score = None
        status = "neutral"
        if score is not None:
            if score >= baseline + 5:
                status = "positive"
            elif score < baseline - 5:
                status = "warning"
        heatmap.append({"label": label, "score": score, "status": status})
    return {
        "overall": session.overall_score,
        "hard": getattr(session, "hard_skill_score", None),
        "soft": getattr(session, "soft_skill_score", None),
        "categories": categories,
        "category_heatmap": heatmap,
        "fit_scores": recommendations.get("fit_scores", {}),
        "strengths": recommendations.get("strengths", []),
        "development": recommendations.get("development", []),
        "seniority": recommendations.get("seniority"),
    }


def build_actionable_summary(report, decision_summary, recommended_decision):
    base_score = report.get("overall")
    if base_score is None:
        base_score = report.get("score")
    threshold = getattr(settings, "ASSESSMENT_PASSING_SCORE", 70)
    flags = len(report.get("flags", [])) if isinstance(report, dict) else 0
    if recommended_decision:
        recommendation = recommended_decision["decision"]
    elif decision_summary:
        top = max(decision_summary, key=lambda item: item["count"])
        recommendation = top["decision"]
    else:
        if base_score is None:
            recommendation = "hold"
        elif base_score >= threshold and flags == 0:
            recommendation = "advance"
        elif base_score >= threshold - 5:
            recommendation = "hold"
        else:
            recommendation = "reject"
    tone_map = {
        "advance": ("Advance candidate", "Strong score and minimal risk.", "positive", "Strong Hire"),
        "hold": ("Gather more signals", "Borderline score or pending follow-up.", "neutral", "Needs Review"),
        "reject": ("Do not advance", "Score or risk indicators fall below expectations.", "negative", "Below Bar"),
    }
    headline, default_subline, tone, label = tone_map.get(recommendation, tone_map["hold"])
    if base_score is not None:
        subline = f"Score {base_score:.1f} vs. target {threshold}"
    else:
        subline = default_subline
    strengths = report.get("strengths") or report.get("traits", {})
    strength_focus = ""
    if isinstance(strengths, list) and strengths:
        strength_focus = strengths[0].title()
    elif isinstance(strengths, dict) and strengths:
        strength_focus = max(strengths.items(), key=lambda item: item[1])[0].title()
    score_display = f"{base_score:.0f}" if base_score is not None else "—"
    flag_display = f"{flags} flag{'s' if flags != 1 else ''}" if flags else "None"
    return {
        "headline": headline,
        "subline": subline,
        "tone": tone,
        "label": label,
        "strength_focus": strength_focus,
        "metrics": {
            "score": score_display,
            "flags": flag_display,
            "strength": strength_focus or "—",
        },
    }


def _default_project_health(project=None):
    return {
        "project": project,
        "total": 0,
        "submitted": 0,
        "in_progress": 0,
        "draft": 0,
        "paused": 0,
        "active_invites": 0,
        "completion_rate": None,
        "avg_completion_minutes": None,
        "avg_time_to_fill_days": None,
        "top_candidates": [],
        "spotlight_candidate": None,
    }


def build_project_health_map(account: ClientAccount, dataset_map: dict | None = None) -> dict[int, dict]:
    dataset_map = dataset_map or build_dataset_map(account)
    stats: dict[int, dict] = {}
    for code, queryset in dataset_map.items():
        label = ClientAccount.ASSESSMENT_DETAILS.get(code, {}).get("label", code.title())
        # Only consider sessions tied to a project
        for session in queryset.filter(project__isnull=False):
            project = session.project
            if not project:
                continue
            entry = stats.get(project.id)
            if not entry:
                entry = {
                    "project": project,
                    "total": 0,
                    "submitted": 0,
                    "in_progress": 0,
                    "draft": 0,
                    "paused": 0,
                    "active_invites": 0,
                    "completion_rate": None,
                    "avg_completion_minutes": None,
                    "avg_time_to_fill_days": None,
                    "top_candidates": [],
                    "spotlight_candidate": None,
                    "_completion_minutes_sum": 0,
                    "_completion_minutes_count": 0,
                    "_time_to_fill_days_sum": 0,
                    "_time_to_fill_days_count": 0,
                }
                stats[project.id] = entry

            entry["total"] += 1
            status = session.status
            if status == "submitted":
                entry["submitted"] += 1
            elif status == "in_progress":
                entry["in_progress"] += 1
            elif status == "draft":
                entry["draft"] += 1
            elif status == "paused":
                entry["paused"] += 1

            if status == "submitted":
                start_ts = session.started_at or session.created_at
                submitted_ts = session.submitted_at or session.updated_at
                if start_ts and submitted_ts:
                    runtime_minutes = (submitted_ts - start_ts).total_seconds() / 60
                else:
                    runtime_minutes = session.duration_minutes or None
                if runtime_minutes:
                    entry["_completion_minutes_sum"] += runtime_minutes
                    entry["_completion_minutes_count"] += 1
                if session.created_at and submitted_ts:
                    days_to_complete = (submitted_ts - session.created_at).total_seconds() / 86400
                    if days_to_complete >= 0:
                        entry["_time_to_fill_days_sum"] += days_to_complete
                        entry["_time_to_fill_days_count"] += 1

                score = getattr(session, "overall_score", None)
                if score is None:
                    score = getattr(session, "eligibility_score", None)
                try:
                    numeric_score = float(score) if score is not None else None
                except (TypeError, ValueError):
                    numeric_score = None
                if numeric_score is not None:
                    entry["top_candidates"].append(
                        {
                            "candidate": session.candidate_id,
                            "score": numeric_score,
                            "score_display": numeric_score,
                            "assessment": label,
                            "detail_url": reverse("clients:assessment-detail", args=[code, session.uuid]),
                            "submitted_at": submitted_ts,
                        }
                    )

    for entry in stats.values():
        entry["active_invites"] = max(entry["total"] - entry["submitted"], 0)
        if entry["total"]:
            entry["completion_rate"] = round((entry["submitted"] / entry["total"]) * 100)
        if entry.get("_completion_minutes_count"):
            entry["avg_completion_minutes"] = entry["_completion_minutes_sum"] / entry["_completion_minutes_count"]
        if entry.get("_time_to_fill_days_count"):
            entry["avg_time_to_fill_days"] = entry["_time_to_fill_days_sum"] / entry["_time_to_fill_days_count"]
        entry["top_candidates"].sort(key=lambda item: (item.get("score") or 0), reverse=True)
        entry["top_candidates"] = entry["top_candidates"][:3]
        entry["spotlight_candidate"] = entry["top_candidates"][0] if entry["top_candidates"] else None
        entry.pop("_completion_minutes_sum", None)
        entry.pop("_completion_minutes_count", None)
        entry.pop("_time_to_fill_days_sum", None)
        entry.pop("_time_to_fill_days_count", None)
    return stats


ALL_ROLE_CODES = {code for code, _ in ClientAccount.ROLE_CHOICES}
ROLE_INVITE_ACCESS = {"manager", "recruiter"}
ROLE_NOTE_ACCESS = {"manager", "recruiter", "interviewer"}
ROLE_DECISION_ACCESS = {"manager", "recruiter"}
ROLE_BRANDING_ACCESS = ALL_ROLE_CODES


def build_activity_feed(account: ClientAccount, dataset_map: dict, filters: dict, activity_limit: int | None = 6):
    entries: list[dict] = []
    cutoff = timezone.now() - timedelta(days=ACTIVITY_WINDOWS.get(filters.get("window", "30"), 30))
    for code, queryset in dataset_map.items():
        if filters.get("assessment") not in ("all", code):
            continue
        qs = queryset
        if filters.get("status") not in ("all", None):
            qs = qs.filter(status=filters["status"])
        qs = qs.filter(models.Q(updated_at__gte=cutoff) | models.Q(created_at__gte=cutoff))
        label = ClientAccount.ASSESSMENT_DETAILS.get(code, {}).get("label", code.title())
        for session in qs.order_by("-updated_at")[:200]:
            timestamp = session.updated_at or session.created_at
            entries.append(
                {
                    "candidate": session.candidate_id,
                    "assessment": label,
                    "status": session.get_status_display(),
                    "timestamp": timestamp,
                    "detail_url": reverse("clients:assessment-detail", args=[code, session.uuid])
                    if session.status == "submitted"
                    else None,
                    "manage_url": reverse("clients:assessment-manage", args=[code]),
                }
            )
    entries.sort(key=lambda item: item["timestamp"] or timezone.now(), reverse=True)
    if activity_limit:
        return entries[:activity_limit]
    return entries


class ClientSignupView(FormView):
    template_name = "clients/signup.html"
    form_class = ClientSignupForm
    success_url = reverse_lazy("clients:signup-complete")

    def form_valid(self, form):
        try:
            account = form.save()
        except Exception as e:
            logger.exception("Client signup failed: %s", e)
            if isinstance(e, ValidationError):
                msg_list = getattr(e, "messages", None) or getattr(e, "message_list", None)
                msg = msg_list[0] if msg_list else str(e)
                form.add_error(None, msg)
                return self.form_invalid(form)
            raise
        # Send verification email with new service
        email_sent = send_verification_email(account)
        if email_sent:
            messages.success(
                self.request,
                "Thanks for signing up! Please check your inbox to verify your email address.",
            )
        else:
            messages.warning(
                self.request,
                "Account created, but we couldn't send the verification email. Please contact support.",
            )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assessment_details"] = ClientAccount.ASSESSMENT_DETAILS
        return context


class ClientSignupCompleteView(TemplateView):
    template_name = "clients/signup_complete.html"


class ClientVerifyEmailView(TemplateView):
    template_name = "clients/verify_email.html"

    def post(self, request, *args, **kwargs):
        """Handle verification via POST to prevent state-change on GET."""
        context = self._verify(kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = kwargs.get("token")
        account_id = kwargs.get("account_id")

        # On GET, look up the account to show confirmation page but don't verify yet
        account = None
        if token and account_id:
            account = ClientAccount.objects.filter(pk=account_id, verification_token=token).first()

        if not account:
            context["status"] = "invalid"
        elif account.is_email_verified:
            context["status"] = "already"
        elif not account.is_verification_token_valid():
            context["status"] = "expired"
        else:
            # Token is valid — show a confirm button (POST will do the actual verification)
            context["status"] = "confirm"

        context["account"] = account
        return context

    def _verify(self, kwargs):
        token = kwargs.get("token")
        account_id = kwargs.get("account_id")
        account = None
        status = "invalid"

        if token and account_id:
            account = ClientAccount.objects.filter(pk=account_id, verification_token=token).first()

        if not account:
            status = "invalid"
        elif account.is_email_verified:
            status = "already"
        elif not account.is_verification_token_valid():
            status = "expired"
        else:
            account.mark_email_verified()
            status = "verified"
            logger.info("Email verified for account id=%s email=%s", account.pk, account.email)

            admin_notified = send_approval_notification(account)
            if admin_notified:
                logger.info("Admin notification sent for account: %s", account.email)
            else:
                logger.warning("Failed to send admin notification for: %s", account.email)

        return {"status": status, "account": account}


class ClientLoginView(FormView):
    template_name = "clients/login.html"
    form_class = ClientLoginForm
    success_url = reverse_lazy("clients:dashboard")

    def dispatch(self, request, *args, **kwargs):
        if _is_login_rate_limited(request):
            messages.error(request, "Too many login attempts. Please try again in 15 minutes.")
            return self.render_to_response(self.get_context_data())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        logger.info("Login success: user=%s ip=%s", user.email, self.request.META.get("REMOTE_ADDR"))
        return super().form_valid(form)

    def form_invalid(self, form):
        _record_failed_login(self.request)
        email = form.data.get("username", "")
        logger.warning("Login failed: email=%s ip=%s", email, self.request.META.get("REMOTE_ADDR"))
        return super().form_invalid(form)


class ClientLogoutView(LoginRequiredMixin, TemplateView):
    template_name = "clients/logout.html"
    login_url = reverse_lazy("clients:login")

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, "You have been signed out.")
        return redirect("clients:login")


class ClientDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "clients/dashboard.html"
    login_url = reverse_lazy("clients:login")
    http_method_names = ["get", "post"]
    logo_form_class = ClientLogoForm

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "client_account"):
            return redirect("clients:login")
        client = request.user.client_account
        # Check profile completion first
        if not client.company_name:
            return redirect("clients:complete_profile")
        self.logo_form = self.logo_form_class()
        if client.status != "approved":
            messages.info(request, "Your account is still pending approval.")
            return redirect("clients:pending_approval")
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.exception(f"Dashboard error for user {request.user.email}: {e}")
            raise

    def post(self, request, *args, **kwargs):
        account = request.user.client_account
        action = request.POST.get("action")
        if action == "toggle_summary":
            if account.role not in ROLE_INVITE_ACCESS and account.role not in ROLE_BRANDING_ACCESS:
                messages.error(request, "Only managers can edit email settings.")
                return redirect("clients:dashboard")
            opt_in = request.POST.get("weekly_summary") == "on"
            account.receive_weekly_summary = opt_in
            account.save(update_fields=["receive_weekly_summary"])
            if opt_in:
                messages.success(request, "Weekly summary emails enabled.")
            else:
                messages.info(request, "Weekly summary emails disabled.")
        elif action == "dismiss_notification":
            note_id = request.POST.get("notification_id")
            try:
                notification = account.notifications.get(id=note_id)
            except ClientNotification.DoesNotExist:
                messages.error(request, "Notification not found.")
            else:
                notification.is_read = True
                notification.save(update_fields=["is_read"])
        elif action == "upload_logo":
            if account.role not in ROLE_BRANDING_ACCESS:
                messages.error(request, "Only managers can update branding.")
                return redirect("clients:dashboard")
            form = self.logo_form_class(request.POST, request.FILES)
            if form.is_valid():
                account.logo = form.cleaned_data["logo"]
                account.save()
                messages.success(request, "Logo updated.")
                return redirect("clients:dashboard")
            self.logo_form = form
            response = self.get(request, *args, **kwargs)
            response.status_code = 400
            return response
        elif action == "remove_logo":
            if account.role not in ROLE_BRANDING_ACCESS:
                messages.error(request, "Only managers can update branding.")
                return redirect("clients:dashboard")
            if account.has_logo:
                account.clear_logo()
                account.save(update_fields=["logo", "logo_data", "logo_mime"])
            messages.info(request, "Logo removed.")
        elif action == "dismiss_onboarding":
            # Mark onboarding as complete when user dismisses it
            account.mark_onboarding_complete()
            messages.success(request, "Onboarding dismissed. You can always access help from the support link.")
        return redirect("clients:dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.request.user.client_account
        catalog = ClientAccount.ASSESSMENT_DETAILS
        dataset_map = build_dataset_map(account)
        activity_filters = parse_activity_filters(self.request.GET)
        stats = self._calculate_stats(account, dataset_map, activity_filters)
        assessment_stats_map = {item["code"]: item for item in stats.get("assessment_breakdown", [])}
        benchmarks = self._benchmark_snapshot()
        if benchmarks and stats.get("completion_rate") is not None:
            if stats["completion_rate"] + 10 < benchmarks.get("completion_rate", 0):
                stats["attention_items"].append(
                    {
                        "label": "Completion rate below benchmark",
                        "detail": f"Your completion rate ({stats['completion_rate']:.0f}%) trails the network average ({benchmarks.get('completion_rate', 0):.0f}%).",
                        "action_url": reverse("clients:analytics"),
                    }
                )
        if stats["total_candidates"] < max(3, len(account.approved_assessments) * 2):
            stats["attention_items"].append(
                {
                    "label": "Low invite volume",
                    "detail": "Send more invites to keep your pipeline active.",
                    "action_url": reverse("clients:assessments"),
                }
            )
        context.update(
            {
                "account": account,
                "is_manager": account.role == "manager",
                "role_label": dict(ClientAccount.ROLE_CHOICES).get(account.role, account.role.title()),
                "can_manage_branding": account.role in ROLE_BRANDING_ACCESS,
                "allowed_assessments": [
                    {
                        "code": code,
                        "label": catalog.get(code, {}).get("label", code.title()),
                        "description": catalog.get(code, {}).get("description", ""),
                        "manage_url": reverse("clients:assessment-manage", args=[code]),
                        "metrics": assessment_stats_map.get(code, {}),
                    }
                    for code in account.approved_assessments
                ],
                "portal_stats": stats,
                "chart_payload": json.dumps(
                    {
                        "breakdown": stats.get("assessment_breakdown", []),
                        "trend": stats.get("score_trend", []),
                        "funnel": stats.get("funnel", {}),
                    },
                    cls=DjangoJSONEncoder,
                ),
                "quick_actions": self._quick_actions(account),
                "attention_items": stats.get("attention_items", []),
                "activity_feed": stats.get("recent_activity", []),
                "activity_filters": activity_filters,
                "activity_export_url": self._activity_export_url(),
                "benchmark": benchmarks,
                "weekly_summary_enabled": account.receive_weekly_summary,
                "activity_filter_options": {
                    "assessments": [("all", "All assessments")] + list(ClientAccount.ASSESSMENT_CHOICES),
                    "statuses": [("all", "All statuses"), ("draft", "Draft"), ("in_progress", "In progress"), ("submitted", "Completed")],
                    "windows": [("7", "Last 7 days"), ("30", "Last 30 days"), ("90", "Last 90 days")],
                    "presets": [("", "Choose preset"), ("needs_review", "Needs review"), ("completed_last_7", "Completed last 7 days")],
                },
                "activity_querystring": self.request.GET.urlencode(),
                "notifications": self._notifications(account),
                "benchmark_helper": "Benchmarks reference anonymized averages across all clients running the same assessments.",
                "logo_form": getattr(self, "logo_form", self.logo_form_class()),
                "can_manage_invites": account.role in ROLE_INVITE_ACCESS,
                "account_objectives": account.notes,
                "project_preview": [
                    {
                        "title": project.title,
                        "status": project.get_status_display(),
                        "priority": dict(ClientProject.PRIORITY_CHOICES).get(project.priority, project.priority),
                        "open_roles": project.open_roles,
                        "href": reverse("clients:project-detail", args=[project.uuid]),
                        "sessions": project.total_sessions(),
                    }
                    for project in account.projects.order_by("-created_at")[:3]
                ],
                "project_count": account.projects.count(),
                "vacancy_page_url": reverse("pages:vacancy_list", args=[account.slug]) if account.slug else None,
                "published_position_count": account.projects.filter(
                    status=ClientProject.STATUS_ACTIVE, published=True,
                ).count(),
            }
        )

        # Onboarding progress calculation
        if not account.has_completed_onboarding:
            # Check which steps have been completed
            step_1_completed = account.projects.exists()  # Has at least one project
            step_2_completed = stats["total_candidates"] > 0  # Has sent at least one invite
            step_3_completed = stats["completed_count"] > 0  # Has at least one completed assessment

            # Auto-update onboarding step data
            account.onboarding_step_data = {
                'step_1': step_1_completed,
                'step_2': step_2_completed,
                'step_3': step_3_completed,
            }
            account.save(update_fields=['onboarding_step_data'])

            # Auto-complete onboarding if all steps are done
            if step_1_completed and step_2_completed and step_3_completed:
                account.mark_onboarding_complete()

            # Calculate progress
            total_steps = 3
            completed_steps = sum([step_1_completed, step_2_completed, step_3_completed])
            progress_percent = round((completed_steps / total_steps) * 100)

            context.update({
                'onboarding_step_1_completed': step_1_completed,
                'onboarding_step_2_completed': step_2_completed,
                'onboarding_step_3_completed': step_3_completed,
                'onboarding_total_steps': total_steps,
                'onboarding_completed_steps': completed_steps,
                'onboarding_progress': progress_percent,
            })

        plan_details = account.plan_details()
        invite_limit = account.invite_limit()
        invites_used = account.invites_used()
        invite_percent = None
        if invite_limit:
            invite_percent = min(100, round((invites_used / invite_limit) * 100)) if invite_limit else None
        project_limit = account.project_limit()
        project_used = account.active_project_count()
        project_percent = None
        if project_limit:
            project_percent = min(100, round((project_used / project_limit) * 100))
        context["plan_overview"] = {
            "name": plan_details.get("label", account.plan_slug.title()),
            "slug": account.plan_slug,
            "description": plan_details.get("description", ""),
            "invite_limit": invite_limit,
            "invites_used": invites_used,
            "invite_percent": invite_percent,
            "invite_remaining": account.invites_remaining(),
            "project_limit": project_limit,
            "project_used": project_used,
            "project_percent": project_percent,
            "project_remaining": account.remaining_projects(),
            "upgrade_url": f"{reverse('pages:home')}#pricing",
        }

        # Add onboarding context
        context['show_onboarding'] = not account.has_completed_onboarding
        context['onboarding_steps_completed'] = account.onboarding_step_data

        return context

    def _quick_actions(self, account: ClientAccount) -> list[dict]:
        actions = []
        first_assessment = next(iter(account.approved_assessments), None)
        primary_url = reverse("clients:dashboard")
        if first_assessment and account.role in ROLE_INVITE_ACCESS:
            primary_url = reverse("clients:assessment-manage", args=[first_assessment])
            actions.append(
                {
                    "label": "Invite candidate",
                    "description": "Launch a new assessment invite",
                    "href": primary_url,
                }
            )
        actions.append(
            {
                "label": "Download CSV",
                "description": "Export recent results",
                "href": self._activity_export_url(),
            }
        )
        actions.append(
            {
                "label": "Support",
                "description": "Email account management",
                "href": "mailto:support@evalon.app",
                "external": True,
            }
        )
        actions.append(
            {
                "label": "Projects",
                "description": "Track open roles",
                "href": reverse("clients:project-list"),
            }
        )
        return actions

    def _activity_export_url(self):
        base = reverse("clients:activity-export")
        query = self.request.GET.urlencode()
        return f"{base}?{query}" if query else base

    def _calculate_stats(self, account: ClientAccount, dataset_map: dict, activity_filters: dict, activity_limit: int = 6) -> dict:
        marketing_sessions = dataset_map["marketing"]
        product_sessions = dataset_map["product"]
        behavioral_sessions = dataset_map["behavioral"]
        total_candidates = sum(qs.count() for qs in dataset_map.values())

        breakdown = []
        scores: list[float] = []
        durations: list[float] = []
        status_totals = {"draft": 0, "in_progress": 0, "submitted": 0}
        attention_items: list[dict] = []

        def _append_scores(queryset, score_field="overall_score"):
            for score, duration in queryset.filter(status="submitted").values_list(score_field, "duration_minutes"):
                if score is not None:
                    scores.append(float(score))
                if duration is not None:
                    durations.append(float(duration))

        for code, qs in dataset_map.items():
            sf = "eligibility_score" if code == "behavioral" else "overall_score"
            _append_scores(qs, score_field=sf)

        for code in account.approved_assessments:
            label = ClientAccount.ASSESSMENT_DETAILS.get(code, {}).get("label", code.title())
            inviteqs = dataset_map.get(code)
            if inviteqs is None:
                continue
            invites = inviteqs.count()
            in_progress = inviteqs.filter(status="in_progress").count()
            completed = inviteqs.filter(status="submitted").count()
            draft = inviteqs.filter(status="draft").count()
            status_totals["draft"] += draft
            status_totals["in_progress"] += in_progress
            status_totals["submitted"] += completed
            breakdown.append(
                {
                    "code": code,
                    "label": label,
                    "invites": invites,
                    "completed": completed,
                    "in_progress": in_progress,
                    "draft": draft,
                }
            )

        avg_score = sum(scores) / len(scores) if scores else None
        avg_duration = sum(durations) / len(durations) if durations else None

        recent = []
        for qs in dataset_map.values():
            recent += list(qs.order_by("-created_at")[:5])
        recent.sort(key=lambda session: session.created_at or session.updated_at)
        recent = recent[-5:]

        filtered_activity = build_activity_feed(account, dataset_map, activity_filters, activity_limit=activity_limit)

        trend = []
        for session in recent:
            base_score = getattr(session, "overall_score", None)
            if base_score is None:
                base_score = getattr(session, "eligibility_score", None)
            trend.append(
                {
                    "label": session.candidate_id,
                    "score": float(base_score) if base_score is not None else None,
                    "ts": session.submitted_at or session.created_at,
                }
            )

        if status_totals["in_progress"]:
            attention_items.append(
                {
                    "label": "Invites in progress",
                    "detail": f"{status_totals['in_progress']} candidate(s) are still working through assessments.",
                }
            )
        if status_totals["draft"]:
            attention_items.append(
                {
                    "label": "Draft invites",
                    "detail": f"{status_totals['draft']} invite(s) have not been launched.",
                }
            )

        funnel = {
            "invited": total_candidates,
            "started": status_totals["in_progress"] + status_totals["submitted"],
            "completed": status_totals["submitted"],
        }
        completion_rate = (funnel["completed"] / funnel["invited"] * 100) if funnel["invited"] else 0

        return {
            "total_candidates": total_candidates,
            "completed_count": status_totals["submitted"],
            "in_progress_count": status_totals["in_progress"],
            "draft_count": status_totals["draft"],
            "completion_rate": completion_rate,
            "average_score": avg_score,
            "average_duration": avg_duration,
            "assessment_breakdown": breakdown,
            "score_trend": trend,
            "recent_activity": filtered_activity,
            "attention_items": attention_items,
            "funnel": funnel,
        }

    def _benchmark_snapshot(self) -> dict:
        account = self.request.user.client_account
        durations: list[float] = []
        scores: list[float] = []
        total_invites = 0
        total_completed = 0
        datasets = (
            (DigitalMarketingAssessmentSession.objects.filter(client=account), "overall_score"),
            (ProductAssessmentSession.objects.filter(client=account), "overall_score"),
            (BehavioralAssessmentSession.objects.filter(client=account), "eligibility_score"),
            (UXDesignAssessmentSession.objects.filter(client=account), "overall_score"),
            (HRAssessmentSession.objects.filter(client=account), "overall_score"),
            (FinanceAssessmentSession.objects.filter(client=account), "overall_score"),
        )
        for queryset, score_field in datasets:
            total_invites += queryset.count()
            completed = queryset.filter(status="submitted")
            total_completed += completed.count()
            durations.extend(
                float(val) for val in completed.values_list("duration_minutes", flat=True) if val is not None
            )
            scores.extend(
                float(val) for val in completed.values_list(score_field, flat=True) if val is not None
            )
        completion_rate = (total_completed / total_invites * 100) if total_invites else 0
        avg_duration = sum(durations) / len(durations) if durations else None
        avg_score = sum(scores) / len(scores) if scores else None
        return {
            "completion_rate": completion_rate,
            "average_duration": avg_duration,
            "average_score": avg_score,
        }

    def _notifications(self, account: ClientAccount) -> list[ClientNotification]:
        return list(account.notifications.filter(is_read=False)[:5])


class ClientAssessmentsView(LoginRequiredMixin, TemplateView):
    """Dedicated assessments catalog page."""
    template_name = "clients/assessments.html"
    login_url = reverse_lazy("clients:login")

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "client_account"):
            return redirect("clients:login")
        client = request.user.client_account
        if not client.company_name:
            return redirect("clients:complete_profile")
        if client.status != "approved":
            messages.info(request, "Your account is still pending approval.")
            return redirect("clients:pending_approval")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.request.user.client_account
        catalog = ClientAccount.ASSESSMENT_DETAILS
        dataset_map = build_dataset_map(account)

        # Calculate metrics for each assessment
        assessment_stats = {}
        for code in account.approved_assessments:
            sessions = dataset_map.get(code, [])
            total = sessions.count()
            completed = sessions.filter(status='submitted').count()
            in_progress = sessions.filter(status='in_progress').count()
            completion_rate = (completed / total * 100) if total > 0 else None

            assessment_stats[code] = {
                'total_invites': total,
                'completed_invites': completed,
                'in_progress_invites': in_progress,
                'completion_rate': completion_rate,
            }

        context.update({
            'account': account,
            'is_manager': account.role == 'manager',
            'can_manage_invites': account.role in ROLE_INVITE_ACCESS,
            'allowed_assessments': [
                {
                    'code': code,
                    'label': catalog.get(code, {}).get('label', code.title()),
                    'description': catalog.get(code, {}).get('description', ''),
                    'manage_url': reverse('clients:assessment-manage', args=[code]),
                    'metrics': assessment_stats.get(code, {}),
                }
                for code in account.approved_assessments
            ],
            'activity_export_url': reverse('clients:activity-export'),
        })
        return context


class ClientAnalyticsView(LoginRequiredMixin, TemplateView):
    """Analytics and reporting page."""
    template_name = "clients/analytics.html"
    login_url = reverse_lazy("clients:login")

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "client_account"):
            return redirect("clients:login")
        client = request.user.client_account
        if not client.company_name:
            return redirect("clients:complete_profile")
        if client.status != "approved":
            messages.info(request, "Your account is still pending approval.")
            return redirect("clients:pending_approval")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.request.user.client_account
        dataset_map = build_dataset_map(account)

        # Get time period filter (default to 30 days)
        period = self.request.GET.get('period', '30')
        period_days = {'7': 7, '30': 30, '90': 90, 'all': None}.get(period, 30)

        # Calculate analytics data
        analytics_data = self._calculate_analytics(account, dataset_map, period_days)

        context.update({
            'account': account,
            'is_manager': account.role == 'manager',
            'analytics': analytics_data,
            'selected_period': period,
            'chart_payload': analytics_data['chart_data'],
        })
        return context

    def _calculate_analytics(self, account: ClientAccount, dataset_map: dict, period_days: int = None):
        """Calculate comprehensive analytics data."""
        from datetime import timedelta

        # Filter by time period if specified
        cutoff = None
        if period_days:
            cutoff = timezone.now() - timedelta(days=period_days)

        # Aggregate all sessions across all assessment types in the dataset
        all_sessions = []
        for assessment_type, qs in dataset_map.items():
            if cutoff:
                qs = qs.filter(created_at__gte=cutoff)
            all_sessions.extend(list(qs))

        total_count = len(all_sessions)
        completed_sessions = [s for s in all_sessions if s.status == 'submitted']
        in_progress_sessions = [s for s in all_sessions if s.status == 'in_progress']

        # Calculate key metrics
        completion_rate = (len(completed_sessions) / total_count * 100) if total_count > 0 else 0

        # Score statistics
        scores = []
        for s in completed_sessions:
            score = getattr(s, 'overall_score', None) or getattr(s, 'eligibility_score', None)
            if score is not None:
                scores.append(float(score))

        avg_score = sum(scores) / len(scores) if scores else None

        # Duration statistics
        durations = [s.duration_minutes for s in completed_sessions if s.duration_minutes]
        avg_duration = sum(durations) / len(durations) if durations else None

        # Assessment breakdown
        assessment_breakdown = []
        for code in account.approved_assessments:
            sessions = dataset_map.get(code, [])
            if cutoff:
                sessions = sessions.filter(created_at__gte=cutoff)

            count = sessions.count()
            completed = sessions.filter(status='submitted').count()

            assessment_breakdown.append({
                'code': code,
                'label': ClientAccount.ASSESSMENT_DETAILS.get(code, {}).get('label', code.title()),
                'total': count,
                'completed': completed,
                'completion_rate': (completed / count * 100) if count > 0 else 0,
            })

        # Trend data (last 7 data points)
        trend_data = self._calculate_trend(all_sessions, period_days or 30)

        # Funnel data
        funnel_data = {
            'invited': total_count,
            'started': len([s for s in all_sessions if s.status in ['in_progress', 'submitted']]),
            'completed': len(completed_sessions),
        }

        return {
            'total_invites': total_count,
            'completed_count': len(completed_sessions),
            'in_progress_count': len(in_progress_sessions),
            'completion_rate': completion_rate,
            'average_score': avg_score,
            'average_duration': avg_duration,
            'assessment_breakdown': assessment_breakdown,
            'score_distribution': self._calculate_score_distribution(scores),
            'chart_data': {
                'trend': trend_data,
                'breakdown': assessment_breakdown,
                'funnel': funnel_data,
            }
        }

    def _calculate_trend(self, sessions, days):
        """Calculate trend data for the specified period."""
        from datetime import timedelta
        import math

        if not sessions:
            return []

        # Group sessions by date
        data_points = min(days, 14)  # Max 14 data points
        interval = max(1, math.ceil(days / data_points))

        trend = []
        now = timezone.now()

        for i in range(data_points):
            end_date = now - timedelta(days=i * interval)
            start_date = end_date - timedelta(days=interval)

            period_sessions = [
                s for s in sessions
                if s.created_at and start_date <= s.created_at < end_date
            ]

            completed = [s for s in period_sessions if s.status == 'submitted']
            scores = []
            for s in completed:
                score = getattr(s, 'overall_score', None) or getattr(s, 'eligibility_score', None)
                if score is not None:
                    scores.append(float(score))

            avg_score = sum(scores) / len(scores) if scores else 0

            trend.insert(0, {
                'date': start_date.strftime('%b %d'),
                'count': len(period_sessions),
                'completed': len(completed),
                'avg_score': round(avg_score, 1) if avg_score else 0,
            })

        return trend

    def _calculate_score_distribution(self, scores):
        """Calculate score distribution in ranges."""
        if not scores:
            return []

        ranges = [
            (0, 40, 'Below 40'),
            (40, 60, '40-60'),
            (60, 75, '60-75'),
            (75, 85, '75-85'),
            (85, 100, '85-100'),
        ]

        distribution = []
        for min_score, max_score, label in ranges:
            count = len([s for s in scores if min_score <= s < max_score or (s == 100 and max_score == 100)])
            distribution.append({
                'label': label,
                'count': count,
                'percentage': (count / len(scores) * 100) if scores else 0,
            })

        return distribution


class ClientSettingsView(LoginRequiredMixin, View):
    """Account settings and preferences page."""
    template_name = "clients/settings.html"
    login_url = reverse_lazy("clients:login")

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "client_account"):
            return redirect("clients:login")
        client = request.user.client_account
        if not client.company_name:
            return redirect("clients:complete_profile")
        if client.status != "approved":
            messages.info(request, "Your account is still pending approval.")
            return redirect("clients:pending_approval")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self):
        account = self.request.user.client_account

        # Get recent webhook deliveries
        recent_deliveries = []
        if account.role in ROLE_BRANDING_ACCESS:
            recent_deliveries = account.webhook_deliveries.order_by('-created_at')[:10]

        return {
            'account': account,
            'is_manager': account.role == 'manager',
            'can_manage_branding': account.role in ROLE_BRANDING_ACCESS,
            'role_label': dict(ClientAccount.ROLE_CHOICES).get(account.role, account.role.title()),
            'password_form': ClientPasswordChangeForm(user=self.request.user),
            'email_form': EmailPreferencesForm(instance=account),
            'recent_deliveries': recent_deliveries,
        }

    def get(self, request, *args, **kwargs):
        from django.shortcuts import render
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        from django.shortcuts import render
        from django.contrib.auth import update_session_auth_hash

        account = request.user.client_account
        action = request.POST.get("action", "")
        context = self.get_context_data()

        if action == "change_password":
            password_form = ClientPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                # Keep user logged in after password change
                update_session_auth_hash(request, request.user)
                messages.success(request, "Your password has been changed successfully.")
                return redirect("clients:settings")
            else:
                context['password_form'] = password_form
                messages.error(request, "Please correct the errors below.")

        elif action == "update_email_preferences":
            email_form = EmailPreferencesForm(data=request.POST, instance=account)
            if email_form.is_valid():
                email_form.save()
                messages.success(request, "Your email preferences have been updated.")
                return redirect("clients:settings")
            else:
                context['email_form'] = email_form
                messages.error(request, "Please correct the errors below.")

        elif action == "update_branding":
            # Handle branding settings update
            if account.role not in ROLE_BRANDING_ACCESS:
                messages.error(request, "You don't have permission to modify branding settings.")
                return redirect("clients:settings")

            # Validate and update color settings (available to all plans)
            import re
            _hex_re = re.compile(r'^#[0-9A-Fa-f]{6}$')
            def _safe_color(val, default):
                return val if val and _hex_re.match(val) else default

            account.brand_primary_color = _safe_color(request.POST.get("brand_primary_color"), "#ff8a00")
            account.brand_secondary_color = _safe_color(request.POST.get("brand_secondary_color"), "#0e1428")
            account.brand_background_color = _safe_color(request.POST.get("brand_background_color"), "#ffffff")

            # Sanitize text settings to prevent stored XSS
            from django.utils.html import escape
            account.custom_welcome_message = escape(request.POST.get("custom_welcome_message", "").strip()[:500])
            account.custom_footer_text = escape(request.POST.get("custom_footer_text", "").strip()[:200])

            # Pro/Enterprise only features
            if account.can_use_white_labeling:
                account.custom_email_sender_name = escape(request.POST.get("custom_email_sender_name", "").strip()[:100])
                account.hide_evalon_branding = request.POST.get("hide_evalon_branding") == "on"

            account.save(update_fields=[
                "brand_primary_color",
                "brand_secondary_color",
                "brand_background_color",
                "custom_welcome_message",
                "custom_footer_text",
                "custom_email_sender_name",
                "hide_evalon_branding",
                "updated_at",
            ])
            messages.success(request, "Your branding settings have been saved.")
            return redirect("clients:settings")

        elif action == "update_webhooks":
            # Handle webhook settings update
            if account.role not in ROLE_BRANDING_ACCESS:
                messages.error(request, "You don't have permission to modify webhook settings.")
                return redirect("clients:settings")

            webhook_url = request.POST.get("webhook_url", "").strip()[:2000]
            webhook_enabled = request.POST.get("webhook_enabled") == "on"
            ALLOWED_WEBHOOK_EVENTS = {
                "session.created", "session.started",
                "session.completed", "session.expired",
            }
            webhook_events = [
                e for e in request.POST.getlist("webhook_events")
                if e in ALLOWED_WEBHOOK_EVENTS
            ]

            # Validate webhook URL if provided
            if webhook_url and not webhook_url.startswith("https://"):
                messages.error(request, "Webhook URL must use HTTPS for security.")
                return redirect("clients:settings")

            if webhook_url and is_ssrf_target(webhook_url):
                messages.error(request, "Webhook URL must not point to internal or private addresses.")
                return redirect("clients:settings")

            account.webhook_url = webhook_url
            account.webhook_enabled = webhook_enabled and bool(webhook_url)
            account.webhook_events = webhook_events

            # Generate secret if enabling webhooks for first time
            if account.webhook_enabled and not account.webhook_secret:
                account.generate_webhook_secret()

            account.save(update_fields=[
                "webhook_url",
                "webhook_enabled",
                "webhook_events",
                "webhook_secret",
                "updated_at",
            ])
            messages.success(request, "Your webhook settings have been saved.")
            return redirect("clients:settings")

        elif action == "generate_webhook_secret":
            if account.role not in ROLE_BRANDING_ACCESS:
                messages.error(request, "You don't have permission to modify webhook settings.")
                return redirect("clients:settings")

            account.generate_webhook_secret()
            messages.success(request, "A new webhook signing secret has been generated.")
            return redirect("clients:settings")

        elif action == "generate_api_key":
            if account.role not in ROLE_BRANDING_ACCESS:
                messages.error(request, "You don't have permission to generate API keys.")
                return redirect("clients:settings")

            account.generate_api_key()
            messages.success(request, "Your new API key has been generated. Copy it now from the field below — it won't be shown again.")
            return redirect("clients:settings")

        elif action == "revoke_api_key":
            if account.role not in ROLE_BRANDING_ACCESS:
                messages.error(request, "You don't have permission to revoke API keys.")
                return redirect("clients:settings")

            account.api_key = ""
            account.api_key_created_at = None
            account.save(update_fields=["api_key", "api_key_created_at", "updated_at"])
            messages.success(request, "Your API key has been revoked.")
            return redirect("clients:settings")

        elif action == "test_webhook":
            if account.role not in ROLE_BRANDING_ACCESS:
                messages.error(request, "You don't have permission to test webhooks.")
                return redirect("clients:settings")

            if not account.has_webhook_configured:
                messages.error(request, "Please configure and save your webhook settings first.")
                return redirect("clients:settings")

            # Send a test webhook
            from .services import send_webhook
            test_data = {
                "test": True,
                "message": "This is a test webhook from Evalon",
                "client": {
                    "company_name": account.company_name,
                },
            }
            success = send_webhook(account, "test.ping", test_data)
            if success:
                messages.success(request, "Test webhook sent successfully! Check your endpoint.")
            else:
                messages.error(request, "Failed to send test webhook. Please check your URL and try again.")
            return redirect("clients:settings")

        elif action == "upload_logo":
            if account.role not in ROLE_BRANDING_ACCESS:
                messages.error(request, "Only managers can update branding.")
                return redirect("clients:settings")
            form = ClientLogoForm(request.POST, request.FILES)
            if form.is_valid():
                account.logo = form.cleaned_data["logo"]
                account.save()
                messages.success(request, "Logo updated.")
            else:
                messages.error(request, "Invalid logo file. Please use PNG or JPG, max 2MB.")
            return redirect("clients:settings")

        elif action == "remove_logo":
            if account.role not in ROLE_BRANDING_ACCESS:
                messages.error(request, "Only managers can update branding.")
                return redirect("clients:settings")
            if account.has_logo:
                account.clear_logo()
                account.save(update_fields=["logo", "logo_data", "logo_mime"])
            messages.info(request, "Logo removed.")
            return redirect("clients:settings")

        return render(request, self.template_name, context)


class ClientActivityExportView(LoginRequiredMixin, View):
    login_url = reverse_lazy("clients:login")

    def get(self, request, *args, **kwargs):
        if not hasattr(request.user, "client_account"):
            return redirect("clients:login")
        account = request.user.client_account
        if not account.company_name:
            return redirect("clients:complete_profile")
        if account.status != "approved":
            messages.error(request, "Your account is not approved yet.")
            return redirect("clients:pending_approval")
        filters = parse_activity_filters(request.GET)
        dataset_map = build_dataset_map(account)
        activity_rows = build_activity_feed(account, dataset_map, filters, activity_limit=None)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=assessment-activity.csv"
        writer = csv.writer(response)
        writer.writerow(["Candidate", "Assessment", "Status", "Updated", "Report URL", "Manage URL"])
        for row in activity_rows:
            timestamp = row.get("timestamp")
            writer.writerow(
                [
                    row.get("candidate"),
                    row.get("assessment"),
                    row.get("status"),
                    timestamp.strftime("%Y-%m-%d %H:%M") if timestamp else "",
                    row.get("detail_url") or "",
                    row.get("manage_url") or "",
                ]
            )
        return response




class ClientAssessmentMixin(LoginRequiredMixin):
    login_url = reverse_lazy("clients:login")
    assessment_type: str
    requires_manager_access = False
    allowed_roles: set[str] | None = None

    ASSESSMENT_CONFIG = {
        "marketing": {
            "label": "Marketing Assessment",
            "form_class": ClientMarketingInviteForm,
            "session_model": DigitalMarketingAssessmentSession,
            "candidate_route": "candidate:marketing-session",
        },
        "product": {
            "label": "Product Management Assessment",
            "form_class": ClientProductInviteForm,
            "session_model": ProductAssessmentSession,
            "candidate_route": "candidate:pm-session",
        },
        "behavioral": {
            "label": "Behavioral Assessment",
            "form_class": ClientBehavioralInviteForm,
            "session_model": BehavioralAssessmentSession,
            "candidate_route": "candidate:behavioral-session",
        },
        "ux_design": {
            "label": "UX/UI Design Assessment",
            "form_class": ClientUXDesignInviteForm,
            "session_model": UXDesignAssessmentSession,
            "candidate_route": "candidate:ux-session",
        },
        "hr": {
            "label": "HR Assessment",
            "form_class": ClientHRInviteForm,
            "session_model": HRAssessmentSession,
            "candidate_route": "candidate:hr-session",
        },
        "finance": {
            "label": "Finance Manager Assessment",
            "form_class": ClientFinanceInviteForm,
            "session_model": FinanceAssessmentSession,
            "candidate_route": "candidate:finance-session",
        },
    }

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "client_account"):
            return redirect("clients:login")
        self.account = request.user.client_account
        self.is_manager = self.account.role == "manager"
        if not self.account.company_name:
            return redirect("clients:complete_profile")
        if self.account.status != "approved":
            messages.info(request, "Your account is pending approval.")
            return redirect("clients:pending_approval")
        assessment_type = kwargs.get("assessment_type")
        if assessment_type not in self.ASSESSMENT_CONFIG:
            raise Http404
        if assessment_type not in self.account.approved_assessments:
            messages.error(request, "You do not have access to that assessment.")
            return redirect("clients:dashboard")
        if self.allowed_roles and self.account.role not in self.allowed_roles:
            messages.error(request, "You do not have access to this workspace.")
            return redirect("clients:dashboard")
        self.assessment_type = assessment_type
        self.assessment_config = self.ASSESSMENT_CONFIG[assessment_type]
        self.can_manage_invites = self.account.role in ROLE_INVITE_ACCESS
        self.can_add_notes = self.account.role in ROLE_NOTE_ACCESS
        self.can_record_decision = self.account.role in ROLE_DECISION_ACCESS
        self._activate_scheduled_invites()
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        return self.assessment_config["form_class"]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["client"] = self.account
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        project = self.get_selected_project()
        if project:
            initial["project"] = project
        return initial

    def get_success_url(self):
        url = reverse("clients:assessment-manage", args=[self.assessment_type])
        project = self.request.GET.get("project") or self.request.POST.get("project_filter")
        if project:
            url = f"{url}?project={project}"
        return url

    def sessions(self):
        model = self.assessment_config["session_model"]
        qs = model.objects.filter(client=self.account)
        project = self.get_selected_project()
        if project:
            qs = qs.filter(project=project)
        return qs.order_by("-created_at")

    def build_share_link(self, session):
        route = self.assessment_config["candidate_route"]
        return self.request.build_absolute_uri(reverse(route, args=[session.uuid]))

    def get_session_object(self, session_uuid):
        model = self.assessment_config["session_model"]
        try:
            return model.objects.get(client=self.account, uuid=session_uuid)
        except model.DoesNotExist:
            raise Http404

    def _activate_scheduled_invites(self):
        model = self.assessment_config["session_model"]
        now = timezone.now()
        scheduled = model.objects.filter(
            client=self.account,
            status="draft",
            scheduled_for__isnull=False,
            scheduled_for__lte=now,
        )[:50]  # batch limit to avoid long request blocking
        for session in scheduled:
            session.status = "in_progress"
            session.scheduled_for = None
            session.started_at = None
            session.save(update_fields=["status", "scheduled_for", "started_at"])
            self._dispatch_candidate_invite_email(session)

    def get_selected_project(self):
        if hasattr(self, "_selected_project"):
            return self._selected_project
        project_uuid = self.request.GET.get("project") or self.request.POST.get("project_filter")
        project = None
        if project_uuid:
            try:
                project = self.account.projects.get(uuid=project_uuid)
            except ClientProject.DoesNotExist:
                project = None
        self._selected_project = project
        return project

    def _candidate_email_from_identifier(self, identifier: str | None) -> str | None:
        if not identifier:
            return None
        identifier = identifier.strip()
        try:
            validate_email(identifier)
        except ValidationError:
            return None
        return identifier.lower()

    def _dispatch_candidate_invite_email(self, session):
        email = self._candidate_email_from_identifier(getattr(session, "candidate_id", ""))
        if not email:
            return "invalid"
        if not getattr(settings, "EMAIL_ENABLED", False):
            return "disabled"
        route = self.assessment_config.get("candidate_route")
        if not route:
            return "no_route"

        # Build assessment URLs
        start_link = self.request.build_absolute_uri(reverse(route, args=[session.uuid]))
        session_link = start_link  # Same link for now

        # Extract candidate first name from email if possible
        candidate_first_name = email.split('@')[0].split('.')[0].title()

        # Calculate deadline based on deadline_type
        due_at = None
        if hasattr(session, 'deadline_type'):
            if session.deadline_type == 'absolute':
                due_at = session.deadline_at
            elif session.deadline_type == 'relative' and session.deadline_days:
                from datetime import timedelta
                from django.utils import timezone as tz
                # Calculate from scheduled_for or now
                base_time = session.scheduled_for or tz.now()
                due_at = base_time + timedelta(days=session.deadline_days)

        # Prepare email context
        context = {
            'company_name': self.account.company_name,
            'invited_by': self.account.company_name,
            'candidate': {
                'first_name': candidate_first_name,
            },
            'assessment': {
                'title': self.assessment_config['label'],
            },
            'start_link': start_link,
            'session_link': session_link,
            'due_at': due_at,
            'notes': getattr(session, 'notes', ''),
            # Client branding
            'brand_primary': self.account.brand_primary_color or '#ff8a00',
            'brand_secondary': self.account.brand_secondary_color or '#0e1428',
            'hide_evalon_branding': self.account.hide_evalon_branding,
            'client_footer_text': self.account.get_footer_text(),
        }

        # Render HTML and text versions
        subject = f"{self.account.company_name} invited you to the {self.assessment_config['label']}"
        html_body = render_to_string('emails/invite_candidate.html', context)
        text_body = strip_tags(html_body)

        # Send email with HTML
        try:
            msg = EmailMultiAlternatives(
                subject,
                text_body,
                getattr(settings, "DEFAULT_FROM_EMAIL", None),
                [email],
            )
            msg.attach_alternative(html_body, "text/html")
            msg.send()
            return "sent"
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to email invite for session %s: %s", session.uuid, exc)
            return "error"

    def _invite_feedback_message(self, session, email_status: str) -> str:
        if email_status == "sent":
            return f"Invite emailed to {session.candidate_id}."
        if email_status == "invalid":
            return f"Invite ready. Share the secure link with {session.candidate_id}."
        if email_status == "disabled":
            return (
                "Invite ready, but email delivery is disabled. Configure email settings or share the link manually."
            )
        if email_status == "error":
            return f"Invite ready, but we could not email {session.candidate_id}. Share the link manually."
        if email_status == "scheduled":
            return "Invite scheduled. We'll email the candidate when it launches."
        return f"Invite ready. Share the secure link with {session.candidate_id}."


class ClientAssessmentManageView(ClientAssessmentMixin, FormView):
    template_name = "clients/assessments/manage.html"
    bulk_form_class = ClientBulkInviteForm
    allowed_roles = ROLE_INVITE_ACCESS

    def form_valid(self, form):
        if not self.can_manage_invites:
            messages.error(self.request, "You do not have permission to create invites.")
            return redirect(self.get_success_url())
        session = form.save()

        # Trigger webhook for session created
        from clients.services import trigger_session_webhook
        trigger_session_webhook(session, "session.created")

        if session.status == "in_progress":
            email_status = self._dispatch_candidate_invite_email(session)
        elif session.status == "draft" and session.scheduled_for:
            email_status = "scheduled"
        else:
            email_status = "invalid"
        messages.success(self.request, self._invite_feedback_message(session, email_status))
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "bulk_upload":
            if not self.is_manager:
                messages.error(request, "Only managers can upload invites.")
                return redirect(self.get_success_url())
            bulk_form = self.bulk_form_class(request.POST, request.FILES, client=self.account)
            if bulk_form.is_valid():
                created, errors = self._process_bulk_upload(
                    bulk_form.cleaned_data["csv_file"],
                    bulk_form.cleaned_data["project"],
                )
                if created:
                    messages.success(request, f"Created {created} invite{'' if created == 1 else 's'}.")
                if errors:
                    messages.warning(request, f"Issues with rows: {', '.join(errors[:5])}")
                return redirect(self.get_success_url())
            context = self.get_context_data(form=self.get_form(), bulk_form=bulk_form)
            return self.render_to_response(context, status=400)
        elif action == "send_reminder":
            if not self.can_manage_invites:
                messages.error(request, "You do not have permission to send reminders.")
                return redirect(self.get_success_url())
            self._trigger_reminder(request.POST.get("session_uuid"))
            return redirect(self.get_success_url())
        elif action == "launch_now":
            if not self.can_manage_invites:
                messages.error(self.request, "You do not have permission to launch invites.")
                return redirect(self.get_success_url())
            self._launch_now(request.POST.get("session_uuid"))
            return redirect(self.get_success_url())
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_rows = []
        sessions = list(self.sessions())
        note_lookup = {
            row["session_uuid"]: row
            for row in ClientSessionNote.objects.filter(
                client=self.account,
                assessment_type=self.assessment_type,
                session_uuid__in=[session.uuid for session in sessions],
            )
            .values("session_uuid")
            .annotate(
                note_count=models.Count("id"),
                needs_review_count=models.Count("id", filter=models.Q(needs_review=True)),
            )
        }
        decision_lookup = {
            row["session_uuid"]: row
            for row in ClientSessionNote.objects.filter(
                client=self.account,
                assessment_type=self.assessment_type,
                session_uuid__in=[session.uuid for session in sessions],
                note_type="decision",
                decision__gt="",
            )
            .values("session_uuid")
            .annotate(
                advance=models.Count("id", filter=models.Q(decision="advance")),
                hold=models.Count("id", filter=models.Q(decision="hold")),
                reject=models.Count("id", filter=models.Q(decision="reject")),
            )
        }
        for session in sessions:
            score = getattr(session, "overall_score", None)
            if score is None:
                score = getattr(session, "hard_skill_score", None)
            if score is None:
                score = getattr(session, "eligibility_score", None)
            note_meta = note_lookup.get(session.uuid, {})
            decision_meta = decision_lookup.get(session.uuid, {})
            decision_label = ""
            if decision_meta:
                options = {
                    "advance": decision_meta.get("advance", 0),
                    "hold": decision_meta.get("hold", 0),
                    "reject": decision_meta.get("reject", 0),
                }
                best = max(options.items(), key=lambda item: item[1])
                if best[1]:
                    decision_label = f"{best[0].title()} ({best[1]})"
            project = session.project
            session_rows.append(
                {
                    "candidate": session.candidate_id,
                    "status": session.get_status_display(),
                    "status_code": session.status,
                    "score": score,
                    "submitted_at": session.submitted_at,
                    "share_link": self.build_share_link(session),
                    "detail_url": reverse(
                        "clients:assessment-detail", args=[self.assessment_type, session.uuid]
                    )
                    if session.status == "submitted"
                    else None,
                    "notes": note_meta.get("note_count", 0),
                    "needs_review": note_meta.get("needs_review_count", 0) > 0,
                    "scheduled_for": session.scheduled_for,
                    "last_reminder_at": session.last_reminder_at,
                    "reminder_count": session.reminder_count,
                    "uuid": session.uuid,
                    "decision_summary": decision_label,
                    "project_title": project.title if project else "Unassigned",
                    "project_url": reverse("clients:project-detail", args=[project.uuid])
                    if project
                    else None,
                }
            )
        bulk_form = context.get("bulk_form")
        if not bulk_form:
            bulk_form = self.bulk_form_class(client=self.account, initial={"project": self.get_selected_project()})
        selected_project = self.get_selected_project()
        context.update(
            {
                "assessment_label": self.assessment_config["label"],
                "sessions": session_rows,
                "bulk_form": bulk_form,
                "projects": self.account.projects.order_by("-created_at"),
                "selected_project": selected_project,
                "has_projects": self.account.projects.exists(),
            }
        )
        return context

    def _process_bulk_upload(self, csv_file, project: ClientProject) -> tuple[int, list[str]]:
        created = 0
        errors: list[str] = []
        csv_file.seek(0)
        decoded = io.TextIOWrapper(csv_file.file, encoding="utf-8")
        reader = csv.DictReader(decoded)
        default_duration = self.get_form_class().base_fields["duration_minutes"].initial or 30
        remaining = self.account.invites_remaining()
        if remaining is not None and remaining <= 0:
            return 0, ["Invite quota reached. Upgrade your plan or wait for the next cycle."]
        for idx, row in enumerate(reader, start=1):
            if remaining is not None and remaining <= 0:
                errors.append("Invite quota reached. Remaining rows were skipped.")
                break
            candidate = row.get("candidate_id") or row.get("candidate_identifier") or row.get("email")
            if not candidate:
                errors.append(f"row {idx}: missing candidate_id")
                continue
            duration = row.get("duration_minutes") or row.get("duration") or default_duration
            send_at = row.get("send_at") or row.get("scheduled_for")
            form_data = {
                "candidate_identifier": candidate,
                "duration_minutes": duration,
                "send_at": send_at,
                "project": str(project.pk),
            }
            form = self.get_form_class()(data=form_data, client=self.account)
            if form.is_valid():
                if remaining is not None and remaining <= 0:
                    errors.append("Invite quota reached. Remaining rows were skipped.")
                    break
                session = form.save()
                if session.status == "in_progress":
                    self._dispatch_candidate_invite_email(session)
                created += 1
                if remaining is not None:
                    remaining -= 1
            else:
                error_text = "; ".join(
                    [msg for messages in form.errors.values() for msg in messages]
                )
                errors.append(f"row {idx}: {error_text}")
        return created, errors

    def _trigger_reminder(self, session_uuid: str | None):
        if not session_uuid:
            return
        session = self.get_session_object(session_uuid)
        if session.status != "in_progress":
            messages.error(self.request, "Reminders are only available for active candidates.")
            return
        session.last_reminder_at = timezone.now()
        session.reminder_count = (session.reminder_count or 0) + 1
        session.save(update_fields=["last_reminder_at", "reminder_count"])
        messages.success(self.request, f"Reminder logged for {session.candidate_id}.")

    def _launch_now(self, session_uuid: str | None):
        if not session_uuid:
            return
        session = self.get_session_object(session_uuid)
        if session.status != "draft" or not session.scheduled_for:
            messages.info(self.request, "Invite already active.")
            return
        session.status = "in_progress"
        session.scheduled_for = None
        session.save(update_fields=["status", "scheduled_for"])
        email_status = self._dispatch_candidate_invite_email(session)
        messages.success(self.request, self._invite_feedback_message(session, email_status))


class ClientAssessmentDetailView(ClientAssessmentMixin, FormView):
    template_name = "clients/assessments/detail.html"
    form_class = ClientSessionNoteForm
    requires_manager_access = False

    def _ensure_session(self, request, **kwargs):
        try:
            session = self.get_session_object(kwargs.get("session_uuid"))
        except Http404:
            messages.error(request, "That assessment could not be found.")
            return redirect("clients:assessment-manage", assessment_type=kwargs.get("assessment_type"))
        if session.status != "submitted":
            messages.info(request, "This report becomes available once the candidate submits.")
            return redirect("clients:assessment-manage", assessment_type=kwargs.get("assessment_type"))
        self.session_obj = session
        return None

    def get(self, request, *args, **kwargs):
        response = self._ensure_session(request, **kwargs)
        if response:
            return response
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = self._ensure_session(request, **kwargs)
        if response:
            return response
        action = request.POST.get("action")
        if action == "quick_decision" and self.can_record_decision:
            decision = request.POST.get("decision")
            valid_decisions = {choice[0] for choice in ClientSessionNote.DECISION_CHOICES}
            if decision in valid_decisions:
                note_text = request.POST.get("note", "").strip()
                ClientSessionNote.objects.create(
                    client=self.account,
                    assessment_type=self.assessment_type,
                    session_uuid=self.session_obj.uuid,
                    candidate_id=self.session_obj.candidate_id,
                    note=note_text,
                    note_type="decision",
                    decision=decision,
                    author=self.request.user,
                    author_role=self.account.role,
                )
                messages.success(request, f"Decision '{decision.title()}' recorded.")
                return redirect(self.get_success_url())
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = getattr(self, "session_obj", None)
        report = build_session_report(session, self.assessment_type)
        decision_summary = list(
            ClientSessionNote.objects.filter(
                client=self.account,
                assessment_type=self.assessment_type,
                session_uuid=session.uuid,
                note_type="decision",
                decision__gt="",
            )
            .values("decision")
            .annotate(count=models.Count("id"))
        )
        recommended_decision = None
        if decision_summary:
            recommended_decision = max(decision_summary, key=lambda item: item["count"])
        share_link = self.build_share_link(session)
        context.update(
            {
                "assessment_label": self.assessment_config["label"],
                "session_obj": session,
                "share_link": share_link,
                "report": report,
                "assessment_type": self.assessment_type,
                "note_form": context.get("form") or self.get_form(),
                "notes": ClientSessionNote.objects.filter(
                    client=self.account,
                    assessment_type=self.assessment_type,
                    session_uuid=session.uuid,
                ),
                "can_edit_notes": self.can_add_notes,
                "can_record_decision": self.can_record_decision,
                "decision_summary": decision_summary,
                "recommended_decision": recommended_decision,
                "actionable_summary": build_actionable_summary(report, decision_summary, recommended_decision),
                "response_drilldown": build_response_drilldown(session),
                "activity_timeline": build_activity_timeline(session),
                "comparative_insights": build_comparative_insights(session),
                "quick_followups": build_followup_links(session, share_link),
                "candidate_feedback": build_candidate_feedback(session),
                "integrity_signals": build_integrity_signals(session),
                "pdf_export_url": reverse(
                    "clients:assessment-export",
                    args=[self.assessment_type, session.uuid],
                ),
                "audit_log": build_audit_log(session, self.account),
            }
        )
        return context


class ClientProjectAccessMixin(LoginRequiredMixin):
    login_url = reverse_lazy("clients:login")

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "client_account"):
            return redirect("clients:login")
        self.account = request.user.client_account
        if not self.account.company_name:
            return redirect("clients:complete_profile")
        if self.account.status != "approved":
            messages.info(request, "Your account is pending approval.")
            return redirect("clients:pending_approval")
        return super().dispatch(request, *args, **kwargs)


class ClientProjectListView(ClientProjectAccessMixin, TemplateView):
    template_name = "clients/projects/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tab = self.request.GET.get("tab", "positions")
        context["active_tab"] = tab

        # Positions data (always needed for count badge)
        dataset_map = build_dataset_map(self.account)
        project_health = build_project_health_map(self.account, dataset_map)
        projects = list(self.account.projects.order_by("-created_at"))
        for project in projects:
            project.health = project_health.get(project.id, _default_project_health(project))
        context["projects"] = projects
        context["project_health_map"] = project_health

        # Campaigns data
        campaigns = self.account.campaigns.all()
        for campaign in campaigns:
            campaign.pos_count = campaign.position_count
            campaign.active_count = campaign.active_position_count
        context["campaigns"] = campaigns
        context["campaign_form"] = getattr(self, "campaign_form", HiringProjectForm(client=self.account))

        context["is_manager"] = self.account.role == "manager"
        return context

    def post(self, request, *args, **kwargs):
        if self.account.role != "manager":
            messages.error(request, "Only managers can create projects.")
            return redirect("clients:project-list")
        form = HiringProjectForm(request.POST, client=self.account)
        if form.is_valid():
            campaign = form.save()
            messages.success(request, f'Project "{campaign.name}" created.')
            return redirect("clients:campaign-detail", campaign_uuid=campaign.uuid)
        self.campaign_form = form
        return self.render_to_response(self.get_context_data(), status=400)


class ClientProjectCreateView(ClientProjectAccessMixin, TemplateView):
    template_name = "clients/projects/edit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = None
        context["is_create"] = True
        context["form"] = getattr(self, "form", ClientProjectForm(client=self.account))
        return context

    def post(self, request, *args, **kwargs):
        remaining = self.account.remaining_projects()
        if remaining is not None and remaining <= 0:
            messages.error(
                request,
                "Your current plan reached the active position limit. Archive a position or upgrade to add more.",
            )
            return redirect("clients:project-list")
        if self.account.role != "manager":
            messages.error(request, "Only managers can create positions.")
            return redirect("clients:project-list")
        form = ClientProjectForm(request.POST, client=self.account)
        if form.is_valid():
            project = form.save()
            messages.success(request, "Position created.")
            return redirect("clients:project-detail", project_uuid=project.uuid)
        self.form = form
        return self.render_to_response(self.get_context_data(), status=400)


class ClientProjectDetailView(ClientProjectAccessMixin, TemplateView):
    template_name = "clients/projects/detail.html"

    def get_project(self):
        if not hasattr(self, "_project"):
            self._project = get_object_or_404(
                self.account.projects, uuid=self.kwargs.get("project_uuid")
            )
        return self._project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        dataset_map = build_dataset_map(self.account)
        project_health_map = build_project_health_map(self.account, dataset_map)
        project_health = project_health_map.get(project.id, _default_project_health(project))
        assessment_details = []
        recent_sessions = []
        pipeline_columns = [
            {"key": key, "label": PIPELINE_STAGE_LABELS.get(key, key.title()), "sessions": []}
            for key in PIPELINE_STAGE_KEYS
        ]
        pipeline_lookup = {column["key"]: column["sessions"] for column in pipeline_columns}
        for code, queryset in dataset_map.items():
            label = ClientAccount.ASSESSMENT_DETAILS.get(code, {}).get("label", code.title())
            qs = queryset.filter(project=project)
            total = qs.count()
            if total:
                assessment_details.append(
                    {
                        "label": label,
                        "total": total,
                        "submitted": qs.filter(status="submitted").count(),
                        "in_progress": qs.filter(status="in_progress").count(),
                        "draft": qs.filter(status="draft").count(),
                    }
                )
            for session in qs.order_by("-updated_at")[:50]:
                stage = normalize_pipeline_stage(session)
                score = getattr(session, "overall_score", None)
                if score is None:
                    score = getattr(session, "eligibility_score", None)
                card = {
                    "candidate": session.candidate_id,
                    "assessment": label,
                    "assessment_code": code,
                    "stage": stage,
                    "status": session.get_status_display(),
                    "status_slug": session.status,
                    "score": score,
                    "level": getattr(session, "level", "mid"),
                    "level_display": session.get_level_display() if hasattr(session, "get_level_display") else "Mid-Level",
                    "updated_at": session.pipeline_stage_updated_at
                    or session.updated_at
                    or session.created_at,
                    "detail_url": reverse("clients:assessment-detail", args=[code, session.uuid])
                    if session.status == "submitted"
                    else None,
                    "stage_url": reverse(
                        "clients:project-pipeline-update", args=[project.uuid, code, session.uuid]
                    ),
                }
                pipeline_lookup.get(stage, pipeline_columns[0]["sessions"]).append(card)
                recent_sessions.append(
                    {
                        "candidate": session.candidate_id,
                        "assessment": label,
                        "status": session.get_status_display(),
                        "level": getattr(session, "level", "mid"),
                        "level_display": session.get_level_display() if hasattr(session, "get_level_display") else "Mid-Level",
                        "updated_at": session.updated_at or session.created_at,
                        "detail_url": reverse("clients:assessment-detail", args=[code, session.uuid])
                        if session.status == "submitted"
                        else None,
                    }
                )
        recent_sessions.sort(key=lambda item: item["updated_at"], reverse=True)
        for column in pipeline_columns:
            column["count"] = len(column["sessions"])
        context.update(
            {
                "project": project,
                "project_health": project_health,
                "pipeline_columns": pipeline_columns,
                "pipeline_stage_choices": PIPELINE_STAGE_CHOICES,
                "can_edit_pipeline": self.account.role in ROLE_INVITE_ACCESS,
                "assessment_details": assessment_details,
                "recent_sessions": recent_sessions[:20],
            }
        )
        return context


class ClientProjectEditView(ClientProjectAccessMixin, TemplateView):
    template_name = "clients/projects/edit.html"

    def get_project(self):
        if not hasattr(self, "_project"):
            self._project = get_object_or_404(
                self.account.projects, uuid=self.kwargs.get("project_uuid")
            )
        return self._project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["project"] = project
        context["form"] = getattr(
            self, "form",
            ClientProjectForm(instance=project, client=self.account),
        )
        return context

    def post(self, request, *args, **kwargs):
        if self.account.role != "manager":
            messages.error(request, "Only managers can edit positions.")
            return redirect("clients:project-detail", project_uuid=self.kwargs["project_uuid"])
        project = self.get_project()
        form = ClientProjectForm(request.POST, instance=project, client=self.account)
        if form.is_valid():
            form.save()
            messages.success(request, "Position updated.")
            return redirect("clients:project-detail", project_uuid=project.uuid)
        self.form = form
        return self.render_to_response(self.get_context_data(), status=400)


class ClientProjectCloneView(ClientProjectAccessMixin, FormView):
    template_name = "clients/projects/clone.html"
    form_class = ClientProjectForm

    def dispatch(self, request, *args, **kwargs):
        if self.account.role != "manager":
            messages.error(request, "Only managers can duplicate positions.")
            return redirect("clients:project-list")
        self.source_project = get_object_or_404(
            self.account.projects, uuid=kwargs.get("project_uuid")
        )
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        data = model_to_dict(
            self.source_project,
            fields=[
                "title",
                "role_level",
                "department",
                "location",
                "employment_type",
                "work_model",
                "salary_min",
                "salary_max",
                "salary_currency",
                "required_skills",
                "priority",
                "status",
                "open_roles",
                "target_start_date",
                "description",
                "published",
            ],
        )
        data["title"] = f"{self.source_project.title} copy"
        return data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["client"] = self.account
        return kwargs

    def form_valid(self, form):
        project = form.save()
        messages.success(
            self.request,
            f"Created '{project.title}' based on {self.source_project.title}.",
        )
        return redirect("clients:project-detail", project_uuid=project.uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dataset_map = build_dataset_map(self.account)
        project_health = build_project_health_map(self.account, dataset_map).get(
            self.source_project.id, _default_project_health(self.source_project)
        )
        context.update(
            {
                "source_project": self.source_project,
                "project_health": project_health,
            }
        )
        return context


class ClientProjectPipelineStageView(ClientProjectAccessMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        if self.account.role not in ROLE_INVITE_ACCESS:
            messages.error(request, "Only managers or recruiters can update stages.")
            return redirect("clients:project-detail", project_uuid=kwargs.get("project_uuid"))
        project = get_object_or_404(self.account.projects, uuid=kwargs.get("project_uuid"))
        assessment_type = kwargs.get("assessment_type")
        session_uuid = kwargs.get("session_uuid")
        model = ASSESSMENT_MODEL_MAP.get(assessment_type)
        if model is None:
            raise Http404("Unknown assessment.")
        session = get_object_or_404(
            model.objects.filter(client=self.account, project=project), uuid=session_uuid
        )
        next_stage = request.POST.get("stage")
        if next_stage not in PIPELINE_STAGE_LABELS:
            messages.error(request, "Invalid pipeline stage.")
            return redirect("clients:project-detail", project_uuid=project.uuid)
        session.pipeline_stage = next_stage
        session.pipeline_stage_updated_at = timezone.now()
        session.save(update_fields=["pipeline_stage", "pipeline_stage_updated_at"])
        messages.success(
            request,
            f"Moved {session.candidate_id} to {PIPELINE_STAGE_LABELS[next_stage]}.",
        )
        return redirect(f"{reverse('clients:project-detail', args=[project.uuid])}#pipeline")

    def form_valid(self, form):
        session = getattr(self, "session_obj", None)
        if not self.can_add_notes and form.cleaned_data.get("note_type") != "decision":
            messages.error(self.request, "You do not have permission to add notes.")
            return redirect(self.get_success_url())
        if (
            form.cleaned_data.get("note_type") == "decision"
            and not self.can_record_decision
        ):
            messages.error(self.request, "You do not have permission to record decisions.")
            return redirect(self.get_success_url())
        note = form.save(commit=False)
        note.client = self.account
        note.assessment_type = self.assessment_type
        note.session_uuid = session.uuid
        note.candidate_id = session.candidate_id
        note.author = self.request.user
        note.author_role = self.account.role
        note.save()
        messages.success(self.request, "Note saved.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("clients:assessment-detail", args=[self.assessment_type, self.kwargs.get("session_uuid")])


def build_response_drilldown(session):
    questions = session.question_set or []
    responses = session.responses or []
    breakdown = []
    for idx, question in enumerate(questions):
        resp = responses[idx] if idx < len(responses) else None
        if isinstance(resp, dict):
            answer = resp.get("answer") or resp.get("value") or resp.get("selection")
            is_correct = resp.get("is_correct")
            elapsed = resp.get("elapsed_seconds") or resp.get("time_spent")
        else:
            answer = resp
            is_correct = None
            elapsed = None
        prompt = question.get("question_text") if isinstance(question, dict) else None
        if not prompt and isinstance(question, dict):
            prompt = question.get("prompt") or question.get("title")
        if not prompt:
            prompt = f"Question {idx + 1}"
        category = question.get("category") if isinstance(question, dict) else ""
        outcome = "n/a"
        outcome_class = "neutral"
        if is_correct is True:
            outcome = "Correct"
            outcome_class = "positive"
        elif is_correct is False:
            outcome = "Incorrect"
            outcome_class = "warning"
        elif isinstance(resp, dict) and resp.get("score") is not None:
            outcome = f"Score {resp.get('score')}"
        if elapsed:
            elapsed = f"{float(elapsed):.1f}s"
        breakdown.append(
            {
                "prompt": prompt,
                "answer": answer or "—",
                "category": category,
                "elapsed": elapsed or "—",
                "outcome": outcome,
                "outcome_class": outcome_class,
            }
        )
    return breakdown


def build_activity_timeline(session):
    events = []
    if session.created_at:
        events.append(
            {"label": "Invite created", "timestamp": session.created_at, "description": "Assessment invite issued."}
        )
    if session.scheduled_for:
        events.append(
            {
                "label": "Scheduled",
                "timestamp": session.scheduled_for,
                "description": "Invite scheduled to send automatically.",
            }
        )
    if session.started_at:
        events.append(
            {"label": "Candidate started", "timestamp": session.started_at, "description": "Candidate opened the assessment."}
        )
    if session.last_reminder_at:
        events.append(
            {
                "label": "Reminder sent",
                "timestamp": session.last_reminder_at,
                "description": f"Reminder email #{session.reminder_count or 1} sent.",
            }
        )
    if session.paused_at:
        events.append(
            {"label": "Paused", "timestamp": session.paused_at, "description": "Candidate paused the assessment."}
        )
    if session.submitted_at:
        duration = None
        if session.started_at:
            total_minutes = (session.submitted_at - session.started_at).total_seconds() / 60
            duration = f"Completed in {total_minutes:.1f} minutes."
        events.append(
            {
                "label": "Submitted",
                "timestamp": session.submitted_at,
                "description": duration or "Candidate completed the assessment.",
            }
        )
    return events


def build_comparative_insights(session):
    if not session.client or not session.client.approved_assessments:
        return {}
    queryset = session.__class__.objects.filter(status="submitted", client=session.client)
    total_assessment = queryset.count()
    recent = queryset.filter(created_at__gte=timezone.now() - timedelta(days=30)).count()
    score_field = "overall_score"
    if not hasattr(session, "overall_score") or session.overall_score is None:
        if hasattr(session, "eligibility_score"):
            score_field = "eligibility_score"
    top_score = queryset.aggregate(models.Max(score_field)).get(f"{score_field}__max")
    cohort_score = queryset.aggregate(models.Avg(score_field)).get(f"{score_field}__avg")
    percentile = None
    candidate_score = getattr(session, score_field, None)
    if candidate_score is not None and total_assessment:
        better = queryset.filter(**{f"{score_field}__gt": candidate_score}).count()
        equal = queryset.filter(**{f"{score_field}": candidate_score}).count()
        cumulative = better + equal
        percentile = max(0, 100 - round((cumulative / total_assessment) * 100))
    return {
        "cohort_total": total_assessment,
        "cohort_recent": recent,
        "cohort_avg": cohort_score,
        "top_score": top_score,
        "candidate_score": candidate_score,
        "percentile": percentile,
    }


def build_followup_links(session, share_link):
    candidate = session.candidate_id
    subject = f"Next steps for {candidate}"
    base_body = f"Candidate report: {share_link}"
    return [
        {
            "label": "Schedule interview",
            "description": "Draft an email to schedule the next round.",
            "href": f"mailto:?subject={subject}%20-%20Interview&body={base_body}",
            "external": True,
        },
        {
            "label": "Request more info",
            "description": "Send candidate a follow-up questionnaire.",
            "href": share_link,
            "external": True,
        },
        {
            "label": "Share report",
            "description": "Copy the report link for your ATS or manager.",
            "href": share_link,
            "external": True,
        },
    ]


def build_candidate_feedback(session):
    if not session.candidate_feedback_score and not session.candidate_feedback_comment:
        return {}
    labels = {5: "Excellent", 4: "Good", 3: "Neutral", 2: "Challenging", 1: "Poor"}
    return {
        "score": session.candidate_feedback_score,
        "label": labels.get(session.candidate_feedback_score),
        "comment": session.candidate_feedback_comment,
        "submitted_at": session.candidate_feedback_submitted_at,
        "contact_email": session.candidate_feedback_email,
        "contact_phone": session.candidate_feedback_phone,
        "allow_follow_up": session.candidate_feedback_opt_in,
    }


def build_integrity_signals(session):
    telemetry = session.telemetry_log or {}
    if not telemetry:
        return {}
    device = telemetry.get("device_info") or {}
    hints = telemetry.get("device_hints") or {}
    events = telemetry.get("events") or []
    return {
        "ip_address": device.get("ip"),
        "ip_switches": max(0, len(telemetry.get("ip_history") or []) - 1),
        "user_agent": device.get("user_agent") or hints.get("userAgent"),
        "paste_count": telemetry.get("paste_count", 0),
        "last_event": events[-1] if events else None,
        "timezone": hints.get("timezone"),
    }


def build_audit_log(session, client_account):
    events = []
    events.append(
        {
            "label": "Assessment created",
            "timestamp": session.created_at,
            "description": f"Invite issued for {session.candidate_id}",
        }
    )
    if session.started_at:
        events.append(
            {
                "label": "Candidate started",
                "timestamp": session.started_at,
                "description": "Candidate opened the assessment link.",
            }
        )
    if session.submitted_at:
        events.append(
            {
                "label": "Candidate submitted",
                "timestamp": session.submitted_at,
                "description": "Responses were finalized.",
            }
        )
    if session.candidate_feedback_submitted_at:
        events.append(
            {
                "label": "Feedback captured",
                "timestamp": session.candidate_feedback_submitted_at,
                "description": f"Rated {session.candidate_feedback_score}/5",
            }
        )
    note_events = ClientSessionNote.objects.filter(
        client=client_account, session_uuid=session.uuid
    ).order_by("-created_at")[:10]
    for note in note_events:
        events.append(
            {
                "label": "Reviewer note",
                "timestamp": note.created_at,
                "description": note.note[:120] + ("..." if note.note and len(note.note) > 120 else ""),
            }
        )
    return sorted(events, key=lambda entry: entry["timestamp"] or timezone.now(), reverse=True)



class ClientAssessmentExportView(ClientAssessmentMixin, View):
    requires_manager_access = False

    def get(self, request, *args, **kwargs):
        try:
            session = self.get_session_object(kwargs.get("session_uuid"))
        except Http404:
            messages.error(request, "Assessment not available.")
            return redirect("clients:assessment-manage", assessment_type=kwargs.get("assessment_type"))
        if session.status != "submitted":
            messages.error(request, "Report not finalized yet.")
            return redirect("clients:assessment-manage", assessment_type=kwargs.get("assessment_type"))
        response = ClientAssessmentDetailView.as_view()(request, *args, **kwargs)
        return response


class GettingStartedView(LoginRequiredMixin, TemplateView):
    """Getting Started checklist with 8 actionable onboarding tasks."""
    template_name = "clients/getting_started.html"
    login_url = reverse_lazy("clients:login")

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "client_account"):
            return redirect("clients:login")
        client = request.user.client_account
        if not client.company_name:
            return redirect("clients:complete_profile")
        if client.status != "approved":
            messages.info(request, "Your account is still pending approval.")
            return redirect("clients:pending_approval")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.request.user.client_account
        step_data = account.onboarding_step_data or {}

        # Count sessions for invite/review detection
        dataset_map = build_dataset_map(account)
        total_sessions = sum(qs.count() for qs in dataset_map.values())
        completed_sessions = sum(
            qs.filter(status="submitted").count() for qs in dataset_map.values()
        )

        # Build link to first assessment manage page
        first_assessment = next(iter(account.approved_assessments), None)
        assessment_url = (
            reverse("clients:assessment-manage", args=[first_assessment])
            if first_assessment
            else reverse("clients:assessments")
        )

        steps = [
            {
                "key": "complete_profile",
                "number": 1,
                "title": "Complete your profile",
                "description": "Ensure your company name and contact details are set up.",
                "icon": "user",
                "action_label": "Go to Settings",
                "action_url": reverse("clients:settings"),
                "completed": bool(account.company_name),
                "auto": True,
            },
            {
                "key": "upload_logo",
                "number": 2,
                "title": "Upload company logo",
                "description": "Add your brand identity to candidate-facing assessment pages.",
                "icon": "image",
                "action_label": "Upload Logo",
                "action_url": reverse("clients:settings") + "#branding",
                "completed": account.has_logo,
                "auto": True,
            },
            {
                "key": "create_project",
                "number": 3,
                "title": "Create your first project",
                "description": "Organize your hiring pipeline by role or campaign.",
                "icon": "folder",
                "action_label": "Create Project",
                "action_url": reverse("clients:project-list"),
                "completed": account.projects.exists(),
                "auto": True,
            },
            {
                "key": "browse_assessments",
                "number": 4,
                "title": "Browse assessment banks",
                "description": "Explore your approved assessment types and question banks.",
                "icon": "file-text",
                "action_label": "Browse Assessments",
                "action_url": reverse("clients:assessments"),
                "completed": step_data.get("browse_assessments", False),
                "auto": False,
            },
            {
                "key": "invite_candidate",
                "number": 5,
                "title": "Invite your first candidate",
                "description": "Send an assessment invitation to a candidate via email.",
                "icon": "send",
                "action_label": "Send Invite",
                "action_url": assessment_url,
                "completed": total_sessions > 0,
                "auto": True,
            },
            {
                "key": "review_assessment",
                "number": 6,
                "title": "Review a completed assessment",
                "description": "Check a candidate's auto-scored results and recommendations.",
                "icon": "bar-chart",
                "action_label": "View Results",
                "action_url": assessment_url,
                "completed": completed_sessions > 0,
                "auto": True,
            },
            {
                "key": "setup_notifications",
                "number": 7,
                "title": "Set up notifications",
                "description": "Configure email alerts for assessment completions and activity.",
                "icon": "bell",
                "action_label": "Notification Settings",
                "action_url": reverse("clients:settings") + "#notifications",
                "completed": step_data.get("setup_notifications", False),
                "auto": False,
            },
            {
                "key": "explore_analytics",
                "number": 8,
                "title": "Explore analytics",
                "description": "View hiring insights, score distributions, and performance reports.",
                "icon": "trending-up",
                "action_label": "View Analytics",
                "action_url": reverse("clients:analytics"),
                "completed": step_data.get("explore_analytics", False),
                "auto": False,
            },
        ]

        completed_count = sum(1 for s in steps if s["completed"])
        total_count = len(steps)
        progress_percent = round((completed_count / total_count) * 100)
        all_complete = completed_count == total_count

        if all_complete and not account.has_completed_onboarding:
            account.mark_onboarding_complete()

        context.update({
            "account": account,
            "steps": steps,
            "completed_count": completed_count,
            "total_count": total_count,
            "progress_percent": progress_percent,
            "all_complete": all_complete,
        })
        return context


class OnboardingCompleteView(LoginRequiredMixin, View):
    """AJAX endpoint to mark onboarding steps complete."""
    login_url = reverse_lazy("clients:login")

    def post(self, request, *args, **kwargs):
        account = request.user.client_account
        action = request.POST.get('action')  # 'complete_step' or 'complete_tour'

        if action == 'complete_tour':
            account.mark_onboarding_complete()
            return JsonResponse({'success': True, 'message': 'Onboarding completed!'})

        elif action == 'complete_step':
            VALID_STEPS = {
                'step_1', 'step_2', 'step_3', 'step_4', 'step_5',
                'browse_assessments', 'setup_notifications', 'explore_analytics',
            }
            step_id = request.POST.get('step_id', '')
            if step_id and step_id in VALID_STEPS:
                account.onboarding_step_data[step_id] = True
                account.save(update_fields=['onboarding_step_data'])
                return JsonResponse({'success': True, 'step': step_id})

        return JsonResponse({'success': False}, status=400)


class OnboardingResetView(LoginRequiredMixin, View):
    """Allow user to restart onboarding."""
    login_url = reverse_lazy("clients:login")

    def post(self, request, *args, **kwargs):
        account = request.user.client_account
        account.reset_onboarding()
        messages.success(request, "Onboarding tour has been reset. It will start on your next dashboard visit.")
        return redirect('clients:dashboard')


class ClientBillingView(LoginRequiredMixin, TemplateView):
    """Display billing and plan management for client accounts."""
    login_url = reverse_lazy("clients:login")
    template_name = "clients/billing.html"

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "client_account"):
            return redirect("clients:login")
        client = request.user.client_account
        if not client.company_name:
            return redirect("clients:complete_profile")
        if client.status != "approved":
            messages.info(request, "Your account is pending approval.")
            return redirect("clients:pending_approval")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.request.user.client_account
        role = account.role

        # Role labels
        context['is_manager'] = role == "manager"
        context['role_label'] = dict(ClientAccount.ROLE_CHOICES).get(role, role.title())

        # Get current plan details
        plan_details = account.plan_details()

        # Calculate usage
        invite_limit = account.invite_limit()
        invites_used = account.invites_used()
        invite_percent = None
        if invite_limit and invite_limit > 0:
            invite_percent = min(100, round((invites_used / invite_limit) * 100))

        project_limit = account.project_limit()
        project_used = account.active_project_count()
        project_percent = None
        if project_limit and project_limit > 0:
            project_percent = min(100, round((project_used / project_limit) * 100))

        # Current plan info
        context['current_plan'] = {
            'name': plan_details.get('label', account.plan_slug.title()),
            'slug': account.plan_slug,
            'description': plan_details.get('description', ''),
            'price': plan_details.get('price', 'Free'),
            'billing_cycle': plan_details.get('billing_cycle', 'Forever'),
        }

        # Usage stats
        context['usage'] = {
            'invites': {
                'used': invites_used,
                'limit': invite_limit if invite_limit else 'Unlimited',
                'remaining': account.invites_remaining() if invite_limit else None,
                'percent': invite_percent,
            },
            'projects': {
                'used': project_used,
                'limit': project_limit if project_limit else 'Unlimited',
                'remaining': account.remaining_projects() if project_limit else None,
                'percent': project_percent,
            }
        }

        # Build available plans from the pricing tiers (matching homepage structure)
        available_plans = [
            {
                'slug': 'starter',
                'name': 'Starter',
                'price': '$0',
                'billing_cycle': 'Forever',
                'description': 'Try Evalon with two active roles and a small pool of candidates.',
                'invite_quota': 20,
                'project_quota': 2,
                'features': [
                    'Marketing, PM, and behavioral banks',
                    'Basic reports & CSV export',
                    'Email support',
                ],
            },
            {
                'slug': 'pro',
                'name': 'Pro',
                'price': '$59',
                'billing_cycle': 'per month',
                'description': 'Run multiple searches with richer reporting and simple branding.',
                'invite_quota': 250,
                'project_quota': 10,
                'features': [
                    'Pipeline kanban & top-candidate spotlights',
                    'Custom branding + shareable reports',
                    'Priority chat + email support',
                ],
            },
            {
                'slug': 'enterprise',
                'name': 'Enterprise',
                'price': 'Custom',
                'billing_cycle': 'contact us',
                'description': 'Unlimited projects and invites, tailor-made assessments, SSO, and hands-on rollout.',
                'invite_quota': None,
                'project_quota': None,
                'features': [
                    'Agentic AI hiring pipelines',
                    'Dedicated CSM + success playbooks',
                    'Custom assessments & security reviews',
                    'SLA, SSO/SAML, and SOC 2 readiness',
                ],
            },
        ]

        # Add upgrade/downgrade indicators
        plan_order = {'starter': 1, 'pro': 2, 'enterprise': 3}
        current_order = plan_order.get(account.plan_slug, 0)

        for plan in available_plans:
            plan_order_num = plan_order.get(plan['slug'], 0)

            if plan['slug'] == account.plan_slug:
                plan['action'] = 'current'
                plan['is_current'] = True
            elif plan_order_num > current_order:
                plan['action'] = 'upgrade'
                plan['is_current'] = False
            else:
                plan['action'] = 'downgrade'
                plan['is_current'] = False

        context['available_plans'] = available_plans
        context['contact_email'] = 'support@evalon.app'

        return context


class CompleteProfileView(LoginRequiredMixin, FormView):
    """View for completing profile after social authentication signup."""

    template_name = "clients/complete_profile.html"
    form_class = SocialProfileCompleteForm
    login_url = reverse_lazy("clients:login")
    success_url = reverse_lazy("clients:pending_approval")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("clients:login")
        try:
            client = request.user.client_account
            # If profile is already complete, redirect appropriately
            if client.company_name:
                if client.status == "approved":
                    return redirect("clients:dashboard")
                return redirect("clients:pending_approval")
        except ClientAccount.DoesNotExist:
            # If no client account exists yet, something went wrong
            messages.error(request, "No account found. Please try signing up again.")
            return redirect("clients:signup")
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form_class = form_class or self.get_form_class()
        return form_class(instance=self.request.user.client_account, **self.get_form_kwargs())

    def form_valid(self, form):
        account = form.save()
        # Send admin notification for approval
        admin_notified = send_approval_notification(account)
        if admin_notified:
            logger.info(f"Admin notification sent for social signup: {account.email}")
        messages.success(
            self.request,
            "Profile completed! Your account is now pending admin approval.",
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assessment_details"] = ClientAccount.ASSESSMENT_DETAILS
        try:
            context["client"] = self.request.user.client_account
        except ClientAccount.DoesNotExist:
            pass
        return context


class PendingApprovalView(LoginRequiredMixin, TemplateView):
    """View shown to users waiting for admin approval."""

    template_name = "clients/pending_approval.html"
    login_url = reverse_lazy("clients:login")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("clients:login")
        try:
            client = request.user.client_account
            # If profile incomplete, redirect to complete profile first
            if not client.company_name:
                return redirect("clients:complete_profile")
            # If already approved, redirect to dashboard
            if client.status == "approved":
                return redirect("clients:dashboard")
        except ClientAccount.DoesNotExist:
            return redirect("clients:signup")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context["client"] = self.request.user.client_account
        except ClientAccount.DoesNotExist:
            pass
        return context


class SupportRequestCreateView(LoginRequiredMixin, View):
    """Handle support request submissions via AJAX."""
    login_url = reverse_lazy("clients:login")

    def post(self, request, *args, **kwargs):
        if not hasattr(request.user, "client_account"):
            return JsonResponse({"success": False, "error": "Not authenticated"}, status=401)

        client = request.user.client_account

        # Parse JSON body or form data
        if request.content_type == "application/json":
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        else:
            data = request.POST

        # Validate required fields
        valid_types = {c[0] for c in SupportRequest.TYPE_CHOICES}
        request_type = data.get("request_type", "billing")
        if request_type not in valid_types:
            request_type = "other"
        subject = data.get("subject", "").strip()[:200]
        message = data.get("message", "").strip()

        if not subject:
            return JsonResponse({"success": False, "error": "Subject is required"}, status=400)
        if not message:
            return JsonResponse({"success": False, "error": "Message is required"}, status=400)

        # Create support request
        support_request = SupportRequest.objects.create(
            client=client,
            request_type=request_type,
            subject=subject,
            message=message,
        )

        # Log the request
        logger.info(f"Support request #{support_request.pk} created by {client.company_name}")

        return JsonResponse({
            "success": True,
            "message": "Your support request has been submitted. We'll get back to you soon.",
            "request_id": support_request.pk,
        })


class NotificationsAPIView(LoginRequiredMixin, View):
    """Return last 20 notifications as JSON (unread first, then by date)."""
    login_url = reverse_lazy("clients:login")

    def get(self, request):
        if not hasattr(request.user, "client_account"):
            return JsonResponse({"error": "Unauthorized"}, status=403)
        account = request.user.client_account
        notifications = (
            account.notifications
            .order_by("is_read", "-created_at")[:20]
        )
        data = [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "category": n.category,
                "link_url": n.link_url,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ]
        unread_count = account.notifications.filter(is_read=False).count()
        return JsonResponse({"notifications": data, "unread_count": unread_count})


class NotificationsMarkReadView(LoginRequiredMixin, View):
    """Mark one or all notifications as read."""
    login_url = reverse_lazy("clients:login")

    def post(self, request):
        if not hasattr(request.user, "client_account"):
            return JsonResponse({"error": "Unauthorized"}, status=403)
        account = request.user.client_account

        if request.content_type == "application/json":
            try:
                body = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON"}, status=400)
        else:
            body = request.POST

        note_id = body.get("id")
        if note_id:
            account.notifications.filter(id=note_id, is_read=False).update(is_read=True)
        else:
            account.notifications.filter(is_read=False).update(is_read=True)

        unread_count = account.notifications.filter(is_read=False).count()
        return JsonResponse({"success": True, "unread_count": unread_count})


class CampaignQuickCreateView(ClientProjectAccessMixin, View):
    """AJAX endpoint: create a campaign and return its id + name."""

    def post(self, request, *args, **kwargs):
        if self.account.role != "manager":
            return JsonResponse({"error": "Permission denied."}, status=403)
        name = request.POST.get("name", "").strip()
        if not name:
            return JsonResponse({"error": "Project name is required."}, status=400)
        campaign = HiringProject.objects.create(
            client=self.account, name=name, status="active",
        )
        return JsonResponse({"id": campaign.id, "name": campaign.name})


# ── Campaign (Hiring Project) Views ───────────────────────────────────

class CampaignListView(ClientProjectAccessMixin, TemplateView):
    template_name = "clients/campaigns/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaigns = self.account.campaigns.all()
        for campaign in campaigns:
            campaign.pos_count = campaign.position_count
            campaign.active_count = campaign.active_position_count
        context["campaigns"] = campaigns
        context["form"] = getattr(self, "form", HiringProjectForm(client=self.account))
        context["is_manager"] = self.account.role == "manager"
        return context

    def post(self, request, *args, **kwargs):
        if self.account.role != "manager":
            messages.error(request, "Only managers can create projects.")
            return redirect("clients:campaign-list")
        form = HiringProjectForm(request.POST, client=self.account)
        if form.is_valid():
            campaign = form.save()
            messages.success(request, f'Project "{campaign.name}" created.')
            return redirect("clients:campaign-detail", campaign_uuid=campaign.uuid)
        self.form = form
        return self.render_to_response(self.get_context_data(), status=400)


class CampaignDetailView(ClientProjectAccessMixin, TemplateView):
    template_name = "clients/campaigns/detail.html"

    def get_campaign(self):
        if not hasattr(self, "_campaign"):
            self._campaign = get_object_or_404(
                self.account.campaigns, uuid=self.kwargs.get("campaign_uuid")
            )
        return self._campaign

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign = self.get_campaign()
        positions = campaign.positions.order_by("-created_at")
        for pos in positions:
            pos.app_count = pos.applications.count()
        context["campaign"] = campaign
        context["positions"] = positions
        context["unassigned_positions"] = self.account.projects.filter(campaign__isnull=True).order_by("-created_at")
        context["form"] = HiringProjectForm(instance=campaign, client=self.account)
        context["is_manager"] = self.account.role == "manager"
        total_apps = sum(p.app_count for p in positions)
        context["stats"] = {
            "total_positions": positions.count(),
            "active_positions": positions.filter(status=ClientProject.STATUS_ACTIVE).count(),
            "total_applications": total_apps,
        }
        return context

    def post(self, request, *args, **kwargs):
        campaign = self.get_campaign()
        action = request.POST.get("action")

        if action == "assign_position":
            pos_uuid = request.POST.get("position_uuid")
            if pos_uuid:
                pos = get_object_or_404(self.account.projects, uuid=pos_uuid)
                pos.campaign = campaign
                pos.save(update_fields=["campaign"])
                messages.success(request, f'"{pos.title}" added to this project.')
            return redirect("clients:campaign-detail", campaign_uuid=campaign.uuid)

        if action == "remove_position":
            pos_uuid = request.POST.get("position_uuid")
            if pos_uuid:
                pos = get_object_or_404(campaign.positions.all(), uuid=pos_uuid)
                pos.campaign = None
                pos.save(update_fields=["campaign"])
                messages.success(request, f'"{pos.title}" removed from this project.')
            return redirect("clients:campaign-detail", campaign_uuid=campaign.uuid)

        return redirect("clients:campaign-detail", campaign_uuid=campaign.uuid)


class CampaignEditView(ClientProjectAccessMixin, View):
    def post(self, request, *args, **kwargs):
        campaign = get_object_or_404(
            self.account.campaigns, uuid=self.kwargs.get("campaign_uuid")
        )
        form = HiringProjectForm(request.POST, instance=campaign, client=self.account)
        if form.is_valid():
            form.save()
            messages.success(request, "Project updated.")
        else:
            messages.error(request, "Please fix the errors below.")
        return redirect("clients:campaign-detail", campaign_uuid=campaign.uuid)


# ── Application Management Views ──────────────────────────────────────

class ApplicationListView(ClientProjectAccessMixin, TemplateView):
    template_name = "clients/applications/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        applications = PositionApplication.objects.filter(
            client=self.account,
        ).select_related("project")

        project_uuid = self.request.GET.get("position")
        if project_uuid:
            applications = applications.filter(project__uuid=project_uuid)

        status_filter = self.request.GET.get("status")
        if status_filter and status_filter in dict(PositionApplication.STATUS_CHOICES):
            applications = applications.filter(status=status_filter)

        context["applications"] = applications
        context["projects"] = self.account.projects.order_by("-created_at")
        context["status_choices"] = PositionApplication.STATUS_CHOICES
        context["selected_position"] = project_uuid or ""
        context["selected_status"] = status_filter or ""
        return context


class ApplicationDetailView(ClientProjectAccessMixin, TemplateView):
    template_name = "clients/applications/detail.html"

    def get_application(self):
        if not hasattr(self, "_application"):
            self._application = get_object_or_404(
                PositionApplication,
                client=self.account,
                uuid=self.kwargs.get("application_uuid"),
            )
        return self._application

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = self.get_application()
        context["application"] = application
        context["position"] = application.project
        context["pipeline_candidate"] = application.pipeline_candidate

        from .forms import SendAssessmentFromApplicationForm
        context["send_assessment_form"] = SendAssessmentFromApplicationForm(client=self.account)
        return context

    def post(self, request, *args, **kwargs):
        application = self.get_application()
        new_status = request.POST.get("new_status")
        valid_transitions = {
            "pending": ["reviewed", "rejected"],
            "reviewed": ["assessment_sent", "hired", "rejected"],
            "assessment_sent": ["hired", "rejected"],
        }
        allowed = valid_transitions.get(application.status, [])
        if new_status in allowed:
            application.status = new_status
            application.save(update_fields=["status", "updated_at"])
            messages.success(request, f"Application status updated to {application.get_status_display()}.")
        else:
            messages.error(request, "Invalid status transition.")
        return redirect("clients:application-detail", application_uuid=application.uuid)


class ApplicationResumeDownloadView(ClientProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        application = get_object_or_404(
            PositionApplication,
            client=self.account,
            uuid=kwargs.get("application_uuid"),
        )
        if not application.resume_data:
            raise Http404("No resume attached.")
        response = HttpResponse(
            bytes(application.resume_data),
            content_type=application.resume_mime or "application/octet-stream",
        )
        filename = application.resume_filename or f"{application.full_name}_resume"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ApplicationSendAssessmentView(ClientProjectAccessMixin, View):
    def post(self, request, *args, **kwargs):
        from .forms import SendAssessmentFromApplicationForm

        application = get_object_or_404(
            PositionApplication,
            client=self.account,
            uuid=kwargs.get("application_uuid"),
        )

        if application.status not in ("pending", "reviewed"):
            messages.error(request, "Assessment has already been sent for this application.")
            return redirect("clients:application-detail", application_uuid=application.uuid)

        form = SendAssessmentFromApplicationForm(request.POST, client=self.account)
        if not form.is_valid():
            messages.error(request, "Please select a valid assessment type.")
            return redirect("clients:application-detail", application_uuid=application.uuid)

        assessment_type = form.cleaned_data["assessment_type"]
        config = ClientAssessmentMixin.ASSESSMENT_CONFIG.get(assessment_type)
        if not config:
            messages.error(request, "Invalid assessment type.")
            return redirect("clients:application-detail", application_uuid=application.uuid)

        SessionModel = config["session_model"]
        form_class = config["form_class"]
        generate_question_set = form_class.generate_question_set

        level = "mid"
        question_set = generate_question_set(level=level)
        session, created = SessionModel.objects.get_or_create(
            candidate_id=application.email,
            client=self.account,
            defaults={"status": "draft"},
        )
        session.question_set = question_set
        session.responses = []  # Clear stale responses when regenerating questions
        session.status = "in_progress"
        session.client = self.account
        session.project = application.project
        session.level = level
        session.duration_minutes = 45
        session.started_at = None
        session.submitted_at = None
        session.overall_score = None
        session.save()

        application.status = "assessment_sent"
        application.assessment_session_uuid = session.uuid
        application.assessment_type = assessment_type
        application.save(update_fields=["status", "assessment_session_uuid", "assessment_type", "updated_at"])

        if getattr(settings, "EMAIL_ENABLED", False):
            route = config["candidate_route"]
            start_link = request.build_absolute_uri(reverse(route, args=[session.uuid]))
            candidate_first_name = (
                application.full_name.split()[0]
                if application.full_name.strip()
                else application.email.split("@")[0].title()
            )

            email_context = {
                "company_name": self.account.company_name,
                "invited_by": self.account.company_name,
                "candidate": {"first_name": candidate_first_name},
                "assessment": {"title": config["label"]},
                "start_link": start_link,
                "session_link": start_link,
                "due_at": None,
                "notes": "",
                "brand_primary": self.account.brand_primary_color or "#ff8a00",
                "brand_secondary": self.account.brand_secondary_color or "#0e1428",
                "hide_evalon_branding": self.account.hide_evalon_branding,
                "client_footer_text": self.account.get_footer_text(),
            }

            subject = f"{self.account.company_name} invited you to the {config['label']}"
            html_body = render_to_string("emails/invite_candidate.html", email_context)
            text_body = strip_tags(html_body)

            try:
                msg = EmailMultiAlternatives(
                    subject,
                    text_body,
                    getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    [application.email],
                )
                msg.attach_alternative(html_body, "text/html")
                msg.send()
                messages.success(request, f"Assessment invitation sent to {application.email}.")
            except Exception as exc:
                logger.warning("Failed to email invite for application %s: %s", application.uuid, exc)
                messages.warning(request, "Assessment created but email failed. Share the link manually.")
        else:
            messages.success(request, f"Assessment session created for {application.email}.")

        return redirect("clients:application-detail", application_uuid=application.uuid)
