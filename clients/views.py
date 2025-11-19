from __future__ import annotations

from django.contrib import messages
import csv
import json
from datetime import timedelta
import csv
import io

from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import FormView, TemplateView
from django.db import models

from marketing_assessments.models import DigitalMarketingAssessmentSession
from pm_assessments.models import ProductAssessmentSession
from behavioral_assessments.models import BehavioralAssessmentSession

from .forms import (
    ClientBehavioralInviteForm,
    ClientBulkInviteForm,
    ClientLoginForm,
    ClientMarketingInviteForm,
    ClientProductInviteForm,
    ClientSignupForm,
    ClientSessionNoteForm,
    ClientLogoForm,
)
from .models import ClientAccount, ClientNotification, ClientSessionNote

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


def build_dataset_map(account: ClientAccount):
    return {
        "marketing": DigitalMarketingAssessmentSession.objects.filter(client=account),
        "product": ProductAssessmentSession.objects.filter(client=account),
        "behavioral": BehavioralAssessmentSession.objects.filter(client=account),
    }


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
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assessment_details"] = ClientAccount.ASSESSMENT_DETAILS
        return context


class ClientSignupCompleteView(TemplateView):
    template_name = "clients/signup_complete.html"


class ClientLoginView(FormView):
    template_name = "clients/login.html"
    form_class = ClientLoginForm
    success_url = reverse_lazy("clients:dashboard")

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        return super().form_valid(form)


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
        self.logo_form = self.logo_form_class()
        if request.user.client_account.status != "approved":
            messages.info(request, "Your account is still pending approval.")
            return redirect("clients:signup")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        account = request.user.client_account
        action = request.POST.get("action")
        if action == "toggle_summary":
            if account.role != "manager":
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
            if account.role != "manager":
                messages.error(request, "Only managers can update branding.")
                return redirect("clients:dashboard")
            form = self.logo_form_class(request.POST, request.FILES)
            if form.is_valid():
                account.logo = form.cleaned_data["logo"]
                account.save(update_fields=["logo"])
                messages.success(request, "Logo updated.")
                return redirect("clients:dashboard")
            self.logo_form = form
            response = self.get(request, *args, **kwargs)
            response.status_code = 400
            return response
        elif action == "remove_logo":
            if account.role != "manager":
                messages.error(request, "Only managers can update branding.")
                return redirect("clients:dashboard")
            if account.logo:
                account.logo.delete(save=False)
                account.logo = None
                account.save(update_fields=["logo"])
            messages.info(request, "Logo removed.")
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
                    }
                )
        if stats["total_candidates"] < max(3, len(account.approved_assessments) * 2):
            stats["attention_items"].append(
                {
                    "label": "Low invite volume",
                    "detail": "Send more invites to keep your pipeline active.",
                }
            )
        context.update(
            {
                "account": account,
                "is_manager": account.role == "manager",
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
            }
        )
        return context

    def _quick_actions(self, account: ClientAccount) -> list[dict]:
        actions = []
        first_assessment = next(iter(account.approved_assessments), None)
        primary_url = reverse("clients:dashboard")
        if first_assessment and account.role == "manager":
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
                "href": "mailto:support@sira.app",
                "external": True,
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
        total_candidates = (
            marketing_sessions.count() + product_sessions.count() + behavioral_sessions.count()
        )

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

        _append_scores(marketing_sessions)
        _append_scores(product_sessions)
        _append_scores(behavioral_sessions, score_field="eligibility_score")

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

        recent = list(marketing_sessions.order_by("-created_at")[:5])
        recent += list(product_sessions.order_by("-created_at")[:5])
        recent += list(behavioral_sessions.order_by("-created_at")[:5])
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
        durations: list[float] = []
        scores: list[float] = []
        total_invites = 0
        total_completed = 0
        datasets = (
            (DigitalMarketingAssessmentSession.objects.all(), "overall_score"),
            (ProductAssessmentSession.objects.all(), "overall_score"),
            (BehavioralAssessmentSession.objects.all(), "eligibility_score"),
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


class ClientActivityExportView(LoginRequiredMixin, View):
    login_url = reverse_lazy("clients:login")

    def get(self, request, *args, **kwargs):
        if not hasattr(request.user, "client_account"):
            return redirect("clients:login")
        account = request.user.client_account
        if account.status != "approved":
            messages.error(request, "Your account is not approved yet.")
            return redirect("clients:dashboard")
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
    requires_manager_access = True

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
    }

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "client_account"):
            return redirect("clients:login")
        self.account = request.user.client_account
        self.is_manager = self.account.role == "manager"
        if self.account.status != "approved":
            messages.info(request, "Your account is pending approval.")
            return redirect("clients:dashboard")
        assessment_type = kwargs.get("assessment_type")
        if assessment_type not in self.ASSESSMENT_CONFIG:
            raise Http404
        if assessment_type not in self.account.approved_assessments:
            messages.error(request, "You do not have access to that assessment.")
            return redirect("clients:dashboard")
        if self.requires_manager_access and not self.is_manager:
            messages.error(request, "Only managers can perform that action.")
            return redirect("clients:dashboard")
        self.assessment_type = assessment_type
        self.assessment_config = self.ASSESSMENT_CONFIG[assessment_type]
        self._activate_scheduled_invites()
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        return self.assessment_config["form_class"]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["client"] = self.account
        return kwargs

    def get_success_url(self):
        return reverse("clients:assessment-manage", args=[self.assessment_type])

    def sessions(self):
        model = self.assessment_config["session_model"]
        return model.objects.filter(client=self.account).order_by("-created_at")

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
        )
        for session in scheduled:
            session.status = "in_progress"
            session.scheduled_for = None
            session.started_at = None
            session.save(update_fields=["status", "scheduled_for", "started_at"])


class ClientAssessmentManageView(ClientAssessmentMixin, FormView):
    template_name = "clients/assessments/manage.html"
    bulk_form_class = ClientBulkInviteForm

    def form_valid(self, form):
        session = form.save()
        messages.success(self.request, f"Invite ready. Share the link with {session.candidate_id}.")
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "bulk_upload":
            if not self.is_manager:
                messages.error(request, "Only managers can upload invites.")
                return redirect(self.get_success_url())
            bulk_form = self.bulk_form_class(request.POST, request.FILES)
            if bulk_form.is_valid():
                created, errors = self._process_bulk_upload(bulk_form.cleaned_data["csv_file"])
                if created:
                    messages.success(request, f"Created {created} invite{'' if created == 1 else 's'}.")
                if errors:
                    messages.warning(request, f"Issues with rows: {', '.join(errors[:5])}")
                return redirect(self.get_success_url())
            context = self.get_context_data(form=self.get_form(), bulk_form=bulk_form)
            return self.render_to_response(context, status=400)
        elif action == "send_reminder":
            self._trigger_reminder(request.POST.get("session_uuid"))
            return redirect(self.get_success_url())
        elif action == "launch_now":
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
        for session in sessions:
            score = getattr(session, "overall_score", None)
            if score is None:
                score = getattr(session, "hard_skill_score", None)
            if score is None:
                score = getattr(session, "eligibility_score", None)
            note_meta = note_lookup.get(session.uuid, {})
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
                }
            )
        bulk_form = context.get("bulk_form")
        if not bulk_form:
            bulk_form = self.bulk_form_class()
        context.update(
            {
                "assessment_label": self.assessment_config["label"],
                "sessions": session_rows,
                "bulk_form": bulk_form,
            }
        )
        return context

    def _process_bulk_upload(self, csv_file) -> tuple[int, list[str]]:
        created = 0
        errors: list[str] = []
        decoded = io.TextIOWrapper(csv_file.file, encoding="utf-8")
        reader = csv.DictReader(decoded)
        default_duration = self.get_form_class().base_fields["duration_minutes"].initial or 30
        for idx, row in enumerate(reader, start=1):
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
            }
            form = self.get_form_class()(data=form_data, client=self.account)
            if form.is_valid():
                form.save()
                created += 1
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
        messages.success(self.request, f"Invite for {session.candidate_id} is now live.")


class ClientAssessmentDetailView(ClientAssessmentMixin, FormView):
    template_name = "clients/assessments/detail.html"
    form_class = ClientSessionNoteForm
    requires_manager_access = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_uuid = kwargs.get("session_uuid")
        session = self.get_session_object(session_uuid)
        report = self._build_report(session)
        context.update(
            {
                "assessment_label": self.assessment_config["label"],
                "session_obj": session,
                "share_link": self.build_share_link(session),
                "report": report,
                "assessment_type": self.assessment_type,
                "note_form": context.get("form") or self.get_form(),
                "notes": ClientSessionNote.objects.filter(
                    client=self.account,
                    assessment_type=self.assessment_type,
                    session_uuid=session.uuid,
                ),
                "can_edit_notes": self.is_manager,
            }
        )
        return context

    def _build_report(self, session):
        if self.assessment_type == "behavioral":
            return {
                "score": session.eligibility_score,
                "label": session.eligibility_label,
                "traits": session.trait_scores or {},
                "flags": session.risk_flags or [],
            }
        recommendations = session.recommendations or {}
        return {
            "overall": session.overall_score,
            "hard": getattr(session, "hard_skill_score", None),
            "soft": getattr(session, "soft_skill_score", None),
            "categories": session.category_breakdown or {},
            "fit_scores": recommendations.get("fit_scores", {}),
            "strengths": recommendations.get("strengths", []),
            "development": recommendations.get("development", []),
            "seniority": recommendations.get("seniority"),
        }

    def form_valid(self, form):
        session_uuid = self.kwargs.get("session_uuid")
        session = self.get_session_object(session_uuid)
        if not self.is_manager:
            messages.error(self.request, "Only managers can add notes.")
            return redirect(self.get_success_url())
        note = form.save(commit=False)
        note.client = self.account
        note.assessment_type = self.assessment_type
        note.session_uuid = session.uuid
        note.candidate_id = session.candidate_id
        note.author = self.request.user
        note.save()
        messages.success(self.request, "Note saved.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("clients:assessment-detail", args=[self.assessment_type, self.kwargs.get("session_uuid")])
