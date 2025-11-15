from django.core.management.base import BaseCommand

from marketing_assessments.models import DigitalMarketingQuestion


class Command(BaseCommand):
    help = "Seed the digital marketing question bank with starter prompts."

    def handle(self, *args, **options):
        questions = SAMPLE_QUESTIONS
        created = 0
        for payload in questions:
            obj, was_created = DigitalMarketingQuestion.objects.get_or_create(
                question_text=payload["question_text"],
                defaults={k: v for k, v in payload.items() if k != "question_text"},
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} questions."))


SAMPLE_QUESTIONS = [
    {
        "question_text": "A Smart Bidding campaign suddenly sees ROAS drop 25% week over week. What is the first diagnostic you should run?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "ppc",
        "options": {
            "choices": [
                {"id": "A", "text": "Check change history for budget shifts"},
                {"id": "B", "text": "Reduce bid strategy target immediately"},
                {"id": "C", "text": "Switch attribution model"},
                {"id": "D", "text": "Pause the worst performing ad group"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
    },
    {
        "question_text": "Rank these bidding strategies from highest to lowest automation.",
        "question_type": "ranking",
        "difficulty_level": 3,
        "category": "ppc",
        "options": {"items": ["Target CPA", "Maximize Clicks", "Enhanced CPC", "Manual CPC"]},
        "correct_answer": ["Target CPA", "Maximize Clicks", "Enhanced CPC", "Manual CPC"],
        "scoring_weight": 1.0,
    },
    {
        "question_text": "Which change best improves E-E-A-T for a medical blog?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "seo",
        "options": {
            "choices": [
                {"id": "A", "text": "Adding recipe structured data"},
                {"id": "B", "text": "Listing contributor medical credentials"},
                {"id": "C", "text": "Embedding more stock photos"},
                {"id": "D", "text": "Increasing keyword density"},
            ]
        },
        "correct_answer": "B",
        "scoring_weight": 1.0,
    },
    {
        "question_text": "A crawl log shows thousands of 302 redirects to the same URL. What is the likely issue?",
        "question_type": "scenario",
        "difficulty_level": 4,
        "category": "seo",
        "options": {
            "choices": [
                {"id": "A", "text": "Broken canonical tags"},
                {"id": "B", "text": "Infinite redirect loop wasting crawl budget"},
                {"id": "C", "text": "Missing sitemap entries"},
                {"id": "D", "text": "Robots.txt blocking CSS"},
            ]
        },
        "correct_answer": "B",
        "scoring_weight": 1.2,
    },
    {
        "question_text": "In GA4, which parameter ensures cross-device funnel alignment for a logged-in experience?",
        "question_type": "multiple_choice",
        "difficulty_level": 4,
        "category": "analytics",
        "options": {
            "choices": [
                {"id": "A", "text": "session_id"},
                {"id": "B", "text": "user_id"},
                {"id": "C", "text": "campaign_id"},
                {"id": "D", "text": "utm_term"},
            ]
        },
        "correct_answer": "B",
        "scoring_weight": 1.1,
    },
    {
        "question_text": "Given TOFU evaluate MOFU drop from 8,200 sessions to 1,240 engaged views, what is the percent drop-off?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "analytics",
        "options": {
            "choices": [
                {"id": "A", "text": "84.9%"},
                {"id": "B", "text": "72.1%"},
                {"id": "C", "text": "65.4%"},
                {"id": "D", "text": "51.8%"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
    },
    {
        "question_text": "Select the headline that best matches bottom-of-funnel (BOFU) intent for a payroll SaaS.",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "content",
        "options": {
            "choices": [
                {"id": "A", "text": "10 Payroll Tips for Startups"},
                {"id": "B", "text": "Compare Top 5 Payroll Platforms"},
                {"id": "C", "text": "Why Payroll Compliance Matters"},
                {"id": "D", "text": "How to Choose a Payroll Partner in 2025"},
            ]
        },
        "correct_answer": "B",
        "scoring_weight": 1.0,
    },
    {
        "question_text": "Match the copywriting formula to the funnel stage it best supports.",
        "question_type": "ranking",
        "difficulty_level": 2,
        "category": "content",
        "options": {"items": ["AIDA", "PAS", "Before-After-Bridge", "Problem-Promise-Proof"]},
        "correct_answer": ["TOFU", "MOFU", "MOFU", "BOFU"],
        "scoring_weight": 0.8,
    },
    {
        "question_text": "A DTC brand has CAC creeping up and limited budget. Which mix is best to steady ROAS?",
        "question_type": "scenario",
        "difficulty_level": 4,
        "category": "strategy",
        "options": {
            "choices": [
                {"id": "A", "text": "Shift to 70% prospecting, 30% retargeting"},
                {"id": "B", "text": "Pause top-of-funnel to fund high intent and email"},
                {"id": "C", "text": "Add television to build awareness"},
                {"id": "D", "text": "Double creative testing budget"},
            ]
        },
        "correct_answer": "B",
        "scoring_weight": 1.2,
    },
    {
        "question_text": "Which audience metric signals creative fatigue first on short-form video campaigns?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "social",
        "options": {
            "choices": [
                {"id": "A", "text": "CTR"},
                {"id": "B", "text": "Thumb-stop rate"},
                {"id": "C", "text": "CPM"},
                {"id": "D", "text": "Reach"},
            ]
        },
        "correct_answer": "B",
        "scoring_weight": 1.0,
    },
    {
        "question_text": "Most like me: I default to data to settle creative debates.",
        "question_type": "behavioral_most",
        "difficulty_level": 1,
        "category": "behavioral",
        "options": {
            "statements": [
                "I bring teams together during tense debates.",
                "I use experiments to decide creative direction.",
                "I prioritize rapid shipping over research.",
            ]
        },
        "scoring_weight": 0.5,
    },
    {
        "question_text": "Least like me: pick the statement that aligns the least.",
        "question_type": "behavioral_least",
        "difficulty_level": 1,
        "category": "behavioral",
        "options": {
            "statements": [
                "I shy away from ambiguous briefs.",
                "I prefer feedback before publishing.",
                "I rely heavily on persona documents.",
            ]
        },
        "scoring_weight": 0.5,
    },
    {
        "question_text": "Which KPI proves a creative concept improved top-of-funnel efficiency?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "social",
        "options": {
            "choices": [
                {"id": "A", "text": "Higher CTR with stable CPM"},
                {"id": "B", "text": "Lower ROAS"},
                {"id": "C", "text": "Higher CPC but higher CVR"},
                {"id": "D", "text": "Lower frequency"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
    },
    {
        "question_text": "Select the correct UTM parameters for a TikTok remarketing campaign targeting MOFU visitors.",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "analytics",
        "options": {
            "choices": [
                {"id": "A", "text": "utm_source=tiktok&utm_medium=paid&utm_campaign=remarketing_mofu"},
                {"id": "B", "text": "utm_source=paid&utm_medium=social&utm_campaign=remarketing"},
                {"id": "C", "text": "utm_source=tiktok&utm_medium=organic&utm_campaign=remarketing"},
                {"id": "D", "text": "utm_source=remarketing&utm_medium=social&utm_campaign=tiktok"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
    },
    {
        "question_text": "Identify the missing conversion action that commonly breaks Smart Bidding.",
        "question_type": "multiple_choice",
        "difficulty_level": 4,
        "category": "ppc",
        "options": {
            "choices": [
                {"id": "A", "text": "Phone call conversion"},
                {"id": "B", "text": "Secondary micro conversion"},
                {"id": "C", "text": "Purchased order value upload"},
                {"id": "D", "text": "Add to cart event"},
            ]
        },
        "correct_answer": "C",
        "scoring_weight": 1.1,
    },
    {
        "question_text": "Which schema markup helps a local service provider rank for 'near me' searches?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "seo",
        "options": {
            "choices": [
                {"id": "A", "text": "Article schema"},
                {"id": "B", "text": "FAQ schema"},
                {"id": "C", "text": "LocalBusiness schema"},
                {"id": "D", "text": "Dataset schema"},
            ]
        },
        "correct_answer": "C",
        "scoring_weight": 1.0,
    },
    {
        "question_text": "Reorder the steps to create an AI-assisted content brief.",
        "question_type": "ranking",
        "difficulty_level": 2,
        "category": "content",
        "options": {
            "items": [
                "Define persona and intent",
                "Feed outline to AI tool",
                "Review generated brief",
                "Add SME fact-checking tasks",
            ]
        },
        "correct_answer": [
            "Define persona and intent",
            "Feed outline to AI tool",
            "Review generated brief",
            "Add SME fact-checking tasks",
        ],
        "scoring_weight": 0.9,
    },
    {
        "question_text": "Choose the best channel mix for a B2B SaaS MOFU webinar offer.",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "strategy",
        "options": {
            "choices": [
                {"id": "A", "text": "LinkedIn Sponsored Content + nurture email"},
                {"id": "B", "text": "TikTok in-feed + radio"},
                {"id": "C", "text": "Out-of-home + print ads"},
                {"id": "D", "text": "Snapchat Story ads + display"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
    },
    {
        "question_text": "Scenario: CPM up 30% but CTR flat. Best next step?",
        "question_type": "scenario",
        "difficulty_level": 3,
        "category": "social",
        "options": {
            "choices": [
                {"id": "A", "text": "Expand lookalike size"},
                {"id": "B", "text": "Refresh creative hook & thumb-stop"},
                {"id": "C", "text": "Lower budget 30%"},
                {"id": "D", "text": "Duplicate campaign with higher bid"},
            ]
        },
        "correct_answer": "B",
        "scoring_weight": 1.0,
    },
    {
        "question_text": "Define a custom GA4 conversion using event data: select the correct configuration.",
        "question_type": "multiple_choice",
        "difficulty_level": 4,
        "category": "analytics",
        "options": {
            "choices": [
                {"id": "A", "text": "Mark any event with event_name='purchase'"},
                {"id": "B", "text": "Create new event where event_name='submit_lead' and mark as conversion"},
                {"id": "C", "text": "Toggle enhanced measurement conversions"},
                {"id": "D", "text": "Only rely on data-driven attribution"},
            ]
        },
        "correct_answer": "B",
        "scoring_weight": 1.1,
    },
    {
        "question_text": "Calculate target CPA if LTV is $900 with 40% gross margin and you need 4x payback.",
        "question_type": "multiple_choice",
        "difficulty_level": 4,
        "category": "ppc",
        "options": {
            "choices": [
                {"id": "A", "text": "$225"},
                {"id": "B", "text": "$90"},
                {"id": "C", "text": "$360"},
                {"id": "D", "text": "$600"},
            ]
        },
        "correct_answer": "B",
        "scoring_weight": 1.3,
    },
    {
        "question_text": "Choose a canonical approach for a multi-region site with similar content.",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "seo",
        "options": {
            "choices": [
                {"id": "A", "text": "Self-referencing canonicals + hreflang"},
                {"id": "B", "text": "All pages canonical to US version"},
                {"id": "C", "text": "No canonical tags"},
                {"id": "D", "text": "Canonical to sitemap"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.1,
    },
    {
        "question_text": "Behavioral: I invite feedback even when timelines are tight.",
        "question_type": "behavioral_most",
        "difficulty_level": 1,
        "category": "behavioral",
        "options": {
            "statements": [
                "I prefer to ship without critique.",
                "I proactively seek feedback before launch.",
                "I only review performance post-campaign.",
            ]
        },
        "scoring_weight": 0.5,
    },
    {
        "question_text": "Choose the KPI that indicates creative concept improved top-of-funnel awareness without hurting efficiency.",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "social",
        "options": {
            "choices": [
                {"id": "A", "text": "Higher thumb-stop rate with stable CPM"},
                {"id": "B", "text": "Higher frequency"},
                {"id": "C", "text": "Lower CTR"},
                {"id": "D", "text": "Higher CPC"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
    },
    {
        "question_text": "Order these funnel experiments from validation to scale.",
        "question_type": "ranking",
        "difficulty_level": 3,
        "category": "strategy",
        "options": {"items": ["A/B test CTA", "Expand placement mix", "Add referral program", "Launch gated asset"]},
        "correct_answer": ["A/B test CTA", "Launch gated asset", "Add referral program", "Expand placement mix"],
        "scoring_weight": 1.1,
    },
    {
        "question_text": "Interpret attribution differences: data-driven shows 40% credit to paid social, time-decay shows 15%. What is the action?",
        "question_type": "scenario",
        "difficulty_level": 4,
        "category": "analytics",
        "options": {
            "choices": [
                {"id": "A", "text": "Trust the smaller number and cut spend"},
                {"id": "B", "text": "Investigate upper funnel influence and adjust budgets cautiously"},
                {"id": "C", "text": "Ignore attribution models entirely"},
                {"id": "D", "text": "Switch to first-click attribution"},
            ]
        },
        "correct_answer": "B",
        "scoring_weight": 1.2,
    },
    {
        "question_text": "Identify automation bias risk within Performance Max campaigns.",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "ppc",
        "options": {
            "choices": [
                {"id": "A", "text": "Over-prioritizing branded traffic"},
                {"id": "B", "text": "Serving only on YouTube"},
                {"id": "C", "text": "Increasing manual CPC bids"},
                {"id": "D", "text": "Limiting assets"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.1,
    },
    {
        "question_text": "Diagnose a ranking drop after migrating to a JS framework.",
        "question_type": "scenario",
        "difficulty_level": 4,
        "category": "seo",
        "options": {
            "choices": [
                {"id": "A", "text": "Robots.txt blocked JS"},
                {"id": "B", "text": "Server not serving critical content to Googlebot"},
                {"id": "C", "text": "No sitemap"},
                {"id": "D", "text": "Too many internal links"},
            ]
        },
        "correct_answer": "B",
        "scoring_weight": 1.2,
    },
    {
        "question_text": "Pick the copy variation aligned with persona pain point: 'Ops manager drowning in manual spreadsheets'.",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "content",
        "options": {
            "choices": [
                {"id": "A", "text": "Grow revenue in weeks"},
                {"id": "B", "text": "Replace 12 spreadsheets with one source of truth"},
                {"id": "C", "text": "Our UI is modern"},
                {"id": "D", "text": "We offer unlimited seats"},
            ]
        },
        "correct_answer": "B",
        "scoring_weight": 1.0,
    },
    {
        "question_text": "Least-like-you scenario: handling ambiguous briefs.",
        "question_type": "behavioral_least",
        "difficulty_level": 1,
        "category": "behavioral",
        "options": {
            "statements": [
                "I ask clarifying questions immediately.",
                "I start drafting concepts and iterate later.",
                "I wait for stakeholders to send more info.",
            ]
        },
        "scoring_weight": 0.5,
    },
    {
        "question_text": "Scenario-based ranking of competitor insights by influence on strategy.",
        "question_type": "ranking",
        "difficulty_level": 3,
        "category": "strategy",
        "options": {"items": ["Competitor launching new freemium tier", "Competitor halving CPC bids", "Competitor expanding to offline media"]},
        "correct_answer": [
            "Competitor halving CPC bids",
            "Competitor launching new freemium tier",
            "Competitor expanding to offline media",
        ],
        "scoring_weight": 1.0,
    },
    {
        "question_text": "Select the GA4 audience useful for retargeting MOFU visitors who viewed pricing but not demo.",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "analytics",
        "options": {
            "choices": [
                {"id": "A", "text": "event_name='page_view' where page_location contains '/pricing' and not event='demo_booked'"},
                {"id": "B", "text": "All users"},
                {"id": "C", "text": "Traffic from organic only"},
                {"id": "D", "text": "Users who triggered purchase"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.1,
    },
]
