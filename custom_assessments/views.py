"""
Views for Custom Assessments client portal.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .decorators import check_custom_assessment_limit, premium_required
from .forms import (
    AIGenerationForm,
    CSVUploadForm,
    CustomAssessmentForm,
    CustomQuestionForm,
    InviteCandidateForm,
)
from .models import CustomAssessment, CustomAssessmentSession, CustomQuestion
from .services import (
    CSVValidationError,
    create_questions_from_data,
    generate_csv_template,
    generate_questions_with_ai,
    initialize_session,
    parse_csv_questions,
    send_custom_assessment_invitation,
)


class PremiumRequiredMixin:
    """Mixin to require premium plan for views."""

    @method_decorator(premium_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class CustomAssessmentListView(LoginRequiredMixin, PremiumRequiredMixin, ListView):
    """List all custom assessments for the current client."""

    model = CustomAssessment
    template_name = "custom_assessments/list.html"
    context_object_name = "assessments"

    def get_queryset(self):
        return CustomAssessment.objects.filter(
            client=self.request.user.client_account
        ).prefetch_related("questions")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.request.user.client_account

        # Check limits for premium users
        if account.plan_slug == "premium":
            context["assessment_limit"] = 10
            context["assessment_count"] = self.get_queryset().exclude(
                status="archived"
            ).count()
        else:
            context["assessment_limit"] = None

        return context


@method_decorator(check_custom_assessment_limit, name="dispatch")
class CustomAssessmentCreateView(LoginRequiredMixin, PremiumRequiredMixin, CreateView):
    """Create a new custom assessment."""

    model = CustomAssessment
    form_class = CustomAssessmentForm
    template_name = "custom_assessments/create.html"

    def form_valid(self, form):
        form.instance.client = self.request.user.client_account
        messages.success(self.request, "Assessment created! Now add questions.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("custom_assessments:questions", kwargs={"uuid": self.object.uuid})


class CustomAssessmentDetailView(LoginRequiredMixin, PremiumRequiredMixin, DetailView):
    """View assessment details and results."""

    model = CustomAssessment
    template_name = "custom_assessments/detail.html"
    context_object_name = "assessment"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        return CustomAssessment.objects.filter(
            client=self.request.user.client_account
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sessions"] = self.object.sessions.select_related("project").order_by("-created_at")
        context["invite_form"] = InviteCandidateForm(
            client_account=self.request.user.client_account
        )
        return context


class CustomAssessmentUpdateView(LoginRequiredMixin, PremiumRequiredMixin, UpdateView):
    """Edit assessment settings."""

    model = CustomAssessment
    form_class = CustomAssessmentForm
    template_name = "custom_assessments/edit.html"
    context_object_name = "assessment"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        return CustomAssessment.objects.filter(
            client=self.request.user.client_account,
            status="draft",  # Can only edit drafts
        )

    def form_valid(self, form):
        messages.success(self.request, "Assessment updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("custom_assessments:detail", kwargs={"uuid": self.object.uuid})


class CustomAssessmentDeleteView(LoginRequiredMixin, PremiumRequiredMixin, DeleteView):
    """Delete a draft assessment."""

    model = CustomAssessment
    template_name = "custom_assessments/delete.html"
    context_object_name = "assessment"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    success_url = reverse_lazy("custom_assessments:list")

    def get_queryset(self):
        return CustomAssessment.objects.filter(
            client=self.request.user.client_account,
            status="draft",  # Can only delete drafts
        )

    def form_valid(self, form):
        messages.success(self.request, "Assessment deleted.")
        return super().form_valid(form)


class QuestionsManageView(LoginRequiredMixin, PremiumRequiredMixin, TemplateView):
    """Manage questions for an assessment."""

    template_name = "custom_assessments/questions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assessment = get_object_or_404(
            CustomAssessment,
            uuid=self.kwargs["uuid"],
            client=self.request.user.client_account,
        )
        context["assessment"] = assessment
        context["questions"] = assessment.questions.all()
        context["ai_form"] = AIGenerationForm()
        context["csv_form"] = CSVUploadForm()
        context["question_form"] = CustomQuestionForm()
        return context


class QuestionCreateView(LoginRequiredMixin, PremiumRequiredMixin, View):
    """Create a single question manually."""

    def post(self, request, uuid):
        assessment = get_object_or_404(
            CustomAssessment,
            uuid=uuid,
            client=request.user.client_account,
            status="draft",
        )

        form = CustomQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.assessment = assessment
            question.order = assessment.questions.count() + 1
            question.save()
            messages.success(request, "Question added successfully.")
        else:
            for error in form.errors.values():
                messages.error(request, error.as_text())

        return redirect("custom_assessments:questions", uuid=uuid)


class QuestionUpdateView(LoginRequiredMixin, PremiumRequiredMixin, View):
    """Update a question."""

    def post(self, request, uuid, question_id):
        assessment = get_object_or_404(
            CustomAssessment,
            uuid=uuid,
            client=request.user.client_account,
            status="draft",
        )
        question = get_object_or_404(CustomQuestion, pk=question_id, assessment=assessment)

        form = CustomQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, "Question updated.")
        else:
            for error in form.errors.values():
                messages.error(request, error.as_text())

        return redirect("custom_assessments:questions", uuid=uuid)


class QuestionDeleteView(LoginRequiredMixin, PremiumRequiredMixin, View):
    """Delete a question."""

    def post(self, request, uuid, question_id):
        assessment = get_object_or_404(
            CustomAssessment,
            uuid=uuid,
            client=request.user.client_account,
            status="draft",
        )
        question = get_object_or_404(CustomQuestion, pk=question_id, assessment=assessment)
        question.delete()

        # Reorder remaining questions
        for i, q in enumerate(assessment.questions.all(), start=1):
            q.order = i
            q.save(update_fields=["order"])

        messages.success(request, "Question deleted.")
        return redirect("custom_assessments:questions", uuid=uuid)


class CSVUploadView(LoginRequiredMixin, PremiumRequiredMixin, View):
    """Handle CSV file upload for bulk question import."""

    def post(self, request, uuid):
        assessment = get_object_or_404(
            CustomAssessment,
            uuid=uuid,
            client=request.user.client_account,
            status="draft",
        )

        form = CSVUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            for error in form.errors.values():
                messages.error(request, error.as_text())
            return redirect("custom_assessments:questions", uuid=uuid)

        csv_file = form.cleaned_data["csv_file"]
        content = csv_file.read()

        try:
            questions_data = parse_csv_questions(content)
            created = create_questions_from_data(assessment, questions_data)
            messages.success(request, f"Successfully imported {created} questions.")
        except CSVValidationError as e:
            for error in e.errors[:5]:  # Show first 5 errors
                messages.error(
                    request,
                    f"Row {error['row']}: {', '.join(error['errors'])}"
                )
            if len(e.errors) > 5:
                messages.error(request, f"... and {len(e.errors) - 5} more errors")

        return redirect("custom_assessments:questions", uuid=uuid)


class CSVTemplateDownloadView(LoginRequiredMixin, PremiumRequiredMixin, View):
    """Download CSV template."""

    def get(self, request):
        content = generate_csv_template()
        response = HttpResponse(content, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="assessment_questions_template.csv"'
        return response


class AIGenerateView(LoginRequiredMixin, PremiumRequiredMixin, View):
    """Generate questions using AI."""

    def post(self, request, uuid):
        assessment = get_object_or_404(
            CustomAssessment,
            uuid=uuid,
            client=request.user.client_account,
            status="draft",
        )

        form = AIGenerationForm(request.POST)
        if not form.is_valid():
            for error in form.errors.values():
                messages.error(request, error.as_text())
            return redirect("custom_assessments:questions", uuid=uuid)

        try:
            questions_data = generate_questions_with_ai(
                role_description=form.cleaned_data["role_description"],
                skills=form.cleaned_data["skills_to_test"],
                difficulty_level=form.cleaned_data["difficulty_level"],
                num_questions=form.cleaned_data["num_questions"],
            )

            # Save AI generation metadata
            assessment.role_description = form.cleaned_data["role_description"]
            assessment.skills_to_test = form.cleaned_data["skills_to_test"]
            assessment.ai_generated = True
            assessment.save(update_fields=[
                "role_description", "skills_to_test", "ai_generated", "updated_at"
            ])

            created = create_questions_from_data(assessment, questions_data)
            messages.success(request, f"Generated {created} questions using AI.")

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"AI generation failed: {str(e)}")

        return redirect("custom_assessments:questions", uuid=uuid)


class PublishView(LoginRequiredMixin, PremiumRequiredMixin, View):
    """Publish an assessment to make it available for use."""

    def post(self, request, uuid):
        assessment = get_object_or_404(
            CustomAssessment,
            uuid=uuid,
            client=request.user.client_account,
            status="draft",
        )

        if assessment.questions.count() < 1:
            messages.error(request, "Add at least one question before publishing.")
            return redirect("custom_assessments:questions", uuid=uuid)

        assessment.publish()
        messages.success(request, f'"{assessment.name}" is now published and ready to use!')
        return redirect("custom_assessments:detail", uuid=uuid)


class ArchiveView(LoginRequiredMixin, PremiumRequiredMixin, View):
    """Archive a published assessment."""

    def post(self, request, uuid):
        assessment = get_object_or_404(
            CustomAssessment,
            uuid=uuid,
            client=request.user.client_account,
        )
        assessment.archive()
        messages.success(request, f'"{assessment.name}" has been archived.')
        return redirect("custom_assessments:list")


class DuplicateView(LoginRequiredMixin, PremiumRequiredMixin, View):
    """Duplicate an assessment."""

    @method_decorator(check_custom_assessment_limit)
    def post(self, request, uuid):
        assessment = get_object_or_404(
            CustomAssessment,
            uuid=uuid,
            client=request.user.client_account,
        )
        new_assessment = assessment.duplicate()
        messages.success(request, f'Created copy: "{new_assessment.name}"')
        return redirect("custom_assessments:questions", uuid=new_assessment.uuid)


class InviteCandidateView(LoginRequiredMixin, PremiumRequiredMixin, View):
    """Invite a candidate to take the assessment."""

    def post(self, request, uuid):
        assessment = get_object_or_404(
            CustomAssessment,
            uuid=uuid,
            client=request.user.client_account,
            status="published",
        )

        form = InviteCandidateForm(
            request.POST,
            client_account=request.user.client_account
        )
        if not form.is_valid():
            for error in form.errors.values():
                messages.error(request, error.as_text())
            return redirect("custom_assessments:detail", uuid=uuid)

        # Get project if selected
        project = None
        project_id = form.cleaned_data.get("project")
        if project_id:
            from clients.models import ClientProject
            project = ClientProject.objects.filter(
                pk=project_id,
                client_account=request.user.client_account
            ).first()

        # Create session
        session = CustomAssessmentSession.objects.create(
            assessment=assessment,
            client=request.user.client_account,
            project=project,
            candidate_id=form.cleaned_data["candidate_id"],
            candidate_email=form.cleaned_data["candidate_email"],
            level=form.cleaned_data["level"],
            deadline_at=form.cleaned_data.get("deadline_at"),
        )

        # Initialize question order
        initialize_session(session)

        # Send email invitation
        assessment_url = request.build_absolute_uri(
            reverse("candidate:custom-session", args=[session.uuid])
        )
        email_sent, error = send_custom_assessment_invitation(session, assessment_url)

        if email_sent:
            messages.success(
                request,
                f"Invited {form.cleaned_data['candidate_id']} to take the assessment. "
                f"Invitation sent to {form.cleaned_data['candidate_email']}."
            )
        else:
            messages.warning(
                request,
                f"Invited {form.cleaned_data['candidate_id']} but email could not be sent. "
                f"Please share this link manually: {assessment_url}"
            )

        return redirect("custom_assessments:detail", uuid=uuid)


class SessionResultView(LoginRequiredMixin, PremiumRequiredMixin, DetailView):
    """View detailed results for a session."""

    model = CustomAssessmentSession
    template_name = "custom_assessments/session_result.html"
    context_object_name = "session"
    slug_field = "uuid"
    slug_url_kwarg = "session_uuid"

    def get_queryset(self):
        return CustomAssessmentSession.objects.filter(
            client=self.request.user.client_account
        ).select_related("assessment", "project")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Build detailed results
        session = self.object
        questions = session.assessment.questions.all()
        results = []

        for question in questions:
            answer = session.answers.get(str(question.pk))
            results.append({
                "question": question,
                "selected": answer,
                "is_correct": question.is_correct(answer) if answer else False,
            })

        context["results"] = results
        context["correct_count"] = sum(1 for r in results if r["is_correct"])
        context["total_count"] = len(results)

        return context
