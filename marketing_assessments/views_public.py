from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render


class ApiTokenRequestForm(forms.Form):
    company_name = forms.CharField(max_length=180)
    contact_email = forms.EmailField()
    use_case = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}))


def api_overview(request):
    form = ApiTokenRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        payload = form.cleaned_data
        admin_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
        body = (
            f"Company: {payload['company_name']}\n"
            f"Email: {payload['contact_email']}\n"
            f"Use case:\n{payload['use_case']}"
        )
        recipients = [admin_email] if admin_email else []
        if recipients:
            send_mail(
                subject="API Token Request",
                message=body,
                from_email=payload["contact_email"],
                recipient_list=recipients,
                fail_silently=True,
            )
        messages.success(
            request,
            "Thanks! Our team will review your request and share credentials shortly.",
        )
        return redirect("marketing-assessment:api")
    return render(
        request,
        "marketing/api_overview.html",
        {
            "endpoints": [
                {"method": "POST", "path": "/api/marketing-assessment/start/", "description": "Create a session"},
                {"method": "GET", "path": "/api/marketing-assessment/<candidate_id>/questions/", "description": "Retrieve questions"},
                {"method": "POST", "path": "/api/marketing-assessment/<candidate_id>/submit/", "description": "Submit responses"},
                {"method": "GET", "path": "/api/marketing-assessment/<candidate_id>/results/", "description": "Fetch scores"},
            ],
            "form": form,
        },
    )
