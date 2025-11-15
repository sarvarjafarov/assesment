from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render


class ApiTokenRequestForm(forms.Form):
    company_name = forms.CharField(max_length=180, label="Company name")
    contact_email = forms.EmailField(label="Contact email")
    use_case = forms.CharField(
        label="Use case",
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Describe your integration goals."}),
    )


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
        if admin_email:
            send_mail(
                subject="API Token Request",
                message=body,
                from_email=payload["contact_email"],
                recipient_list=[admin_email],
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
            "rest_endpoints": [
                {"method": "POST", "path": "/api/marketing-assessment/start/", "description": "Create digital marketing session"},
                {"method": "GET", "path": "/api/marketing-assessment/<candidate_id>/questions/", "description": "Retrieve question bundle"},
                {"method": "POST", "path": "/api/marketing-assessment/<candidate_id>/submit/", "description": "Submit responses"},
                {"method": "GET", "path": "/api/marketing-assessment/<candidate_id>/results/", "description": "Fetch scores + fit summary"},
                {"method": "GET", "path": "/api/assessments/sessions/<uuid>/responses/", "description": "Behavioral profile + score breakdown"},
            ],
            "language_examples": [
                {
                    "title": "Python requests",
                    "code": "import requests\\nrequests.post('https://your-domain/api/marketing-assessment/start/', json={'candidate_id': 'cand-123'}, headers={'X-API-Key': '<token>'})",
                },
                {
                    "title": "Node.js fetch",
                    "code": "await fetch('/api/marketing-assessment/<id>/submit/', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-API-Key': token }, body: JSON.stringify(responses) });",
                },
                {
                    "title": "cURL",
                    "code": "curl -H 'X-API-Key: <token>' https://your-domain/api/assessments/sessions/<uuid>/responses/",
                },
            ],
            "form": form,
        },
    )
