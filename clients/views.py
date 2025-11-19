from __future__ import annotations

from django.contrib import messages
import json

from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, TemplateView
from django.db import models

from marketing_assessments.models import DigitalMarketingAssessmentSession
from pm_assessments.models import ProductAssessmentSession
from behavioral_assessments.models import BehavioralAssessmentSession

from .forms import (
    ClientBehavioralInviteForm,
    ClientLoginForm,
    ClientMarketingInviteForm,
    ClientProductInviteForm,
    ClientSignupForm,
)
from .models import ClientAccount


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

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "client_account"):
            return redirect("clients:login")
        if request.user.client_account.status != "approved":
            messages.info(request, "Your account is still pending approval.")
            return redirect("clients:signup")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.request.user.client_account
        catalog = ClientAccount.ASSESSMENT_DETAILS
        stats = self._calculate_stats(account)
        assessment_stats_map = {item["code"]: item for item in stats.get("assessment_breakdown", [])}
        context.update(
            {
                "account": account,
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
            }
        )
        return context

    def _quick_actions(self, account: ClientAccount) -> list[dict]:
        actions = []
        first_assessment = next(iter(account.approved_assessments), None)
        primary_url = (
            reverse("clients:assessment-manage", args=[first_assessment])
            if first_assessment
            else reverse("clients:dashboard")
        )
        if first_assessment:
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
                "href": primary_url,
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

    def _calculate_stats(self, account: ClientAccount) -> dict:
        marketing_sessions = DigitalMarketingAssessmentSession.objects.filter(client=account)
        product_sessions = ProductAssessmentSession.objects.filter(client=account)
        behavioral_sessions = BehavioralAssessmentSession.objects.filter(client=account)
        total_candidates = (
            marketing_sessions.count() + product_sessions.count() + behavioral_sessions.count()
        )

        breakdown = []
        scores: list[float] = []
        durations: list[float] = []
        status_totals = {"draft": 0, "in_progress": 0, "submitted": 0}
        attention_items: list[dict] = []
        recent_activity: list[dict] = []

        def _append_scores(queryset, score_field="overall_score"):
            for score, duration in queryset.filter(status="submitted").values_list(score_field, "duration_minutes"):
                if score is not None:
                    scores.append(float(score))
                if duration is not None:
                    durations.append(float(duration))

        _append_scores(marketing_sessions)
        _append_scores(product_sessions)
        _append_scores(behavioral_sessions, score_field="eligibility_score")

        dataset_map = {
            "marketing": marketing_sessions,
            "product": product_sessions,
            "behavioral": behavioral_sessions,
        }

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

        def _recent_payload(qs, code):
            label = ClientAccount.ASSESSMENT_DETAILS.get(code, {}).get("label", code.title())
            entries = []
            for session in qs.order_by("-updated_at")[:5]:
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
            return entries

        for code, queryset in dataset_map.items():
            recent_activity.extend(_recent_payload(queryset, code))

        recent_activity.sort(key=lambda item: item["timestamp"] or timezone.now(), reverse=True)
        recent_activity = recent_activity[:6]

        avg_score = sum(scores) / len(scores) if scores else None
        avg_duration = sum(durations) / len(durations) if durations else None

        recent = list(marketing_sessions.order_by("-created_at")[:5])
        recent += list(product_sessions.order_by("-created_at")[:5])
        recent += list(behavioral_sessions.order_by("-created_at")[:5])
        recent.sort(key=lambda session: session.created_at or session.updated_at)
        recent = recent[-5:]

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
            "recent_activity": recent_activity,
            "attention_items": attention_items,
            "funnel": funnel,
        }


class ClientAssessmentMixin(LoginRequiredMixin):
    login_url = reverse_lazy("clients:login")
    assessment_type: str

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
        if self.account.status != "approved":
            messages.info(request, "Your account is pending approval.")
            return redirect("clients:dashboard")
        assessment_type = kwargs.get("assessment_type")
        if assessment_type not in self.ASSESSMENT_CONFIG:
            raise Http404
        if assessment_type not in self.account.approved_assessments:
            messages.error(request, "You do not have access to that assessment.")
            return redirect("clients:dashboard")
        self.assessment_type = assessment_type
        self.assessment_config = self.ASSESSMENT_CONFIG[assessment_type]
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


class ClientAssessmentManageView(ClientAssessmentMixin, FormView):
    template_name = "clients/assessments/manage.html"

    def form_valid(self, form):
        session = form.save()
        messages.success(self.request, f"Invite ready. Share the link with {session.candidate_id}.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_rows = []
        for session in self.sessions():
            score = getattr(session, "overall_score", None)
            if score is None:
                score = getattr(session, "hard_skill_score", None)
            if score is None:
                score = getattr(session, "eligibility_score", None)
            session_rows.append(
                {
                    "candidate": session.candidate_id,
                    "status": session.get_status_display(),
                    "score": score,
                    "submitted_at": session.submitted_at,
                    "share_link": self.build_share_link(session),
                    "detail_url": reverse(
                        "clients:assessment-detail", args=[self.assessment_type, session.uuid]
                    )
                    if session.status == "submitted"
                    else None,
                }
            )
        context.update(
            {
                "assessment_label": self.assessment_config["label"],
                "sessions": session_rows,
            }
        )
        return context


class ClientAssessmentDetailView(ClientAssessmentMixin, TemplateView):
    template_name = "clients/assessments/detail.html"

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
