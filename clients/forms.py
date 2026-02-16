from __future__ import annotations

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.utils import timezone

from behavioral_assessments.models import BehavioralAssessmentSession
from behavioral_assessments.services import generate_question_set as generate_behavioral_question_set
from marketing_assessments.models import DigitalMarketingAssessmentSession
from marketing_assessments.services import generate_question_set as generate_marketing_question_set
from pm_assessments.models import ProductAssessmentSession
from pm_assessments.services import generate_question_set as generate_pm_question_set
from ux_assessments.models import UXDesignAssessmentSession
from ux_assessments.services import generate_question_set as generate_ux_question_set
from hr_assessments.models import HRAssessmentSession
from hr_assessments.services import generate_question_set as generate_hr_question_set
from finance_assessments.models import FinanceAssessmentSession
from finance_assessments.services import generate_question_set as generate_finance_question_set

from .models import ClientAccount, ClientSessionNote, ClientProject

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
    allowed_types = {"image/png", "image/jpeg"}
    if content_type and content_type not in allowed_types:
        raise forms.ValidationError("Upload a PNG or JPG file.")
    max_size = 2 * 1024 * 1024
    if file_obj.size > max_size:
        raise forms.ValidationError("Logo must be smaller than 2MB.")
    # Validate magic bytes to prevent spoofed content-type
    header = file_obj.read(8)
    file_obj.seek(0)
    if not (header.startswith(b"\x89PNG\r\n\x1a\n") or header.startswith(b"\xff\xd8\xff")):
        raise forms.ValidationError("File content does not match a valid PNG or JPG image.")
    return file_obj


class ClientSignupForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Minimum 8 characters",
            "autocomplete": "new-password"
        }),
        help_text="At least 8 characters with a mix of letters and numbers",
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Re-enter your password",
            "autocomplete": "new-password"
        })
    )
    objectives = forms.CharField(
        label="Hiring objectives",
        widget=forms.Textarea(attrs={
            "rows": 4,
            "placeholder": "Tell us what success looks like for your hiring funnel.",
            "maxlength": 500
        }),
        help_text="What roles, volume, or timelines are most important? (500 characters max)",
        required=False,
    )
    requested_assessments = forms.MultipleChoiceField(
        label="Assessments you'd like to pilot",
        choices=ClientAccount.ASSESSMENT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    logo = forms.FileField(
        label="Company logo",
        required=False,
        help_text="Optional. Upload a PNG, JPG, or SVG (max 2MB) for dashboard branding",
        widget=forms.FileInput(attrs={"accept": "image/png,image/jpeg"}),
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
            "objectives",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={
                "placeholder": "John Smith",
                "autocomplete": "name"
            }),
            "company_name": forms.TextInput(attrs={
                "placeholder": "Acme Inc.",
                "autocomplete": "organization"
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "john@company.com",
                "autocomplete": "email"
            }),
            "phone_number": forms.TextInput(attrs={
                "placeholder": "+1 (555) 123-4567",
                "autocomplete": "tel",
                "type": "tel"
            }),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if ClientAccount.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Unable to create account with this email. It may already be registered."
            )
        return email

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if password and len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        # Run Django's full password validators (common passwords, similarity, numeric-only)
        password_validation.validate_password(password)
        return password

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
        from django.contrib.auth import get_user_model
        from django.db import IntegrityError

        account = super().save(commit=False)
        UserModel = get_user_model()

        # Safe first name: handle empty or single-word full_name
        full_name = (account.full_name or "").strip()
        parts = full_name.split()
        first_name = parts[0] if parts else (account.email or "user").split("@")[0] or "User"

        # Wrap User + ClientAccount creation in a transaction to prevent orphaned users
        with transaction.atomic():
            try:
                user = UserModel.objects.create_user(
                    username=account.email,
                    email=account.email,
                    password=self.cleaned_data["password1"],
                    first_name=first_name,
                )
            except IntegrityError:
                raise forms.ValidationError(
                    "Unable to create account with this email. It may already be registered."
                )

            user.is_active = False
            user.save(update_fields=["is_active"])
            account.user = user
            account.requested_assessments = self.cleaned_data.get("requested_assessments", [])
            objectives = self.cleaned_data.get("objectives", "").strip()
            if objectives:
                account.notes = f"Objectives: {objectives}"
            if commit:
                account.save()
        return account


class ClientLoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email address")

    def clean_username(self):
        """Normalize email to lowercase to prevent case-sensitive login issues."""
        return self.cleaned_data.get("username", "").lower().strip()

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


LEVEL_CHOICES = [
    ("junior", "Junior (0-2 years)"),
    ("mid", "Mid-Level (2-5 years)"),
    ("senior", "Senior (5+ years)"),
]


class BaseClientInviteForm(forms.Form):
    candidate_identifier = forms.CharField(
        label="Candidate identifier (email or ID)",
        help_text="Shared with the candidate to access their workspace.",
    )
    level = forms.ChoiceField(
        label="Assessment Level",
        choices=LEVEL_CHOICES,
        initial="mid",
        help_text="Select the experience level this assessment should target",
    )
    duration_minutes = forms.IntegerField(min_value=5, initial=30, label="Duration (minutes)")
    send_at = forms.DateTimeField(
        required=False,
        label="Schedule send (optional)",
        help_text="Leave blank to send immediately.",
        input_formats=["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%m/%d/%Y %H:%M"],
        widget=forms.DateTimeInput(attrs={
            "class": "datetime-picker",
            "placeholder": "Select date and time",
        }),
    )
    project = forms.ModelChoiceField(
        label="Position",
        queryset=ClientProject.objects.none(),
        help_text="Each invite must be tied to a position.",
    )
    deadline_type = forms.ChoiceField(
        required=False,
        initial="none",
        label="Completion deadline",
        choices=[
            ("none", "No deadline"),
            ("relative", "Days from invite"),
            ("absolute", "Specific date"),
        ],
    )
    deadline_days = forms.IntegerField(
        required=False,
        min_value=1,
        label="Days to complete",
        help_text="Number of days from when invite is sent",
    )
    deadline_at = forms.DateTimeField(
        required=False,
        label="Deadline date",
        help_text="Select the deadline date and time.",
        input_formats=["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%m/%d/%Y %H:%M", "%Y-%m-%d"],
        widget=forms.DateTimeInput(attrs={
            "class": "datetime-picker",
            "placeholder": "Select date and time",
        }),
    )

    model = None
    generate_question_set = None

    def __init__(self, *args, client: ClientAccount | None = None, **kwargs):
        self.client = client
        if not client:
            raise ValueError("client is required")
        super().__init__(*args, **kwargs)
        project_qs = client.projects.order_by("-created_at")
        self.fields["project"].queryset = project_qs
        if not project_qs.exists():
            self.fields["project"].help_text = "Create a position first."

    def clean(self):
        cleaned = super().clean()
        if not self.client.projects.exists():
            raise forms.ValidationError("Create a position before inviting candidates.")
        generator = self.generate_question_set
        if not generator:
            raise forms.ValidationError("Assessment configuration missing.")
        level = cleaned.get("level", "mid")
        question_set = generator(level=level)
        if not question_set:
            raise forms.ValidationError("No questions are active right now.")
        self.question_set = question_set
        # Recheck quota under a row lock to prevent TOCTOU race conditions
        with transaction.atomic():
            from .models import ClientAccount
            locked = ClientAccount.objects.select_for_update().get(pk=self.client.pk)
            remaining = locked.invites_remaining()
            if remaining is not None and remaining <= 0:
                raise forms.ValidationError(
                    "You've reached your monthly invite quota. Upgrade your plan to send more invites."
                )

        # Validate deadline fields
        deadline_type = cleaned.get("deadline_type")
        deadline_days = cleaned.get("deadline_days")
        deadline_at = cleaned.get("deadline_at")

        if deadline_type == "relative" and not deadline_days:
            self.add_error("deadline_days", "Days to complete is required for relative deadlines")
        if deadline_type == "absolute" and not deadline_at:
            self.add_error("deadline_at", "Deadline date is required for absolute deadlines")
        if deadline_type == "none":
            cleaned["deadline_days"] = None
            cleaned["deadline_at"] = None

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
        level = self.cleaned_data.get("level", "mid")
        session, _ = self.model.objects.get_or_create(
            candidate_id=candidate_id,
            client=self.client,
            defaults={"status": "draft"},
        )
        session.question_set = getattr(self, "question_set", None) or self.generate_question_set(level=level)
        send_at = self.cleaned_data.get("send_at")
        session.duration_minutes = self.cleaned_data["duration_minutes"]
        session.started_at = None
        session.client = self.client
        session.project = self.cleaned_data["project"]
        session.level = level
        session.deadline_type = self.cleaned_data.get("deadline_type", "none")
        session.deadline_days = self.cleaned_data.get("deadline_days")
        session.deadline_at = self.cleaned_data.get("deadline_at")
        if send_at:
            session.status = "draft"
            session.scheduled_for = send_at
        else:
            session.status = "in_progress"
            session.scheduled_for = None
        session.save(
            update_fields=[
                "question_set",
                "status",
                "scheduled_for",
                "duration_minutes",
                "started_at",
                "client",
                "project",
                "level",
                "deadline_type",
                "deadline_days",
                "deadline_at",
            ]
        )
        return session


class ClientProductInviteForm(BaseClientInviteForm):
    model = ProductAssessmentSession
    generate_question_set = staticmethod(generate_pm_question_set)

    def save(self) -> ProductAssessmentSession:
        candidate_id = self.cleaned_data["candidate_identifier"]
        level = self.cleaned_data.get("level", "mid")
        session, _ = self.model.objects.get_or_create(
            candidate_id=candidate_id,
            client=self.client,
            defaults={"status": "draft"},
        )
        session.question_set = getattr(self, "question_set", None) or self.generate_question_set(level=level)
        send_at = self.cleaned_data.get("send_at")
        session.duration_minutes = self.cleaned_data["duration_minutes"]
        session.started_at = None
        session.client = self.client
        session.project = self.cleaned_data["project"]
        session.level = level
        session.deadline_type = self.cleaned_data.get("deadline_type", "none")
        session.deadline_days = self.cleaned_data.get("deadline_days")
        session.deadline_at = self.cleaned_data.get("deadline_at")
        if send_at:
            session.status = "draft"
            session.scheduled_for = send_at
        else:
            session.status = "in_progress"
            session.scheduled_for = None
        session.save(
            update_fields=[
                "question_set",
                "status",
                "scheduled_for",
                "duration_minutes",
                "started_at",
                "client",
                "project",
                "level",
                "deadline_type",
                "deadline_days",
                "deadline_at",
            ]
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
        level = self.cleaned_data.get("level", "mid")
        session, _ = self.model.objects.get_or_create(
            candidate_id=candidate_id,
            client=self.client,
            defaults={"status": "draft"},
        )
        session.question_set = getattr(self, "question_set", None) or self.generate_question_set(level=level)
        send_at = self.cleaned_data.get("send_at")
        session.duration_minutes = self.cleaned_data["duration_minutes"]
        session.started_at = None
        session.client = self.client
        session.project = self.cleaned_data["project"]
        session.level = level
        session.deadline_type = self.cleaned_data.get("deadline_type", "none")
        session.deadline_days = self.cleaned_data.get("deadline_days")
        session.deadline_at = self.cleaned_data.get("deadline_at")
        if send_at:
            session.status = "draft"
            session.scheduled_for = send_at
        else:
            session.status = "in_progress"
            session.scheduled_for = None
        session.save(
            update_fields=[
                "question_set",
                "status",
                "scheduled_for",
                "duration_minutes",
                "started_at",
                "client",
                "project",
                "level",
                "deadline_type",
                "deadline_days",
                "deadline_at",
            ]
        )
        return session


class ClientUXDesignInviteForm(BaseClientInviteForm):
    model = UXDesignAssessmentSession
    generate_question_set = staticmethod(generate_ux_question_set)

    def save(self) -> UXDesignAssessmentSession:
        candidate_id = self.cleaned_data["candidate_identifier"]
        level = self.cleaned_data.get("level", "mid")
        session, _ = self.model.objects.get_or_create(
            candidate_id=candidate_id,
            client=self.client,
            defaults={"status": "draft"},
        )
        session.question_set = getattr(self, "question_set", None) or self.generate_question_set(level=level)
        send_at = self.cleaned_data.get("send_at")
        session.duration_minutes = self.cleaned_data["duration_minutes"]
        session.started_at = None
        session.client = self.client
        session.project = self.cleaned_data["project"]
        session.level = level
        session.deadline_type = self.cleaned_data.get("deadline_type", "none")
        session.deadline_days = self.cleaned_data.get("deadline_days")
        session.deadline_at = self.cleaned_data.get("deadline_at")
        if send_at:
            session.status = "draft"
            session.scheduled_for = send_at
        else:
            session.status = "in_progress"
            session.scheduled_for = None
        session.save(
            update_fields=[
                "question_set",
                "status",
                "scheduled_for",
                "duration_minutes",
                "started_at",
                "client",
                "project",
                "level",
                "deadline_type",
                "deadline_days",
                "deadline_at",
            ]
        )
        return session


class ClientHRInviteForm(BaseClientInviteForm):
    model = HRAssessmentSession
    generate_question_set = staticmethod(generate_hr_question_set)

    def save(self) -> HRAssessmentSession:
        candidate_id = self.cleaned_data["candidate_identifier"]
        level = self.cleaned_data.get("level", "mid")
        session, _ = self.model.objects.get_or_create(
            candidate_id=candidate_id,
            client=self.client,
            defaults={"status": "draft"},
        )
        session.question_set = getattr(self, "question_set", None) or self.generate_question_set(level=level)
        send_at = self.cleaned_data.get("send_at")
        session.duration_minutes = self.cleaned_data["duration_minutes"]
        session.started_at = None
        session.client = self.client
        session.project = self.cleaned_data["project"]
        session.level = level
        session.deadline_type = self.cleaned_data.get("deadline_type", "none")
        session.deadline_days = self.cleaned_data.get("deadline_days")
        session.deadline_at = self.cleaned_data.get("deadline_at")
        if send_at:
            session.status = "draft"
            session.scheduled_for = send_at
        else:
            session.status = "in_progress"
            session.scheduled_for = None
        session.save(
            update_fields=[
                "question_set",
                "status",
                "scheduled_for",
                "duration_minutes",
                "started_at",
                "client",
                "project",
                "level",
                "deadline_type",
                "deadline_days",
                "deadline_at",
            ]
        )
        return session


class ClientFinanceInviteForm(BaseClientInviteForm):
    model = FinanceAssessmentSession
    generate_question_set = staticmethod(generate_finance_question_set)

    def save(self) -> FinanceAssessmentSession:
        candidate_id = self.cleaned_data["candidate_identifier"]
        level = self.cleaned_data.get("level", "mid")
        session, _ = self.model.objects.get_or_create(
            candidate_id=candidate_id,
            client=self.client,
            defaults={"status": "draft"},
        )
        session.question_set = getattr(self, "question_set", None) or self.generate_question_set(level=level)
        send_at = self.cleaned_data.get("send_at")
        session.duration_minutes = self.cleaned_data["duration_minutes"]
        session.started_at = None
        session.client = self.client
        session.project = self.cleaned_data["project"]
        session.level = level
        session.deadline_type = self.cleaned_data.get("deadline_type", "none")
        session.deadline_days = self.cleaned_data.get("deadline_days")
        session.deadline_at = self.cleaned_data.get("deadline_at")
        if send_at:
            session.status = "draft"
            session.scheduled_for = send_at
        else:
            session.status = "in_progress"
            session.scheduled_for = None
        session.save(
            update_fields=[
                "question_set",
                "status",
                "scheduled_for",
                "duration_minutes",
                "started_at",
                "client",
                "project",
                "level",
                "deadline_type",
                "deadline_days",
                "deadline_at",
            ]
        )
        return session


class ClientLogoForm(forms.Form):
    logo = forms.FileField(
        label="Upload new logo",
        widget=forms.FileInput(attrs={"accept": "image/png,image/jpeg"}),
    )

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        return _validate_logo_file(logo)


class ClientBulkInviteForm(forms.Form):
    project = forms.ModelChoiceField(
        label="Position",
        queryset=ClientProject.objects.none(),
    )
    csv_file = forms.FileField(
        label="Bulk upload (CSV)",
        help_text="Include headers: candidate_id,duration_minutes,send_at (optional).",
    )

    def __init__(self, *args, client: ClientAccount | None = None, **kwargs):
        self.client = client
        if not client:
            raise ValueError("client is required")
        super().__init__(*args, **kwargs)
        self.fields["project"].queryset = client.projects.order_by("-created_at")

    def clean_csv_file(self):
        csv_file = self.cleaned_data.get("csv_file")
        if not csv_file:
            return csv_file
        if csv_file.size > 2 * 1024 * 1024:
            raise forms.ValidationError("CSV must be under 2MB.")
        return csv_file

    def clean(self):
        cleaned = super().clean()
        if not self.client.projects.exists():
            raise forms.ValidationError("Create a project before uploading invites.")
        return cleaned


class ClientSessionNoteForm(forms.ModelForm):
    note_type = forms.ChoiceField(choices=ClientSessionNote.NOTE_TYPES, label="Type")
    decision = forms.ChoiceField(
        choices=[("", "— Select decision —")] + ClientSessionNote.DECISION_CHOICES,
        required=False,
        label="Decision outcome",
    )

    class Meta:
        model = ClientSessionNote
        fields = ["note_type", "decision", "note", "needs_review"]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3, "placeholder": "Add context or next steps"}),
        }
        labels = {
            "note": "Internal note",
            "needs_review": "Mark as needs review",
        }

    def clean(self):
        cleaned = super().clean()
        note_type = cleaned.get("note_type")
        decision = cleaned.get("decision")
        if note_type == "decision" and not decision:
            self.add_error("decision", "Pick a decision outcome.")
        if note_type != "decision":
            cleaned["decision"] = ""
        note = cleaned.get("note", "").strip()
        needs_review = cleaned.get("needs_review")
        if not note and not needs_review and note_type != "decision":
            raise forms.ValidationError("Add a note, flag the session, or record a decision.")
        return cleaned


class ClientProjectForm(forms.ModelForm):
    class Meta:
        model = ClientProject
        fields = [
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
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "target_start_date": forms.DateInput(attrs={"type": "date"}),
            "required_skills": forms.TextInput(attrs={"placeholder": "e.g. Python, SQL, Leadership"}),
            "salary_min": forms.NumberInput(attrs={"placeholder": "Min"}),
            "salary_max": forms.NumberInput(attrs={"placeholder": "Max"}),
        }

    def __init__(self, *args, client: ClientAccount, **kwargs):
        self.client = client
        super().__init__(*args, **kwargs)
        # status is not rendered in the quick-create template; allow blank so
        # the form validates and falls back to the model default.
        self.fields["status"].required = False
        self.fields["status"].initial = ClientProject.STATUS_ACTIVE

    def save(self, commit=True):
        project = super().save(commit=False)
        project.client = self.client
        if not project.status:
            project.status = ClientProject.STATUS_ACTIVE
        if commit:
            project.save()
        return project


class SocialProfileCompleteForm(forms.ModelForm):
    """Form for completing profile after social authentication signup."""

    requested_assessments = forms.MultipleChoiceField(
        label="Assessments you'd like to pilot",
        choices=ClientAccount.ASSESSMENT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = ClientAccount
        fields = [
            "company_name",
            "phone_number",
            "employee_size",
            "requested_assessments",
        ]
        widgets = {
            "company_name": forms.TextInput(attrs={
                "placeholder": "Acme Inc.",
                "autocomplete": "organization"
            }),
            "phone_number": forms.TextInput(attrs={
                "placeholder": "+1 (555) 123-4567",
                "autocomplete": "tel",
                "type": "tel"
            }),
        }

    def save(self, commit=True) -> ClientAccount:
        account = super().save(commit=False)
        account.requested_assessments = self.cleaned_data.get("requested_assessments", [])
        if commit:
            account.save()
        return account


class ClientPasswordChangeForm(forms.Form):
    """Form for changing client password."""

    current_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Enter current password",
            "autocomplete": "current-password",
        }),
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Minimum 8 characters",
            "autocomplete": "new-password",
        }),
        help_text="At least 8 characters with a mix of letters and numbers",
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Re-enter new password",
            "autocomplete": "new-password",
        }),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get("current_password")
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Your current password is incorrect.")
        return current_password

    def clean_new_password1(self):
        password = self.cleaned_data.get("new_password1")
        if password and len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        # Run Django's password validators
        password_validation.validate_password(password, self.user)
        return password

    def clean(self):
        cleaned = super().clean()
        new_password1 = cleaned.get("new_password1")
        new_password2 = cleaned.get("new_password2")
        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error("new_password2", "Passwords do not match.")
        return cleaned

    def save(self):
        self.user.set_password(self.cleaned_data["new_password1"])
        self.user.save(update_fields=["password"])
        return self.user


class EmailPreferencesForm(forms.ModelForm):
    """Form for managing email notification preferences."""

    class Meta:
        model = ClientAccount
        fields = [
            "receive_weekly_summary",
            "receive_completion_alerts",
            "receive_new_candidate_alerts",
        ]
        widgets = {
            "receive_weekly_summary": forms.CheckboxInput(attrs={
                "class": "toggle-checkbox",
            }),
            "receive_completion_alerts": forms.CheckboxInput(attrs={
                "class": "toggle-checkbox",
            }),
            "receive_new_candidate_alerts": forms.CheckboxInput(attrs={
                "class": "toggle-checkbox",
            }),
        }
        labels = {
            "receive_weekly_summary": "Weekly Summary Email",
            "receive_completion_alerts": "Assessment Completion Alerts",
            "receive_new_candidate_alerts": "New Candidate Alerts",
        }
        help_texts = {
            "receive_weekly_summary": "Receive a weekly digest of your assessment activity and candidate results.",
            "receive_completion_alerts": "Get notified when a candidate completes an assessment.",
            "receive_new_candidate_alerts": "Get notified when a new candidate starts an assessment.",
        }


class BrandingSettingsForm(forms.ModelForm):
    """Form for managing white-labeling and branding settings."""

    brand_primary_color = forms.CharField(
        max_length=7,
        widget=forms.TextInput(attrs={
            "type": "color",
            "class": "color-picker",
        }),
        label="Primary Color",
        help_text="Main brand color used for buttons, links, and highlights",
    )
    brand_secondary_color = forms.CharField(
        max_length=7,
        widget=forms.TextInput(attrs={
            "type": "color",
            "class": "color-picker",
        }),
        label="Text Color",
        help_text="Primary text and heading color",
    )
    brand_background_color = forms.CharField(
        max_length=7,
        widget=forms.TextInput(attrs={
            "type": "color",
            "class": "color-picker",
        }),
        label="Background Color",
        help_text="Assessment page background color",
    )

    class Meta:
        model = ClientAccount
        fields = [
            "brand_primary_color",
            "brand_secondary_color",
            "brand_background_color",
            "custom_email_sender_name",
            "custom_welcome_message",
            "custom_footer_text",
            "hide_evalon_branding",
        ]
        widgets = {
            "custom_email_sender_name": forms.TextInput(attrs={
                "placeholder": "e.g., Acme Hiring Team",
            }),
            "custom_welcome_message": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Add a custom welcome message for candidates...",
            }),
            "custom_footer_text": forms.TextInput(attrs={
                "placeholder": "e.g., Assessment powered by Acme Inc.",
            }),
            "hide_evalon_branding": forms.CheckboxInput(attrs={
                "class": "toggle-checkbox",
            }),
        }
        labels = {
            "custom_email_sender_name": "Email Sender Name",
            "custom_welcome_message": "Custom Welcome Message",
            "custom_footer_text": "Custom Footer Text",
            "hide_evalon_branding": "Hide Evalon Branding",
        }
        help_texts = {
            "custom_email_sender_name": "Custom sender name for assessment invitation emails",
            "custom_welcome_message": "Shown on the assessment intro page before candidates start",
            "custom_footer_text": "Replaces 'Powered by Evalon' in candidate-facing pages",
            "hide_evalon_branding": "Remove Evalon branding from candidate-facing pages (Pro/Enterprise only)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable white-labeling fields for non-Pro/Enterprise plans
        if self.instance and not self.instance.can_use_white_labeling:
            self.fields["hide_evalon_branding"].disabled = True
            self.fields["hide_evalon_branding"].help_text = (
                "Upgrade to Pro or Enterprise to use this feature"
            )
            self.fields["custom_email_sender_name"].disabled = True
            self.fields["custom_email_sender_name"].help_text = (
                "Upgrade to Pro or Enterprise to customize email sender"
            )

    def clean(self):
        cleaned = super().clean()
        # Server-side enforcement of plan restrictions
        if self.instance and not self.instance.can_use_white_labeling:
            cleaned["hide_evalon_branding"] = False
            cleaned["custom_email_sender_name"] = ""
        return cleaned


class WebhookSettingsForm(forms.ModelForm):
    """Form for managing webhook and API integration settings."""

    WEBHOOK_EVENT_CHOICES = [
        ("session.created", "Session Created - When a new assessment session is created"),
        ("session.started", "Session Started - When a candidate starts an assessment"),
        ("session.completed", "Session Completed - When a candidate completes an assessment"),
        ("session.expired", "Session Expired - When an assessment session expires"),
    ]

    webhook_events = forms.MultipleChoiceField(
        choices=WEBHOOK_EVENT_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "webhook-event-checkbox"}),
        label="Webhook Events",
        help_text="Select which events should trigger webhook notifications",
    )

    class Meta:
        model = ClientAccount
        fields = [
            "webhook_enabled",
            "webhook_url",
            "webhook_events",
        ]
        widgets = {
            "webhook_enabled": forms.CheckboxInput(attrs={"class": "toggle-checkbox"}),
            "webhook_url": forms.URLInput(attrs={
                "placeholder": "https://your-server.com/webhooks/evalon",
                "class": "webhook-url-input",
            }),
        }
        labels = {
            "webhook_enabled": "Enable Webhooks",
            "webhook_url": "Webhook URL",
        }
        help_texts = {
            "webhook_enabled": "Enable or disable webhook notifications",
            "webhook_url": "The URL where webhook payloads will be sent (must be HTTPS)",
        }

    def clean_webhook_url(self):
        url = self.cleaned_data.get("webhook_url", "").strip()
        if url and not url.startswith("https://"):
            raise forms.ValidationError("Webhook URL must use HTTPS for security")
        return url

    def clean(self):
        cleaned = super().clean()
        enabled = cleaned.get("webhook_enabled")
        url = cleaned.get("webhook_url")

        if enabled and not url:
            self.add_error("webhook_url", "Webhook URL is required when webhooks are enabled")

        return cleaned
