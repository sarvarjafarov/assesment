from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from assessments.models import (
    Assessment,
    AssessmentSession,
    CandidateProfile,
    Question,
)
from assessments.services import send_invite_email
from .forms import (
    AssessmentForm,
    ChoiceForm,
    ConsoleInviteForm,
    QuestionForm,
    SessionUpdateForm,
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
        now = timezone.now()
        sessions = AssessmentSession.objects.select_related("candidate", "assessment")
        context["stats"] = {
            "total_invites": sessions.count(),
            "in_progress": sessions.filter(status__in=["invited", "in_progress"]).count(),
            "completed": sessions.filter(status="completed").count(),
            "overdue": sessions.filter(
                due_at__lt=now, due_at__isnull=False
            ).exclude(status="completed").count(),
        }
        context["assessment_count"] = Assessment.objects.count()
        context["candidate_count"] = CandidateProfile.objects.count()
        context["upcoming_due"] = (
            sessions.filter(
                due_at__isnull=False, status__in=["invited", "in_progress"]
            )
            .order_by("due_at")[:5]
        )
        context["recent_activity"] = sessions.order_by("-updated_at")[:5]
        context["top_assessments"] = (
            Assessment.objects.annotate(num_sessions=Count("sessions"))
            .order_by("-num_sessions")[:5]
        )
        return context


class AssessmentListView(ConsoleSectionMixin, LoginRequiredMixin, ListView):
    model = Assessment
    template_name = "console/assessments/list.html"
    context_object_name = "assessments"
    section = "assessments"


class AssessmentCreateView(ConsoleSectionMixin, LoginRequiredMixin, CreateView):
    model = Assessment
    form_class = AssessmentForm
    template_name = "console/assessments/form.html"
    section = "assessments"

    def form_valid(self, form):
        messages.success(self.request, "Assessment created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("console:assessment-detail", args=[self.object.slug])


class AssessmentUpdateView(ConsoleSectionMixin, LoginRequiredMixin, UpdateView):
    model = Assessment
    form_class = AssessmentForm
    template_name = "console/assessments/form.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    section = "assessments"

    def form_valid(self, form):
        messages.success(self.request, "Assessment updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("console:assessment-detail", args=[self.object.slug])


class AssessmentDetailView(ConsoleSectionMixin, LoginRequiredMixin, DetailView):
    model = Assessment
    template_name = "console/assessments/detail.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    context_object_name = "assessment"
    section = "assessments"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["questions"] = (
            self.object.questions.prefetch_related("choices").order_by("order")
        )
        return context


class QuestionCreateView(ConsoleSectionMixin, LoginRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = "console/assessments/question_form.html"
    section = "assessments"

    def dispatch(self, request, *args, **kwargs):
        self.assessment = get_object_or_404(Assessment, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.assessment = self.assessment
        messages.success(self.request, "Question added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("console:assessment-detail", args=[self.assessment.slug])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assessment"] = self.assessment
        return context


class ChoiceCreateView(ConsoleSectionMixin, LoginRequiredMixin, FormView):
    form_class = ChoiceForm
    template_name = "console/assessments/choice_form.html"
    section = "assessments"

    def dispatch(self, request, *args, **kwargs):
        self.question = get_object_or_404(
            Question.objects.select_related("assessment"), pk=kwargs["pk"]
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        choice = form.save(commit=False)
        choice.question = self.question
        choice.save()
        messages.success(self.request, "Choice added.")
        return redirect(
            reverse("console:assessment-detail", args=[self.question.assessment.slug])
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["question"] = self.question
        return context



class CandidateListView(ConsoleSectionMixin, LoginRequiredMixin, ListView):
    model = CandidateProfile
    template_name = "console/candidates/list.html"
    context_object_name = "candidates"
    paginate_by = 25
    section = "candidates"

    def get_queryset(self):
        latest_status = AssessmentSession.objects.filter(candidate=OuterRef("pk")).order_by(
            "-created_at"
        )
        queryset = (
            CandidateProfile.objects.all()
            .annotate(session_total=Count("sessions", distinct=True))
            .annotate(latest_status=Subquery(latest_status.values("status")[:1]))
            .order_by("first_name", "last_name")
        )
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status_counts = (
            AssessmentSession.objects.values("status")
            .annotate(total=Count("id"))
            .order_by()
        )
        context["status_counts"] = {entry["status"]: entry["total"] for entry in status_counts}
        context["query"] = self.request.GET.get("q", "")
        return context


class CandidateDetailView(ConsoleSectionMixin, LoginRequiredMixin, DetailView):
    model = CandidateProfile
    template_name = "console/candidates/detail.html"
    context_object_name = "candidate"
    section = "candidates"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sessions = list(
            self.object.sessions.select_related("assessment").order_by("-created_at")
        )
        forms = []
        for session in sessions:
            forms.append(
                (
                    session,
                    SessionUpdateForm(prefix=f"session-{session.pk}", instance=session),
                )
            )
        context["session_forms"] = forms
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        session_id = request.POST.get("session_id")
        session = get_object_or_404(
            AssessmentSession, pk=session_id, candidate=self.object
        )
        form = SessionUpdateForm(
            request.POST, instance=session, prefix=f"session-{session.pk}"
        )
        if form.is_valid():
            form.save()
            messages.success(
                request, f"Session for {session.assessment.title} updated."
            )
            return redirect("console:candidate-detail", pk=self.object.pk)
        context = self.get_context_data(object=self.object)
        existing_forms = context["session_forms"]
        context["session_forms"] = [
            (
                s,
                form
                if s.pk == session.pk
                else SessionUpdateForm(prefix=f"session-{s.pk}", instance=s),
            )
            for s, _ in existing_forms
        ]
        return self.render_to_response(context)


class InviteCreateView(ConsoleSectionMixin, LoginRequiredMixin, FormView):
    template_name = "console/invites/new.html"
    form_class = ConsoleInviteForm
    success_url = reverse_lazy("console:candidate-list")
    section = "invites"

    def form_valid(self, form):
        invited_by = (
            self.request.user.get_full_name()
            or self.request.user.email
            or self.request.user.username
            or "Console"
        )
        result = form.save(invited_by=invited_by)
        session_link = self.request.build_absolute_uri(
            reverse("candidate:session-entry", args=[result.session.uuid])
        )
        send_invite_email(
            candidate=result.candidate,
            assessment=result.assessment,
            session=result.session,
            session_link=session_link,
            invited_by=invited_by,
            due_at=form.cleaned_data.get("due_at"),
            notes=form.cleaned_data.get("notes", ""),
        )
        messages.success(
            self.request,
            f"Invite ready for {result.candidate.first_name}. Share link: {session_link}",
        )
        messages.info(
            self.request,
            f"Invitation email sent to {result.candidate.email}.",
        )
        self.success_url = reverse(
            "console:candidate-detail", args=[result.candidate.pk]
        )
        return super().form_valid(form)
