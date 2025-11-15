from __future__ import annotations

import json

from django import forms

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
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

from assessments.behavioral import STATEMENT_LIBRARY
from assessments.models import (
    Assessment,
    AssessmentSession,
    CandidateProfile,
    CompanyProfile,
    PositionTask,
    Question,
)
from assessments.services import send_invite_email
from blog.models import BlogPost
from marketing_assessments.models import DigitalMarketingAssessmentSession
from marketing_assessments.services import generate_question_set
from .forms import (
    AssessmentForm,
    BlogPostForm,
    MarketingAssessmentInviteForm,
    ChoiceForm,
    CompanyForm,
    ConsoleInviteForm,
    PositionTaskForm,
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
        context["company_count"] = CompanyProfile.objects.count()
        context["active_tasks"] = PositionTask.objects.filter(status="active").count()
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
        context["active_tasks_list"] = (
            PositionTask.objects.filter(status="active")
            .select_related("company", "assessment")
            .annotate(session_total=Count("sessions"))
            .order_by("-session_total", "title")[:5]
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


class CompanyListView(ConsoleSectionMixin, LoginRequiredMixin, ListView):
    model = CompanyProfile
    template_name = "console/companies/list.html"
    context_object_name = "companies"
    section = "companies"

    def get_queryset(self):
        return (
            CompanyProfile.objects.all()
            .annotate(task_total=Count("position_tasks", distinct=True))
            .annotate(session_total=Count("sessions", distinct=True))
            .order_by("name")
        )


class CompanyCreateView(ConsoleSectionMixin, LoginRequiredMixin, CreateView):
    model = CompanyProfile
    form_class = CompanyForm
    template_name = "console/companies/form.html"
    section = "companies"

    def form_valid(self, form):
        messages.success(self.request, "Company profile created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("console:company-detail", args=[self.object.slug])


class CompanyUpdateView(ConsoleSectionMixin, LoginRequiredMixin, UpdateView):
    model = CompanyProfile
    form_class = CompanyForm
    template_name = "console/companies/form.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    section = "companies"

    def form_valid(self, form):
        messages.success(self.request, "Company profile updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("console:company-detail", args=[self.object.slug])


class CompanyDetailView(ConsoleSectionMixin, LoginRequiredMixin, DetailView):
    model = CompanyProfile
    template_name = "console/companies/detail.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    context_object_name = "company"
    section = "companies"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = (
            self.object.position_tasks.select_related("assessment")
            .annotate(session_total=Count("sessions"))
            .order_by("-status", "title")
        )
        context["tasks"] = tasks
        context["recent_sessions"] = (
            self.object.sessions.select_related("candidate", "assessment")
            .order_by("-updated_at")[:5]
        )
        context["allowed_types"] = self.object.assessment_type_labels()
        return context


class BlogPostListView(ConsoleSectionMixin, LoginRequiredMixin, ListView):
    model = BlogPost
    template_name = "console/blog/list.html"
    context_object_name = "posts"
    paginate_by = 20
    section = "blog"

    def get_queryset(self):
        return BlogPost.objects.order_by("-published_at", "-created_at")


class BlogPostCreateView(ConsoleSectionMixin, LoginRequiredMixin, CreateView):
    model = BlogPost
    template_name = "console/blog/form.html"
    form_class = BlogPostForm
    section = "blog"

    def form_valid(self, form):
        messages.success(self.request, "Article drafted.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("console:blog-list")


class BlogPostUpdateView(ConsoleSectionMixin, LoginRequiredMixin, UpdateView):
    model = BlogPost
    template_name = "console/blog/form.html"
    form_class = BlogPostForm
    slug_field = "slug"
    slug_url_kwarg = "slug"
    section = "blog"

    def form_valid(self, form):
        messages.success(self.request, "Article updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("console:blog-list")


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
        messages.success(
            self.request,
            "Assessment ready. Share the candidate link below.",
        )
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


class PositionTaskCreateView(ConsoleSectionMixin, LoginRequiredMixin, CreateView):
    model = PositionTask
    form_class = PositionTaskForm
    template_name = "console/tasks/form.html"
    section = "companies"

    def dispatch(self, request, *args, **kwargs):
        self.company = get_object_or_404(CompanyProfile, slug=kwargs["company_slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["company"] = self.company
        initial["assessment_type"] = (
            (self.company.allowed_assessment_types or ["behavioral"])[0]
        )
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["company"].initial = self.company
        form.fields["company"].widget = forms.HiddenInput()
        return form

    def form_valid(self, form):
        messages.success(self.request, "Position task created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("console:company-detail", args=[self.company.slug])


class PositionTaskDetailView(ConsoleSectionMixin, LoginRequiredMixin, DetailView):
    model = PositionTask
    template_name = "console/tasks/detail.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    section = "companies"

    def get_queryset(self):
        return PositionTask.objects.select_related("company", "assessment")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sessions"] = (
            self.object.sessions.select_related("candidate", "assessment")
            .order_by("-created_at")
        )
        return context


class PositionTaskUpdateView(ConsoleSectionMixin, LoginRequiredMixin, UpdateView):
    model = PositionTask
    form_class = PositionTaskForm
    template_name = "console/tasks/form.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    section = "companies"

    def get_queryset(self):
        return PositionTask.objects.select_related("company")

    def form_valid(self, form):
        messages.success(self.request, "Position task updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "console:position-task-detail",
            args=[self.object.slug],
        )


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
        latest_qs = AssessmentSession.objects.filter(candidate=OuterRef("pk")).order_by(
            "-created_at"
        )
        queryset = (
            CandidateProfile.objects.all()
            .annotate(session_total=Count("sessions", distinct=True))
            .annotate(latest_status=Subquery(latest_qs.values("status")[:1]))
            .annotate(latest_decision=Subquery(latest_qs.values("decision")[:1]))
            .annotate(latest_score=Subquery(latest_qs.values("overall_score")[:1]))
            .annotate(
                latest_company=Subquery(latest_qs.values("company__name")[:1]),
                latest_task=Subquery(latest_qs.values("position_task__title")[:1]),
            )
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
            self.object.sessions.select_related(
                "assessment", "position_task", "company"
            ).order_by("-created_at")
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
        intro_link = self.request.build_absolute_uri(
            reverse("candidate:session-entry", args=[result.session.uuid])
        )
        start_link = self.request.build_absolute_uri(
            reverse("candidate:session-start", args=[result.session.uuid])
        )
        email_result = send_invite_email(
            candidate=result.candidate,
            assessment=result.assessment,
            session=result.session,
            intro_link=intro_link,
            start_link=start_link,
            invited_by=invited_by,
            due_at=form.cleaned_data.get("due_at"),
            notes=form.cleaned_data.get("notes", ""),
        )
        messages.success(
            self.request,
            f"Invite ready for {result.candidate.first_name}. Share link: {intro_link}",
        )
        if email_result and email_result.sent:
            messages.info(
                self.request,
                f"Invitation email sent to {result.candidate.email}.",
            )
        else:
            reason = email_result.reason if email_result else "Email backend unavailable."
            messages.warning(
                self.request,
                f"Email could not be sent (reason: {reason}). Share the invite link manually.",
            )
        self.success_url = reverse(
            "console:candidate-detail", args=[result.candidate.pk]
        )
        return super().form_valid(form)


class ConsoleLoginView(SuccessMessageMixin, FormView):
    template_name = "console/login.html"
    success_url = reverse_lazy("console:dashboard")
    form_class = AuthenticationForm
    success_message = "Welcome back!"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("console:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        return super().form_valid(form)
class SessionDetailView(ConsoleSectionMixin, LoginRequiredMixin, FormView):
    template_name = "console/candidates/session_detail.html"
    form_class = SessionUpdateForm
    section = "candidates"

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            AssessmentSession.objects.select_related(
                "candidate",
                "assessment",
                "assessment__category",
                "position_task",
                "company",
            ).prefetch_related("responses__question", "responses__selected_choices"),
            pk=kwargs["pk"],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.session
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["session_obj"] = self.session
        context["candidate"] = self.session.candidate
        context["assessment"] = self.session.assessment
        responses = list(
            self.session.responses.select_related("question").all()
        )
        for response in responses:
            if response.question.question_type == Question.TYPE_BEHAVIORAL:
                entries = []
                try:
                    data = json.loads(response.answer_text or "[]")
                except json.JSONDecodeError:
                    data = []
                for entry in data:
                    statement_id = entry.get("statement_id")
                    meta = STATEMENT_LIBRARY.get(statement_id, {})
                    entries.append(
                        {
                            "statement_id": statement_id,
                            "response_type": entry.get("response_type"),
                            "text": meta.get("text", ""),
                            "trait": (meta.get("trait") or "").replace("_", " ").title(),
                        }
                    )
                response.behavioral_entries = entries
        context["responses"] = responses
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Session updated.")
        return redirect("console:session-detail", pk=self.session.pk)

    def post(self, request, *args, **kwargs):
        if request.POST.get("quick_decision"):
            decision = request.POST["quick_decision"]
            self.session.decision = decision
            self.session.save(update_fields=["decision", "updated_at"])
            messages.success(
                request,
                f"{self.session.candidate.first_name} marked as {decision.title()}.",
            )
            return redirect("console:session-detail", pk=self.session.pk)
        return super().post(request, *args, **kwargs)
