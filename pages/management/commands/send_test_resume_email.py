"""Send a test resume checker results email with sample data."""
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


SAMPLE_RESULT = {
    "ats_score": 78,
    "verdict": "Strong Match",
    "summary": "Your resume demonstrates solid digital marketing experience with strong campaign management skills. Key gaps include missing AI/ML marketing automation keywords and limited quantification of results. Adding specific metrics and aligning terminology with the JD would significantly boost your ATS score.",
    "hard_skills_analysis": {
        "matched": ["Google Ads", "Facebook Ads", "SEO", "Content Strategy", "HubSpot", "Analytics"],
        "missing_critical": ["AI Marketing", "Programmatic Advertising", "Marketing Mix Modeling"],
        "missing_nice_to_have": ["Tableau", "SQL", "A/B Testing Frameworks"],
    },
    "experience_alignment": {
        "score": 85,
        "assessment": "Candidate has 7+ years of relevant experience exceeding the 6+ requirement. Experience is strong in execution but could better highlight strategic ownership.",
        "years_detected": "7+ years",
        "years_required": "6+ years",
    },
    "keyword_matches": [
        {"keyword": "Google Ads", "found": True, "context": "Found in Skills section", "importance": "high"},
        {"keyword": "SEO", "found": True, "context": "Found in Experience section", "importance": "high"},
        {"keyword": "AI Marketing", "found": False, "context": "Add to skills or reframe automation work", "importance": "high"},
        {"keyword": "Programmatic", "found": False, "context": "Not mentioned anywhere", "importance": "medium"},
        {"keyword": "Content Strategy", "found": True, "context": "Found in job responsibilities", "importance": "medium"},
        {"keyword": "ROI Analysis", "found": False, "context": "Add metrics showing ROI impact", "importance": "high"},
    ],
    "strengths": [
        "Strong campaign management across multiple channels (Google, Meta, LinkedIn)",
        "Demonstrated leadership with team of 4 direct reports",
        "Progressive career growth from coordinator to senior manager",
        "Experience with marketing automation tools (HubSpot, Marketo)",
    ],
    "improvements": [
        {"issue": "No quantified achievements", "fix": "Add metrics like 'Increased ROAS by 45% over 6 months' or 'Managed $2.5M annual ad spend'"},
        {"issue": "Missing ATS-friendly section headers", "fix": "Use standard headers: 'Professional Experience', 'Skills', 'Education' instead of creative titles"},
        {"issue": "Skills section too brief", "fix": "Expand to include all JD keywords: AI marketing, programmatic, marketing mix modeling"},
        {"issue": "No summary/objective statement", "fix": "Add a 2-line professional summary at the top targeting this specific role"},
    ],
    "missing_sections": ["Professional Summary", "Certifications"],
    "formatting_issues": ["Two-column layout may confuse ATS parsers", "Use standard fonts (Arial, Calibri)"],
    "quantification_check": {
        "has_metrics": False,
        "examples_found": [],
        "suggestions": [
            "Add budget managed: 'Managed $X annual digital advertising budget'",
            "Add growth metrics: 'Grew organic traffic by X% over Y months'",
            "Add team size: 'Led cross-functional team of X members'",
        ],
    },
    "action_verbs_check": {
        "weak_phrases": [
            {"original": "Responsible for managing campaigns", "improved": "Orchestrated multi-channel campaigns"},
            {"original": "Helped with SEO strategy", "improved": "Spearheaded SEO strategy overhaul"},
            {"original": "Worked on content creation", "improved": "Produced high-performing content assets"},
        ],
    },
    "overall_recommendations": [
        "Add a professional summary with target role keywords (AI marketing, programmatic, growth) at the top of your resume",
        "Quantify every bullet point with specific metrics: revenue impact, budget size, team size, growth percentages",
        "Reframe marketing automation experience using AI terminology to match the JD requirements",
    ],
    "tip": "Many ATS systems score keyword density, not just presence. Mention critical keywords 2-3 times across different sections (summary, experience, skills) for maximum match rate.",
}


class Command(BaseCommand):
    help = "Send a test resume checker results email"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Recipient email address")

    def handle(self, *args, **options):
        email = options["email"]

        class FakeLead:
            full_name = "Sarvar Jafarov"

        context = {
            "lead": FakeLead(),
            "result": SAMPLE_RESULT,
            "score": SAMPLE_RESULT["ats_score"],
            "verdict": SAMPLE_RESULT["verdict"],
        }

        html_content = render_to_string("emails/resume_checker_results.html", context)
        text_content = strip_tags(html_content)

        subject = f"Your ATS Score: {SAMPLE_RESULT['ats_score']}/100 — {SAMPLE_RESULT['verdict']}"

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)

        self.stdout.write(self.style.SUCCESS(f"Test email sent to {email}"))
