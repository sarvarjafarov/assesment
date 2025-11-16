from django.db import migrations
from django.utils import timezone


def seed_posts(apps, schema_editor):
    BlogPost = apps.get_model("blog", "BlogPost")
    posts = [
        {
            "title": "How People Teams Operationalize Behavioral Insights",
            "slug": "operationalize-behavioral-insights",
            "hero_image": "https://images.unsplash.com/photo-1517242022404-795a8eae617c?auto=format&fit=crop&w=1200&q=80",
            "pill_label": "Talent Ops",
            "pill_style": "accent",
            "excerpt": "Turn candidate behavioral data into concrete enablement for recruiters, interviewers, and hiring managers.",
            "body": (
                "### Build deliberate handoffs\n"
                "Behavioral assessments produce a goldmine of signal. Give hiring teams a template that summarizes strengths, "
                "development areas, and suggested interview focus areas. When recruiters drop this into the hiring packet, "
                "panelists know exactly how to pressure-test fit.\n\n"
                "### Close the loop with candidates\n"
                "Use Sira's behavioral profile to craft feedback snippets. Candidates appreciate specific examples of what "
                "went well and how they can keep improving."
            ),
            "author_name": "Maya Thompson",
            "author_title": "VP People, Sira",
            "status": "published",
            "published_at": timezone.now(),
        },
        {
            "title": "Scaling Marketing Assessments for Hybrid Growth Teams",
            "slug": "scaling-marketing-assessments",
            "hero_image": "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1200&q=80",
            "pill_label": "Digital Marketing",
            "pill_style": "neutral",
            "excerpt": "What top brands learned after rolling out Sira's digital marketing module across paid, lifecycle, and analytics squads.",
            "body": (
                "### Checklist for marketing leaders\n"
                "1. Align on scoring weights per role—performance marketing, SEO, or analytics require different emphasis.\n"
                "2. Pair time-boxed scenarios with behavioral prompts so you cover both execution and collaboration skills.\n"
                "3. Pipe results into your ATS to track which question types predict on-the-job success.\n\n"
                "### Bonus: candidate experience\n"
                "The sequential flow keeps marketers focused. They see only one question at a time and know exactly how much "
                "time is left thanks to built-in timers."
            ),
            "author_name": "Ibrahim Solak",
            "author_title": "Head of Growth, Sira",
            "status": "published",
            "published_at": timezone.now(),
        },
        {
            "title": "Your API Handbook for Integrating Sira Assessments",
            "slug": "api-handbook",
            "hero_image": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
            "pill_label": "Platform",
            "pill_style": "success",
            "excerpt": "We walk through authentication, sample payloads, and how to sync Sira with ATS or internal workflow tools.",
            "body": (
                "### Why teams integrate via API\n"
                "Automation means recruiters never leave their system of record. Start sessions, retrieve questions, and pull "
                "scorecards programmatically.\n\n"
                "### Quick start\n"
                "* Generate an API key in the console.\n"
                "* Call `/api/marketing-assessment/start/` with the candidate identifier.\n"
                "* Store `session_uuid` to submit responses and fetch the final profile.\n\n"
                "Need help? The platform team can share Postman collections and webhooks for completed assessments."
            ),
            "author_name": "Lena Ortiz",
            "author_title": "Director of Platform, Sira",
            "status": "published",
            "published_at": timezone.now(),
        },
    ]
    for payload in posts:
        BlogPost.objects.update_or_create(
            slug=payload["slug"],
            defaults=payload,
        )


def remove_posts(apps, schema_editor):
    BlogPost = apps.get_model("blog", "BlogPost")
    BlogPost.objects.filter(
        slug__in=[
            "operationalize-behavioral-insights",
            "scaling-marketing-assessments",
            "api-handbook",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_posts, remove_posts),
    ]
