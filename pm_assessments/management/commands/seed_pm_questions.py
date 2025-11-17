from django.core.management.base import BaseCommand

from pm_assessments.models import ProductQuestion


class Command(BaseCommand):
    help = "Seed the product management assessment with starter questions."

    def handle(self, *args, **options):
        created = 0
        for payload in SAMPLE_QUESTIONS:
            question, was_created = ProductQuestion.objects.get_or_create(
                question_text=payload["question_text"],
                defaults={k: v for k, v in payload.items() if k != "question_text"},
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} product questions."))


SAMPLE_QUESTIONS = [
    {
        "question_text": "Which artifact best communicates a new product strategy to executives?",
        "question_type": ProductQuestion.TYPE_MULTIPLE,
        "difficulty_level": 3,
        "category": ProductQuestion.CATEGORY_STRATEGY,
        "options": {
            "choices": [
                {"id": "A", "text": "Release notes with bug fixes"},
                {"id": "B", "text": "North star metric narrative"},
                {"id": "C", "text": "Sprint burndown"},
                {"id": "D", "text": "User story map"},
            ]
        },
        "correct_answer": "B",
    },
    {
        "question_text": "Rank these roadmap techniques from most qualitative to most quantitative.",
        "question_type": ProductQuestion.TYPE_RANKING,
        "difficulty_level": 2,
        "category": ProductQuestion.CATEGORY_ROADMAP,
        "options": {
            "items": [
                "Opportunity solution tree",
                "Now/Next/Later board",
                "RICE scoring",
                "Weighted shortest job first",
            ]
        },
        "correct_answer": [
            "Opportunity solution tree",
            "Now/Next/Later board",
            "RICE scoring",
            "Weighted shortest job first",
        ],
    },
    {
        "question_text": "A discovery sprint revealed conflicting insights from sales and analytics. What should you do first?",
        "question_type": ProductQuestion.TYPE_SCENARIO,
        "difficulty_level": 3,
        "category": ProductQuestion.CATEGORY_DISCOVERY,
        "options": {
            "choices": [
                {"id": "A", "text": "Ignore sales feedback and ship"},
                {"id": "B", "text": "Run follow-up interviews to reconcile signals"},
                {"id": "C", "text": "Freeze the roadmap"},
                {"id": "D", "text": "Escalate to finance"},
            ]
        },
        "correct_answer": "B",
    },
    {
        "question_text": "Which metric confirms a pricing experiment moved the activation funnel?",
        "question_type": ProductQuestion.TYPE_MULTIPLE,
        "difficulty_level": 4,
        "category": ProductQuestion.CATEGORY_ANALYTICS,
        "options": {
            "choices": [
                {"id": "A", "text": "Net promoter score"},
                {"id": "B", "text": "Trial-to-paid conversion"},
                {"id": "C", "text": "Page load time"},
                {"id": "D", "text": "Monthly active users"},
            ]
        },
        "correct_answer": "B",
    },
    {
        "question_text": "A squad keeps slipping releases despite stable velocity. What is your next move as PM?",
        "question_type": ProductQuestion.TYPE_SCENARIO,
        "difficulty_level": 3,
        "category": ProductQuestion.CATEGORY_DELIVERY,
        "options": {
            "choices": [
                {"id": "A", "text": "Cut scope without stakeholder input"},
                {"id": "B", "text": "Run a delivery retrospective to uncover blockers"},
                {"id": "C", "text": "Replace the tech lead"},
                {"id": "D", "text": "Add more scrum ceremonies"},
            ]
        },
        "correct_answer": "B",
    },
    {
        "question_text": "Which tactic best reduces stakeholder thrash during quarterly planning?",
        "question_type": ProductQuestion.TYPE_MULTIPLE,
        "difficulty_level": 2,
        "category": ProductQuestion.CATEGORY_STAKEHOLDER,
        "options": {
            "choices": [
                {"id": "A", "text": "Exclusive 1:1 meetings only"},
                {"id": "B", "text": "Single brief summarizing bets, success metrics, and tradeoffs"},
                {"id": "C", "text": "Ship roadmap without review"},
                {"id": "D", "text": "Let engineering run planning"},
            ]
        },
        "correct_answer": "B",
    },
    {
        "question_text": "Reason through how you would justify delaying a GA launch when beta metrics miss the retention target by 8%.",
        "question_type": ProductQuestion.TYPE_REASONING,
        "difficulty_level": 4,
        "category": ProductQuestion.CATEGORY_DELIVERY,
        "options": {},
    },
    {
        "question_text": "Most like me: I bring qualitative feedback into the roadmap before exec asks for it.",
        "question_type": ProductQuestion.TYPE_BEHAVIORAL_MOST,
        "difficulty_level": 1,
        "category": ProductQuestion.CATEGORY_BEHAVIORAL,
        "options": {
            "statements": [
                "I wait for data scientists to summarize customer calls.",
                "I translate research takeaways into quarterly themes early.",
                "I prefer keeping discovery separate from planning.",
            ]
        },
        "scoring_weight": 0.5,
    },
    {
        "question_text": "Least like me: choose the option that does not match your style.",
        "question_type": ProductQuestion.TYPE_BEHAVIORAL_LEAST,
        "difficulty_level": 1,
        "category": ProductQuestion.CATEGORY_BEHAVIORAL,
        "options": {
            "statements": [
                "I champion transparency with partners even when priorities shift.",
                "I avoid sharing blockers until after we fix them.",
                "I close the loop with customers after every launch.",
            ]
        },
        "scoring_weight": 0.5,
    },
]
