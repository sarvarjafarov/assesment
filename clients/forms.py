from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone

from behavioral_assessments.models import BehavioralAssessmentSession
from behavioral_assessments.services import generate_question_set as generate_behavioral_question_set
from marketing_assessments.models import DigitalMarketingAssessmentSession
from marketing_assessments.services import generate_question_set as generate_marketing_question_set
from pm_assessments.models import ProductAssessmentSession
from pm_assessments.services import generate_question_set as generate_pm_question_set

from .models import ClientAccount, ClientSessionNote

PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
}


def _validate_logo_file(file_obj):
    if not file_obj:
        return file_obj
    content_type = getattr(file_obj, "content_type", "")
    allowed_types = {"image/png", "image/jpeg", "image/svg+xml"}
    if content_type and content_type not in allowed_types:
        raise forms.ValidationError("Upload a PNG, JPG, or SVG file.")
    max_size = 2 * 1024 * 1024
    if file_obj.size > max_size:
        raise forms.ValidationError("Logo must be smaller than 2MB.")
    return file_obj


class ClientSignupForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)
    requested_assessments = forms.MultipleChoiceField(
        label="Assessments you'd like to pilot",
        choices=ClientAccount.ASSESSMENT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    logo = forms.FileField(
        label="Company logo",
        required=False,
        help_text="Optional. Upload a PNG or SVG so your dashboard is branded.",
        widget=forms.FileInput(attrs={"accept": "image/png,image/jpeg,image/svg+xml"}),
    )

    class Meta:
        model = ClientAccount
        fields = [
            "full_name",
            "company_name",
            "logo",
            "email",
            "phone_number",
            "employee_size",
            "requested_assessments",
        ]

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if email.split("@")[-1] in PUBLIC_EMAIL_DOMAINS:
            raise forms.ValidationError("Please use your company email address.")
        if ClientAccount.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Passwords do not match.")
        return cleaned

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        return _validate_logo_file(logo)

    def save(self, commit=True) -> ClientAccount:
        account = super().save(commit=False)
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()
        user = UserModel.objects.create_user(
            username=account.email,
            email=account.email,
            password=self.cleaned_data["password1"],
            first_name=account.full_name.split(" ")[0],
        )
        user.is_active = False
        user.save(update_fields=["is_active"])
        account.user = user
        account.requested_assessments = self.cleaned_data.get("requested_assessments", [])
        if commit:
            account.save()
        return account


class ClientLoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email address")

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        try:
            account = user.client_account
        except ClientAccount.DoesNotExist:
            raise forms.ValidationError(
                "This login is reserved for approved client accounts.", code="inactive"
            )
        if account.status != "approved":
            raise forms.ValidationError(
                "Your account is still pending approval.", code="inactive"
            )


class BaseClientInviteForm(forms.Form):
    candidate_identifier = forms.CharField(
        label="Candidate identifier (email or ID)",
        help_text="Shared with the candidate to access their workspace.",
    )
    duration_minutes = forms.IntegerField(min_value=5, initial=30, label="Duration (minutes)")
    send_at = forms.DateTimeField(
        required=False,
        label="Schedule send (optional)",
        help_text="Leave blank to send immediately. Use YYYY-MM-DD HH:MM format.",
        input_formats=["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%m/%d/%Y %H:%M"],
    )

    model = None
    generate_question_set = None

    def __init__(self, *args, client: ClientAccount | None = None, **kwargs):
        self.client = client
        if not client:
            raise ValueError("client is required")
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        generator = self.generate_question_set
        if not generator:
            raise forms.ValidationError("Assessment configuration missing.")
        question_set = generator()
        if not question_set:
            raise forms.ValidationError("No questions are active right now.")
        self.question_set = question_set
        return cleaned

    def clean_send_at(self):
        send_at = self.cleaned_data.get("send_at")
        if not send_at:
            return send_at
        if timezone.is_naive(send_at):
            send_at = timezone.make_aware(send_at, timezone.get_current_timezone())
        if send_at < timezone.now():
            raise forms.ValidationError("Scheduled time must be in the future.")
        return send_at

    def save(self):
        raise NotImplementedError


class ClientMarketingInviteForm(BaseClientInviteForm):
    model = DigitalMarketingAssessmentSession
    generate_question_set = staticmethod(generate_marketing_question_set)

    def save(self) -> DigitalMarketingAssessmentSession:
        candidate_id = self.cleaned_data["candidate_identifier"]
        session, _ = self.model.objects.get_or_create(
            candidate_id=candidate_id,
            client=self.client,
            defaults={"status": "draft"},
        )
        session.question_set = getattr(self, "question_set", None) or self.generate_question_set()
        send_at = self.cleaned_data.get("send_at")
        session.duration_minutes = self.cleaned_data["duration_minutes"]
        session.started_at = None
        session.client = self.client
        if send_at:
            session.status = "draft"
            session.scheduled_for = send_at
        else:
            session.status = "in_progress"
            session.scheduled_for = None
        session.save(
            update_fields=["question_set", "status", "scheduled_for", "duration_minutes", "started_at", "client"]
        )
        return session


class ClientProductInviteForm(BaseClientInviteForm):
    model = ProductAssessmentSession
    generate_question_set = staticmethod(generate_pm_question_set)

    def save(self) -> ProductAssessmentSession:
        candidate_id = self.cleaned_data["candidate_identifier"]
        session, _ = self.model.objects.get_or_create(
            candidate_id=candidate_id,
            client=self.client,
            defaults={"status": "draft"},
        )
        session.question_set = getattr(self, "question_set", None) or self.generate_question_set()
        send_at = self.cleaned_data.get("send_at")
        session.duration_minutes = self.cleaned_data["duration_minutes"]
        session.started_at = None
        session.client = self.client
        if send_at:
            session.status = "draft"
            session.scheduled_for = send_at
        else:
            session.status = "in_progress"
            session.scheduled_for = None
        session.save(
            update_fields=["question_set", "status", "scheduled_for", "duration_minutes", "started_at", "client"]
        )
        return session


class ClientBehavioralInviteForm(BaseClientInviteForm):
    model = BehavioralAssessmentSession
    generate_question_set = staticmethod(generate_behavioral_question_set)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["duration_minutes"].initial = 15

    def save(self) -> BehavioralAssessmentSession:
        candidate_id = self.cleaned_data["candidate_identifier"]
        session, _ = self.model.objects.get_or_create(
            candidate_id=candidate_id,
            client=self.client,
            defaults={"status": "draft"},
        )
        session.question_set = getattr(self, "question_set", None) or self.generate_question_set()
        send_at = self.cleaned_data.get("send_at")
        session.duration_minutes = self.cleaned_data["duration_minutes"]
        session.started_at = None
        session.client = self.client
        if send_at:
            session.status = "draft"
            session.scheduled_for = send_at
        else:
            session.status = "in_progress"
            session.scheduled_for = None
        session.save(
            update_fields=["question_set", "status", "scheduled_for", "duration_minutes", "started_at", "client"]
        )
        return session


class ClientLogoForm(forms.Form):
    logo = forms.FileField(
        label="Upload new logo",
        widget=forms.FileInput(attrs={"accept": "image/png,image/jpeg,image/svg+xml"}),
    )

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        return _validate_logo_file(logo)


class ClientBulkInviteForm(forms.Form):
    csv_file = forms.FileField(
        label="Bulk upload (CSV)",
        help_text="Include headers: candidate_id,duration_minutes,send_at (optional).",
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data.get("csv_file")
        if not csv_file:
            return csv_file
        if csv_file.size > 2 * 1024 * 1024:
            raise forms.ValidationError("CSV must be under 2MB.")
        return csv_file


class ClientSessionNoteForm(forms.ModelForm):
    class Meta:
        model = ClientSessionNote
        fields = ["note", "needs_review"]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3, "placeholder": "Add context or next steps"}),
        }
        labels = {
            "note": "Internal note",
            "needs_review": "Mark as needs review",
        }

    def clean(self):
        cleaned = super().clean()
        note = cleaned.get("note", "").strip()
        needs_review = cleaned.get("needs_review")
        if not note and not needs_review:
            raise forms.ValidationError("Add a note or flag the session for review.")
        return cleaned
