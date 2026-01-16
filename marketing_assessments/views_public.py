import json

from django import forms
from django.contrib import messages
from django.shortcuts import redirect, render

from pages.models import APIAccessRequest


class ApiTokenRequestForm(forms.ModelForm):
    """Form for API access requests - saves to database."""

    class Meta:
        model = APIAccessRequest
        fields = ['company_name', 'contact_email', 'use_case']
        widgets = {
            'company_name': forms.TextInput(attrs={'placeholder': 'Your Company'}),
            'contact_email': forms.EmailInput(attrs={'placeholder': 'you@company.com'}),
            'use_case': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describe your integration goals - ATS sync, workflow automation, custom dashboards, etc.'
            }),
        }
        labels = {
            'company_name': 'Company name',
            'contact_email': 'Contact email',
            'use_case': 'Use case',
        }


def api_overview(request):
    form = ApiTokenRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        api_request = form.save()
        messages.success(
            request,
            f"Thanks! We've received your API access request for {api_request.company_name}. Our team will review and share credentials within 1 business day.",
        )
        return redirect("marketing_assessments:api")

    # API documentation resources (contact us for access)
    postman_url = None  # Available upon API access approval
    openapi_url = None  # Available upon API access approval
    schema_url = None   # Available upon API access approval
    rest_endpoints = [
        {
            "method": "POST",
            "path": "/api/marketing-assessment/start/",
            "description": "Create digital marketing session",
            "request_schema": {"candidate_id": "string", "assessment": "marketing|pm|behavioral"},
            "response_schema": {
                "session_uuid": "UUID",
                "launch_url": "https://session-link",
                "expires_at": "ISO8601 timestamp",
            },
        },
        {
            "method": "GET",
            "path": "/api/marketing-assessment/<candidate_id>/questions/",
            "description": "Retrieve question bundle",
            "request_schema": {"headers": {"X-API-Key": "token"}},
            "response_schema": {
                "questions": [
                    {"id": 42, "type": "multiple_choice", "category": "strategy", "prompt": "text", "options": ["A", "B", "C"]},
                ],
                "time_limit_minutes": 45,
            },
        },
        {
            "method": "POST",
            "path": "/api/marketing-assessment/<candidate_id>/submit/",
            "description": "Submit responses",
            "request_schema": [
                {"question_id": 42, "answer": "A"},
                {"question_id": 51, "selected": "most"},
            ],
            "response_schema": {"detail": "Assessment submitted", "session_uuid": "UUID"},
        },
        {
            "method": "GET",
            "path": "/api/marketing-assessment/<candidate_id>/results/",
            "description": "Fetch scores + fit summary",
            "request_schema": {"headers": {"X-API-Key": "token"}},
            "response_schema": {
                "overall_score": 84.2,
                "category_breakdown": {"strategy": 86, "execution": 82},
                "fit_recommendation": "text",
            },
        },
        {
            "method": "GET",
            "path": "/api/assessments/sessions/<uuid>/responses/",
            "description": "Behavioral profile + score breakdown",
            "request_schema": {"headers": {"X-API-Key": "token"}},
            "response_schema": {
                "session_uuid": "UUID",
                "insights": [{"trait": "Adaptability", "score": 78}],
                "raw_responses": [{"block": 1, "most": "A", "least": "C"}],
            },
        },
    ]
    for endpoint in rest_endpoints:
        for key in ("request_schema", "response_schema"):
            value = endpoint.get(key)
            if value is not None:
                endpoint[f"{key}_pretty"] = json.dumps(value, indent=2)

    return render(
        request,
        "marketing/api_overview.html",
        {
            "rest_endpoints": rest_endpoints,
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
                {
                    "title": "Ruby Net::HTTP",
                    "code": "require 'net/http'\\nuri = URI('https://your-domain/api/marketing-assessment/cand-123/results/')\\nreq = Net::HTTP::Get.new(uri)\\nreq['X-API-Key'] = token\\nres = Net::HTTP.start(uri.hostname, uri.port, use_ssl: true) { |http| http.request(req) }",
                },
            ],
            "hero_use_cases": [
                "Trigger invites from your ATS or onboarding tools.",
                "Embed live status + scores in manager dashboards.",
                "Sync completed assignments back to HRIS or CRMs.",
            ],
            "hero_metrics": [
                {"value": "99.98%", "label": "Uptime across regions"},
                {"value": "120 ms", "label": "Median response time"},
                {"value": "180+", "label": "Active partner teams"},
            ],
            "loop_steps": [
                {"title": "Issue invite", "detail": "Call /start with candidate metadata and assessment type to receive a secure session link."},
                {"title": "Candidate completes", "detail": "Evalon hosts the UX on mobile or desktop, saves progress, and scores responses in real time."},
                {"title": "Sync outcomes", "detail": "Webhooks push scores + breakdowns back to your ATS/CRM, and you can pull the JSON results anytime."},
            ],
            "environment_details": [
                {"label": "API base URL", "value": request.build_absolute_uri('/api/')},
                {"label": "Authentication", "value": "X-API-Key header"},
                {"label": "Rate limit", "value": "600 req/min per workspace"},
                {"label": "Response format", "value": "JSON (UTF-8)"},
            ],
            "architecture_flows": [
                {
                    "title": "Create session",
                    "description": "Your system hits <code>/start</code> with candidate + assessment metadata. Evalon returns a secure link.",
                },
                {
                    "title": "Candidate completes",
                    "description": "Evalon handles UX, scoring, and telemetry. Webhooks notify your app when responses arrive.",
                },
                {
                    "title": "Pull scores",
                    "description": "Fetch score reports or export behavioral traits into interview guides or ATS notes.",
                },
            ],
            "partner_highlights": [
                {"name": "Northwind ATS", "quote": "Evalon's API shaved 4 hours per req by auto-issuing PM assessments."},
                {"name": "Atlas CRM", "quote": "We embed candidate scorecards right in our enterprise deal rooms."},
            ],
            "changelog": [
                {"date": "May 2025", "entry": "Added behavioral profile endpoint + webhook retries."},
                {"date": "Apr 2025", "entry": "Released Postman collection and OpenAPI 1.2."},
                {"date": "Mar 2025", "entry": "Launched sandbox environment + per-workspace API keys."},
            ],
            "postman_url": postman_url,
            "openapi_url": openapi_url,
            "schema_url": schema_url,
            "download_bundle": {
                "headline": "API resources",
                "description": "Request API access to receive our Postman collection, OpenAPI spec, and webhook schemas for your team.",
                "resources": [
                    {"label": "Postman collection", "description": "Pre-built requests for every endpoint.", "href": postman_url},
                    {"label": "OpenAPI spec", "description": "Full contract with parameters + responses.", "href": openapi_url},
                    {"label": "Webhook schema", "description": "JSON schema for score callbacks.", "href": schema_url},
                ],
            },
            "playground_examples": [
                {
                    "slug": "start",
                    "title": "Create marketing assessment session",
                    "method": "POST",
                    "path": "/api/marketing-assessment/start/",
                    "description": "Provision a secure invite link for your candidate.",
                    "request": {
                        "headers": {"X-API-Key": "sk_live_***", "Content-Type": "application/json"},
                        "body": {"candidate_id": "cand-123", "assessment": "marketing"},
                    },
                    "response": {
                        "status": 201,
                        "body": {"session_uuid": "7c6c8842-ff8b-4d85-9b64-1c1190cb9a1e", "expires_at": "2025-06-20T19:04:00Z"},
                    },
                },
                {
                    "slug": "results",
                    "title": "Fetch completed results",
                    "method": "GET",
                    "path": "/api/marketing-assessment/cand-123/results/",
                    "description": "Retrieve the overall score and category-level insights.",
                    "request": {
                        "headers": {"X-API-Key": "sk_live_***"},
                        "body": None,
                    },
                    "response": {
                        "status": 200,
                        "body": {
                            "overall_score": 84.2,
                            "category_breakdown": {"strategy": 86, "execution": 82, "analytics": 80},
                            "fit_recommendation": "Great fit for performance marketing lead.",
                        },
                    },
                },
                {
                    "slug": "webhook",
                    "title": "Receive webhook payload",
                    "method": "POST",
                    "path": "https://your-app.com/webhooks/evalon",
                    "description": "Example JSON body delivered when a candidate finishes.",
                    "request": {
                        "headers": {"X-Evalon-Signature": "sha256=***"},
                        "body": {
                            "event": "assessment.completed",
                            "session_uuid": "7c6c8842-ff8b-4d85-9b64-1c1190cb9a1e",
                            "candidate_id": "cand-123",
                            "overall_score": 84.2,
                            "completed_at": "2025-06-11T08:42:22Z",
                        },
                    },
                    "response": {
                        "status": 200,
                        "body": {"detail": "Webhook received"},
                    },
                },
            ],
            "form": form,
        },
    )
