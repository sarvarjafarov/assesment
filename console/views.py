from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView, TemplateView

from behavioral_assessments.models import BehavioralAssessmentSession
from marketing_assessments.models import DigitalMarketingAssessmentSession
from pm_assessments.models import ProductAssessmentSession

from .forms import (
    BehavioralAssessmentInviteForm,
    MarketingAssessmentInviteForm,
    ProductAssessmentInviteForm,
)


class ConsoleSectionMixin:
    section = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["section"] = self.section
        return context


class DashboardView(ConsoleSectionMixin, LoginRequiredMixin, TemplateView):
    template_name = "console/dashboard.html"
    section = "dashboard"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary_cards"] = self._build_cards()
        context["recent_sessions"] = self._recent_sessions()
        return context

    def _build_cards(self) -> list[dict]:
        cards = []
        cards.append(self._card_payload(
            label="Marketing",
            queryset=DigitalMarketingAssessmentSession.objects.all(),
            detail_url=reverse("console:marketing-list"),
        ))
        cards.append(self._card_payload(
            label="Product",
            queryset=ProductAssessmentSession.objects.all(),
            detail_url=reverse("console:pm-list"),
        ))
        cards.append(self._card_payload(
            label="Behavioral",
            queryset=BehavioralAssessmentSession.objects.all(),
            detail_url=reverse("console:behavioral-list"),
        ))
        return cards

    def _card_payload(self, *, label: str, queryset, detail_url: str) -> dict:
        total = queryset.count()
        in_progress = queryset.filter(status="in_progress").count()
        completed = queryset.filter(status="submitted").count()
        return {
            "label": label,
            "total": total,
            "in_progress": in_progress,
            "completed": completed,
            "detail_url": detail_url,
        }

    def _recent_sessions(self) -> list[dict]:
        entries: list[dict] = []
        now = timezone.now()
        sources = [
            ("Marketing", DigitalMarketingAssessmentSession.objects.order_by("-updated_at")[:10], "console:marketing-detail"),
            ("Product", ProductAssessmentSession.objects.order_by("-updated_at")[:10], "console:pm-detail"),
            ("Behavioral", BehavioralAssessmentSession.objects.order_by("-updated_at")[:10], "console:behavioral-detail"),
        ]
        for label, queryset, url_name in sources:
            for session in queryset:
                timestamp = session.updated_at or now
                entries.append(
                    {
                        "candidate": session.candidate_id,
                        "status": session.get_status_display(),
                        "label": label,
                        "timestamp": timestamp,
                        "url": reverse(url_name, args=[session.uuid]),
                    }
                )
        entries.sort(key=lambda item: item["timestamp"], reverse=True)
        return entries[:10]


class MarketingAssessmentListView(ConsoleSectionMixin, LoginRequiredMixin, ListView):
    model = DigitalMarketingAssessmentSession
    template_name = "console/marketing/list.html"
    context_object_name = "sessions"
    section = "marketing"
    paginate_by = 25

    def get_queryset(self):
        return DigitalMarketingAssessmentSession.objects.order_by("-created_at")


class MarketingAssessmentCreateView(ConsoleSectionMixin, LoginRequiredMixin, FormView):
    template_name = "console/marketing/form.html"
    form_class = MarketingAssessmentInviteForm
    section = "marketing"

    def form_valid(self, form):
        session = form.save()
        messages.success(self.request, "Marketing assessment ready. Share the candidate link below.")
        self.success_url = reverse("console:marketing-detail", args=[session.uuid])
        return super().form_valid(form)


class MarketingAssessmentDetailView(ConsoleSectionMixin, LoginRequiredMixin, DetailView):
    model = DigitalMarketingAssessmentSession
    template_name = "console/marketing/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    context_object_name = "session_obj"
    section = "marketing"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        share_link = self.request.build_absolute_uri(
            reverse("candidate:marketing-session", args=[self.object.uuid])
        )
        context["share_link"] = share_link
        return context


class ProductAssessmentListView(ConsoleSectionMixin, LoginRequiredMixin, ListView):
    model = ProductAssessmentSession
    template_name = "console/pm/list.html"
    context_object_name = "sessions"
    section = "pm"
    paginate_by = 25

    def get_queryset(self):
        return ProductAssessmentSession.objects.order_by("-created_at")


class ProductAssessmentCreateView(ConsoleSectionMixin, LoginRequiredMixin, FormView):
    template_name = "console/pm/form.html"
    form_class = ProductAssessmentInviteForm
    section = "pm"

    def form_valid(self, form):
        session = form.save()
        messages.success(self.request, "PM assessment ready. Share the candidate link below.")
        self.success_url = reverse("console:pm-detail", args=[session.uuid])
        return super().form_valid(form)


class ProductAssessmentDetailView(ConsoleSectionMixin, LoginRequiredMixin, DetailView):
    model = ProductAssessmentSession
    template_name = "console/pm/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    context_object_name = "session_obj"
    section = "pm"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        share_link = self.request.build_absolute_uri(
            reverse("candidate:pm-session", args=[self.object.uuid])
        )
        context["share_link"] = share_link
        return context


class BehavioralAssessmentListView(ConsoleSectionMixin, LoginRequiredMixin, ListView):
    model = BehavioralAssessmentSession
    template_name = "console/behavioral/list.html"
    context_object_name = "sessions"
    section = "behavioral"
    paginate_by = 25

    def get_queryset(self):
        return BehavioralAssessmentSession.objects.order_by("-created_at")


class BehavioralAssessmentCreateView(ConsoleSectionMixin, LoginRequiredMixin, FormView):
    template_name = "console/behavioral/form.html"
    form_class = BehavioralAssessmentInviteForm
    section = "behavioral"

    def form_valid(self, form):
        session = form.save()
        messages.success(self.request, "Behavioral assessment ready. Share the candidate link below.")
        self.success_url = reverse("console:behavioral-detail", args=[session.uuid])
        return super().form_valid(form)


class BehavioralAssessmentDetailView(ConsoleSectionMixin, LoginRequiredMixin, DetailView):
    model = BehavioralAssessmentSession
    template_name = "console/behavioral/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    context_object_name = "session_obj"
    section = "behavioral"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        share_link = self.request.build_absolute_uri(
            reverse("candidate:behavioral-session", args=[self.object.uuid])
        )
        context["share_link"] = share_link
        trait_scores = self.object.trait_scores or {}
        context["traits"] = [
            {
                "label": trait.replace("_", " ").title(),
                "score": score,
            }
            for trait, score in trait_scores.items()
        ]
        context["eligibility"] = {
            "score": self.object.eligibility_score,
            "label": self.object.eligibility_label,
        }
        context["risk_flags"] = self.object.risk_flags or []
        return context


class ConsoleLoginView(FormView):
    template_name = "console/login.html"
    success_url = reverse_lazy("console:dashboard")
    form_class = AuthenticationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("console:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super().form_valid(form)
