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

    # Actual API endpoints matching the implementation
    rest_endpoints = [
        # Main Assessment API (Behavioral assessments)
        {
            "method": "POST",
            "path": "/api/assessments/invitations/",
            "description": "Create candidate invitation for behavioral assessment",
            "request_schema": {
                "email": "candidate@example.com",
                "full_name": "Jane Doe",
                "assessment_slug": "sales-associate-behavioral",
                "behavioral_focus": ["adaptability", "collaboration"],
                "notes": "Optional notes for the session",
                "due_at": "2025-06-30T17:00:00Z"
            },
            "response_schema": {
                "session_uuid": "7c6c8842-ff8b-4d85-9b64-1c1190cb9a1e",
                "assessment": "sales-associate-behavioral",
                "candidate": {
                    "id": 123,
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "email": "candidate@example.com"
                },
                "status": "invited",
                "behavioral_focus": ["adaptability", "collaboration"],
                "email_sent": True
            },
        },
        {
            "method": "GET",
            "path": "/api/assessments/sessions/<uuid>/responses/",
            "description": "Get session status and results",
            "request_schema": {"headers": {"X-API-Key": "your-api-key"}},
            "response_schema": {
                "session_uuid": "7c6c8842-ff8b-4d85-9b64-1c1190cb9a1e",
                "status": "submitted",
                "submitted_at": "2025-06-11T08:42:22Z",
                "overall_score": 84.2,
                "candidate": {
                    "id": 123,
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "email": "candidate@example.com"
                },
                "assessment": {
                    "id": 5,
                    "title": "Sales Associate Behavioral",
                    "category": "Sales"
                },
                "score_breakdown": {"adaptability": 86, "collaboration": 82},
                "behavioral_profile": {"dominant_traits": ["adaptability"]},
                "behavioral_focus": ["adaptability", "collaboration"]
            },
        },
        {
            "method": "POST",
            "path": "/api/assessments/sessions/<uuid>/responses/",
            "description": "Submit candidate responses and scores",
            "request_schema": {
                "responses": [
                    {"question_id": 42, "answer": "A"},
                    {"question_id": 43, "most": "B", "least": "D"}
                ],
                "overall_score": 84.2,
                "score_breakdown": {"adaptability": 86, "collaboration": 82}
            },
            "response_schema": {
                "session_uuid": "7c6c8842-ff8b-4d85-9b64-1c1190cb9a1e",
                "status": "submitted",
                "submitted_at": "2025-06-11T08:42:22Z"
            },
        },
        {
            "method": "GET",
            "path": "/api/assessments/categories/",
            "description": "List all assessment categories",
            "request_schema": None,
            "response_schema": {
                "categories": [
                    {
                        "name": "Sales",
                        "slug": "sales",
                        "summary": "Assessments for sales roles",
                        "assessments": [
                            {
                                "title": "Sales Associate Behavioral",
                                "slug": "sales-associate-behavioral",
                                "level": "entry",
                                "duration_minutes": 30,
                                "skills_focus": ["communication", "resilience"]
                            }
                        ]
                    }
                ]
            },
        },
        # Marketing Assessment API
        {
            "method": "POST",
            "path": "/api/marketing-assessment/start/",
            "description": "Start a marketing skills assessment session",
            "request_schema": {"candidate_id": "cand-123"},
            "response_schema": {"session_uuid": "7c6c8842-ff8b-4d85-9b64-1c1190cb9a1e"},
        },
        {
            "method": "GET",
            "path": "/api/marketing-assessment/<candidate_id>/questions/",
            "description": "Retrieve questions for the candidate's session",
            "request_schema": {"headers": {"X-API-Key": "your-api-key"}},
            "response_schema": {
                "session_uuid": "7c6c8842-ff8b-4d85-9b64-1c1190cb9a1e",
                "questions": [
                    {
                        "id": 42,
                        "question_text": "How would you approach a declining CTR?",
                        "question_type": "multiple_choice",
                        "difficulty_level": "intermediate",
                        "category": "analytics",
                        "options": ["A", "B", "C", "D"],
                        "scoring_weight": 1.0
                    }
                ]
            },
        },
        {
            "method": "POST",
            "path": "/api/marketing-assessment/<candidate_id>/submit/",
            "description": "Submit assessment responses",
            "request_schema": [
                {"question_id": 42, "answer": "A"},
                {"question_id": 43, "answer": "B"}
            ],
            "response_schema": {
                "detail": "Assessment submitted",
                "session_uuid": "7c6c8842-ff8b-4d85-9b64-1c1190cb9a1e"
            },
        },
        {
            "method": "GET",
            "path": "/api/marketing-assessment/<candidate_id>/results/",
            "description": "Fetch assessment scores and breakdown",
            "request_schema": {"headers": {"X-API-Key": "your-api-key"}},
            "response_schema": {
                "candidate_id": "cand-123",
                "hard_skill_score": 82.5,
                "soft_skill_score": 78.0,
                "overall_score": 80.3,
                "category_breakdown": {"strategy": 86, "analytics": 78, "execution": 82},
                "recommendations": "Strong analytical skills. Consider for senior roles."
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
                    "code": "import requests\\nrequests.post('https://your-domain/api/assessments/invitations/',\\n    json={'email': 'candidate@example.com', 'full_name': 'Jane Doe', 'assessment_slug': 'sales-behavioral'},\\n    headers={'X-API-Key': 'your-api-key'})",
                },
                {
                    "title": "Node.js fetch",
                    "code": "await fetch('/api/assessments/sessions/<uuid>/responses/', {\\n  headers: { 'X-API-Key': token }\\n}).then(r => r.json());",
                },
                {
                    "title": "cURL",
                    "code": "curl -X POST https://your-domain/api/assessments/invitations/ \\\\\\n  -H 'X-API-Key: your-api-key' \\\\\\n  -H 'Content-Type: application/json' \\\\\\n  -d '{\"email\": \"candidate@example.com\", \"full_name\": \"Jane Doe\", \"assessment_slug\": \"sales-behavioral\"}'",
                },
                {
                    "title": "Ruby Net::HTTP",
                    "code": "require 'net/http'\\nuri = URI('https://your-domain/api/assessments/sessions/<uuid>/responses/')\\nreq = Net::HTTP::Get.new(uri)\\nreq['X-API-Key'] = 'your-api-key'\\nres = Net::HTTP.start(uri.hostname, uri.port, use_ssl: true) { |http| http.request(req) }",
                },
            ],
            "hero_use_cases": [
                "Trigger invites from your ATS or onboarding tools.",
                "Embed live status + scores in manager dashboards.",
                "Sync completed assignments back to HRIS or CRMs.",
            ],
            "hero_metrics": [
                {"value": "REST", "label": "JSON API"},
                {"value": "3", "label": "Assessment types"},
                {"value": "Secure", "label": "API key auth"},
            ],
            "loop_steps": [
                {"title": "Create invitation", "detail": "POST to /api/assessments/invitations/ with candidate email and assessment slug. A secure session link is emailed to the candidate."},
                {"title": "Candidate completes", "detail": "Evalon hosts the assessment experience on mobile or desktop, auto-saves progress, and scores responses."},
                {"title": "Retrieve results", "detail": "GET /api/assessments/sessions/<uuid>/responses/ to fetch scores, behavioral profile, and candidate data."},
            ],
            "environment_details": [
                {"label": "API base URL", "value": request.build_absolute_uri('/api/')},
                {"label": "Authentication", "value": "X-API-Key header"},
                {"label": "Rate limit", "value": "600 req/min per workspace"},
                {"label": "Response format", "value": "JSON (UTF-8)"},
            ],
            "architecture_flows": [
                {
                    "title": "Create invitation",
                    "description": "POST to <code>/api/assessments/invitations/</code> with candidate email and assessment details. Candidate receives an email with their unique session link.",
                },
                {
                    "title": "Candidate completes",
                    "description": "Candidate completes the assessment through Evalon's responsive interface. Progress is saved automatically.",
                },
                {
                    "title": "Retrieve results",
                    "description": "GET <code>/api/assessments/sessions/&lt;uuid&gt;/responses/</code> to fetch overall score, category breakdown, and behavioral profile.",
                },
            ],
            "partner_highlights": [],
            "changelog": [
                {"date": "Jan 2026", "entry": "Added API key authentication to all assessment endpoints."},
                {"date": "Jan 2026", "entry": "Added deadline (due_at) support for assessment invitations."},
                {"date": "Dec 2025", "entry": "Launched behavioral focus selection for targeted assessments."},
            ],
            "postman_url": postman_url,
            "openapi_url": openapi_url,
            "schema_url": schema_url,
            "download_bundle": {
                "headline": "API resources",
                "description": "Request API access to receive your API key and documentation for your team.",
                "resources": [
                    {"label": "API key", "description": "Secure authentication token for all endpoints.", "href": None},
                    {"label": "Documentation", "description": "Full endpoint reference with examples.", "href": None},
                ],
            },
            "playground_examples": [
                {
                    "slug": "invite",
                    "title": "Create candidate invitation",
                    "method": "POST",
                    "path": "/api/assessments/invitations/",
                    "description": "Send an assessment invitation to a candidate.",
                    "request": {
                        "headers": {"X-API-Key": "your-api-key", "Content-Type": "application/json"},
                        "body": {
                            "email": "candidate@example.com",
                            "full_name": "Jane Doe",
                            "assessment_slug": "sales-associate-behavioral",
                            "behavioral_focus": ["adaptability", "collaboration"]
                        },
                    },
                    "response": {
                        "status": 201,
                        "body": {
                            "session_uuid": "7c6c8842-ff8b-4d85-9b64-1c1190cb9a1e",
                            "assessment": "sales-associate-behavioral",
                            "candidate": {"id": 123, "first_name": "Jane", "last_name": "Doe", "email": "candidate@example.com"},
                            "status": "invited",
                            "email_sent": True
                        },
                    },
                },
                {
                    "slug": "results",
                    "title": "Fetch session results",
                    "method": "GET",
                    "path": "/api/assessments/sessions/<uuid>/responses/",
                    "description": "Retrieve the session status, scores, and behavioral profile.",
                    "request": {
                        "headers": {"X-API-Key": "your-api-key"},
                        "body": None,
                    },
                    "response": {
                        "status": 200,
                        "body": {
                            "session_uuid": "7c6c8842-ff8b-4d85-9b64-1c1190cb9a1e",
                            "status": "submitted",
                            "overall_score": 84.2,
                            "score_breakdown": {"adaptability": 86, "collaboration": 82},
                            "behavioral_profile": {"dominant_traits": ["adaptability"]}
                        },
                    },
                },
                {
                    "slug": "categories",
                    "title": "List assessment categories",
                    "method": "GET",
                    "path": "/api/assessments/categories/",
                    "description": "Get all available assessment categories and their assessments.",
                    "request": {
                        "headers": {},
                        "body": None,
                    },
                    "response": {
                        "status": 200,
                        "body": {
                            "categories": [
                                {
                                    "name": "Sales",
                                    "slug": "sales",
                                    "assessments": [{"title": "Sales Associate Behavioral", "slug": "sales-associate-behavioral"}]
                                }
                            ]
                        },
                    },
                },
            ],
            "form": form,
        },
    )
