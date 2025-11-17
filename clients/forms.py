from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import ClientAccount

PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
}


class ClientSignupForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)
    requested_assessments = forms.MultipleChoiceField(
        label="Assessments you'd like to pilot",
        choices=ClientAccount.ASSESSMENT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = ClientAccount
        fields = [
            "full_name",
            "company_name",
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
