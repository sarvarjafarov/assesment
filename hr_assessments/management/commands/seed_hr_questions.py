from django.core.management.base import BaseCommand

from hr_assessments.models import HRQuestion


class Command(BaseCommand):
    help = "Seed the HR question bank with starter prompts."

    def handle(self, *args, **options):
        created = 0
        for payload in SAMPLE_QUESTIONS:
            obj, was_created = HRQuestion.objects.get_or_create(
                question_text=payload["question_text"],
                defaults={k: v for k, v in payload.items() if k != "question_text"},
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} questions."))


SAMPLE_QUESTIONS = [
    # ── Talent Acquisition & Recruitment (7 questions) ────────────────────
    {
        "question_text": "What is the primary purpose of a structured interview?",
        "question_type": "multiple_choice",
        "difficulty_level": 1,
        "category": "talent_acquisition",
        "options": {
            "choices": [
                {"id": "A", "text": "Ensure consistency in candidate evaluation"},
                {"id": "B", "text": "Speed up the hiring process"},
                {"id": "C", "text": "Impress candidates with professionalism"},
                {"id": "D", "text": "Satisfy a legal requirement"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Structured interviews use standardized questions and scoring rubrics to ensure every candidate is evaluated consistently, reducing bias.",
    },
    {
        "question_text": "Which sourcing channel typically yields the highest quality-of-hire for senior roles?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "talent_acquisition",
        "options": {
            "choices": [
                {"id": "A", "text": "Employee referrals"},
                {"id": "B", "text": "Job boards"},
                {"id": "C", "text": "Social media ads"},
                {"id": "D", "text": "Campus recruiting"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Research consistently shows employee referrals produce higher quality-of-hire, faster time-to-fill, and better retention for senior positions.",
    },
    {
        "question_text": "You have 3 open engineering roles and your offer-acceptance rate has dropped to 40%. What's your first step?",
        "question_type": "scenario",
        "difficulty_level": 3,
        "category": "talent_acquisition",
        "options": {
            "choices": [
                {"id": "A", "text": "Analyze candidate feedback and decline reasons to identify root cause"},
                {"id": "B", "text": "Immediately increase salary offers across the board"},
                {"id": "C", "text": "Speed up the interview process to reduce drop-off"},
                {"id": "D", "text": "Switch to a different recruiting agency"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Diagnosing the root cause through data analysis prevents wasting resources on the wrong fix. Offers may be rejected due to culture, timing, or competing offers—not just compensation.",
    },
    {
        "question_text": "When calculating cost-per-hire, which costs should be included?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "talent_acquisition",
        "options": {
            "choices": [
                {"id": "A", "text": "Agency fees, recruiter salary, tools, travel, and job advertising"},
                {"id": "B", "text": "Only agency fees"},
                {"id": "C", "text": "Only job board spend"},
                {"id": "D", "text": "Only recruiter salary allocation"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "SHRM defines cost-per-hire as the sum of all internal and external recruiting costs divided by total hires in that period.",
    },
    {
        "question_text": "Rank these employer branding initiatives by long-term impact.",
        "question_type": "ranking",
        "difficulty_level": 4,
        "category": "talent_acquisition",
        "options": {
            "items": ["Employee advocacy program", "Careers page redesign", "Glassdoor management", "University partnerships"]
        },
        "correct_answer": ["Employee advocacy program", "University partnerships", "Careers page redesign", "Glassdoor management"],
        "scoring_weight": 1.2,
        "explanation": "Employee advocacy creates authentic, scalable brand ambassadors; university partnerships build long-term pipelines; careers page controls first impressions; Glassdoor management is reactive.",
    },
    {
        "question_text": "A hiring manager insists on hiring only from top-10 universities. Explain how you'd address this while maintaining the relationship and improving diversity.",
        "question_type": "reasoning",
        "difficulty_level": 4,
        "category": "talent_acquisition",
        "options": {},
        "correct_answer": None,
        "scoring_weight": 1.4,
        "explanation": "Look for: presenting data on performance vs. school prestige, proposing skills-based assessments, gradually expanding the school list, sharing diversity hiring metrics and business case.",
    },
    {
        "question_text": "When building a predictive quality-of-hire model, which combination of data points is most predictive?",
        "question_type": "multiple_choice",
        "difficulty_level": 5,
        "category": "talent_acquisition",
        "options": {
            "choices": [
                {"id": "A", "text": "Structured interview scores + job performance ratings + retention data"},
                {"id": "B", "text": "Resume keywords + years of experience"},
                {"id": "C", "text": "University ranking + GPA"},
                {"id": "D", "text": "Number of interviews + time-to-hire"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Predictive models require outcome data (performance, retention) linked to input signals (interview scores). Resume keywords and pedigree have weak predictive validity.",
    },

    # ── Employee Relations & Engagement (6 questions) ─────────────────────
    {
        "question_text": "What is the primary goal of an employee engagement survey?",
        "question_type": "multiple_choice",
        "difficulty_level": 1,
        "category": "employee_relations",
        "options": {
            "choices": [
                {"id": "A", "text": "Identify areas for workplace improvement"},
                {"id": "B", "text": "Check regulatory compliance"},
                {"id": "C", "text": "Generate reports for the board"},
                {"id": "D", "text": "Keep employees busy with forms"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Engagement surveys surface employee sentiment to guide actionable improvements in culture, management, and processes.",
    },
    {
        "question_text": "An employee files a harassment complaint. What is the correct first step?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "employee_relations",
        "options": {
            "choices": [
                {"id": "A", "text": "Document the complaint and begin a formal investigation"},
                {"id": "B", "text": "Confront the accused immediately"},
                {"id": "C", "text": "Inform the whole team for transparency"},
                {"id": "D", "text": "Wait for more evidence before acting"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Proper documentation and prompt investigation protect both the complainant and the organization. Delaying or broadcasting the complaint creates liability.",
    },
    {
        "question_text": "Employee engagement scores dropped 15 points in the engineering team after a reorg. You have limited budget. What's your approach?",
        "question_type": "scenario",
        "difficulty_level": 3,
        "category": "employee_relations",
        "options": {
            "choices": [
                {"id": "A", "text": "Conduct stay interviews to understand specific concerns, then create a targeted action plan with engineering leadership"},
                {"id": "B", "text": "Launch a company-wide engagement initiative"},
                {"id": "C", "text": "Offer spot bonuses to the engineering team"},
                {"id": "D", "text": "Wait for the next quarterly survey to see if scores recover"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Stay interviews provide qualitative depth to survey data and cost nothing. Targeted action plans address the specific team's issues rather than broad initiatives.",
    },
    {
        "question_text": "Which retention strategy has the strongest research-backed impact on reducing voluntary turnover?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "employee_relations",
        "options": {
            "choices": [
                {"id": "A", "text": "Career development opportunities and growth paths"},
                {"id": "B", "text": "Across-the-board salary increases"},
                {"id": "C", "text": "Flexible work arrangements alone"},
                {"id": "D", "text": "Team-building events and perks"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Gallup and SHRM research consistently identifies career development as the #1 driver of retention. Compensation matters but is not the primary factor in voluntary turnover.",
    },
    {
        "question_text": "Two high-performing employees have an ongoing conflict that's affecting team morale. Describe your step-by-step mediation approach.",
        "question_type": "reasoning",
        "difficulty_level": 4,
        "category": "employee_relations",
        "options": {},
        "correct_answer": None,
        "scoring_weight": 1.4,
        "explanation": "Look for: individual conversations first, identifying root cause, structured mediation meeting, agreement documentation, follow-up check-ins, escalation path if unresolved.",
    },
    {
        "question_text": "When handling a sensitive employee situation, you tend to...",
        "question_type": "behavioral_most",
        "difficulty_level": 2,
        "category": "employee_relations",
        "options": {
            "statements": [
                "Maintain strict confidentiality and follow protocol",
                "Discuss with trusted colleagues for advice",
                "Prioritize speed over thoroughness",
                "Defer to manager's judgment entirely",
            ]
        },
        "correct_answer": None,
        "scoring_weight": 0.8,
    },

    # ── Compensation & Benefits (5 questions) ─────────────────────────────
    {
        "question_text": "What does 'total rewards' include beyond base salary?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "compensation_benefits",
        "options": {
            "choices": [
                {"id": "A", "text": "Bonuses, benefits, equity, perks, and development opportunities"},
                {"id": "B", "text": "Only performance bonuses"},
                {"id": "C", "text": "Only health insurance"},
                {"id": "D", "text": "Only stock options"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Total rewards encompasses all forms of compensation: base pay, variable pay, benefits, equity, perks, recognition, and career development.",
    },
    {
        "question_text": "You discover a 12% gender pay gap in the engineering department. What's the most appropriate first action?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "compensation_benefits",
        "options": {
            "choices": [
                {"id": "A", "text": "Conduct a detailed pay equity audit controlling for role, experience, and performance"},
                {"id": "B", "text": "Immediately raise all women's salaries by 12%"},
                {"id": "C", "text": "Ignore it if market rates differ"},
                {"id": "D", "text": "Report to legal without further analysis"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "A raw pay gap may be explained by legitimate factors. A controlled analysis determines the adjusted gap and identifies specific inequities to remediate.",
    },
    {
        "question_text": "A top performer demands a 30% raise threatening to leave. Market data shows they're at the 75th percentile. How do you handle this?",
        "question_type": "scenario",
        "difficulty_level": 3,
        "category": "compensation_benefits",
        "options": {
            "choices": [
                {"id": "A", "text": "Acknowledge their value, share market data transparently, explore total rewards enhancements beyond base pay"},
                {"id": "B", "text": "Grant the full 30% raise immediately"},
                {"id": "C", "text": "Deny the request and call their bluff"},
                {"id": "D", "text": "Start recruiting their replacement"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Transparent data sharing builds trust. Exploring total rewards (equity, title, development, flexibility) can address needs without setting unsustainable precedents.",
    },
    {
        "question_text": "Rank these factors by importance when designing a compensation structure.",
        "question_type": "ranking",
        "difficulty_level": 4,
        "category": "compensation_benefits",
        "options": {
            "items": ["Internal equity", "External competitiveness", "Pay transparency", "Budget constraints"]
        },
        "correct_answer": ["Internal equity", "External competitiveness", "Pay transparency", "Budget constraints"],
        "scoring_weight": 1.2,
        "explanation": "Internal equity prevents discrimination and retention issues; external competitiveness attracts talent; transparency builds trust; budget is a constraint, not a design principle.",
    },
    {
        "question_text": "When implementing pay transparency legislation compliance, which approach minimizes legal risk while maintaining flexibility?",
        "question_type": "multiple_choice",
        "difficulty_level": 5,
        "category": "compensation_benefits",
        "options": {
            "choices": [
                {"id": "A", "text": "Published salary bands with clear methodology and regular market updates"},
                {"id": "B", "text": "Exact salary disclosure for every role"},
                {"id": "C", "text": "No changes until enforcement begins"},
                {"id": "D", "text": "Internal-only ranges shared upon request"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Published bands with methodology demonstrate good faith compliance. Regular updates maintain competitiveness. This approach exceeds minimum requirements proactively.",
    },

    # ── Learning & Development (6 questions) ──────────────────────────────
    {
        "question_text": "What is the '70-20-10' model in learning and development?",
        "question_type": "multiple_choice",
        "difficulty_level": 1,
        "category": "learning_development",
        "options": {
            "choices": [
                {"id": "A", "text": "70% on-the-job learning, 20% social learning, 10% formal training"},
                {"id": "B", "text": "70% classroom, 20% online, 10% mentoring"},
                {"id": "C", "text": "70% self-study, 20% workshops, 10% coaching"},
                {"id": "D", "text": "70% budget for tools, 20% for content, 10% for facilitators"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "The 70-20-10 framework suggests most learning happens through experience (70%), with social learning (20%) and formal education (10%) as supplements.",
    },
    {
        "question_text": "Which metric best evaluates training effectiveness beyond attendance?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "learning_development",
        "options": {
            "choices": [
                {"id": "A", "text": "Behavior change and business impact (Kirkpatrick Levels 3-4)"},
                {"id": "B", "text": "Completion rate"},
                {"id": "C", "text": "Satisfaction scores"},
                {"id": "D", "text": "Hours spent in training"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Kirkpatrick Levels 3 (behavior change) and 4 (business results) measure actual learning transfer and organizational impact, not just participation or satisfaction.",
    },
    {
        "question_text": "Leadership identifies a skills gap: 60% of managers lack coaching skills. Budget allows for one initiative. What do you recommend?",
        "question_type": "scenario",
        "difficulty_level": 3,
        "category": "learning_development",
        "options": {
            "choices": [
                {"id": "A", "text": "Cohort-based coaching skills program with peer practice, real-world application, and accountability partners"},
                {"id": "B", "text": "Purchase an off-the-shelf e-learning course on coaching"},
                {"id": "C", "text": "Hire external coaches for every manager"},
                {"id": "D", "text": "Send a company-wide email with coaching tips"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Cohort-based programs combine social learning, practice, and accountability—aligned with the 70-20-10 model—delivering better behavior change than passive content.",
    },
    {
        "question_text": "When designing a succession plan for C-suite roles, which approach is most comprehensive?",
        "question_type": "multiple_choice",
        "difficulty_level": 4,
        "category": "learning_development",
        "options": {
            "choices": [
                {"id": "A", "text": "9-box grid assessment + individualized development plans + external benchmarking"},
                {"id": "B", "text": "Simply promoting the most senior person"},
                {"id": "C", "text": "Annual performance reviews only"},
                {"id": "D", "text": "External hiring pipeline only"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Comprehensive succession planning combines potential assessment (9-box), targeted development, and external market awareness to build a robust leadership pipeline.",
    },
    {
        "question_text": "Rank these performance management approaches by employee development impact.",
        "question_type": "ranking",
        "difficulty_level": 4,
        "category": "learning_development",
        "options": {
            "items": ["Continuous feedback", "360-degree reviews", "OKR-based tracking", "Annual reviews"]
        },
        "correct_answer": ["Continuous feedback", "360-degree reviews", "OKR-based tracking", "Annual reviews"],
        "scoring_weight": 1.2,
        "explanation": "Continuous feedback enables real-time course correction; 360 reviews provide multi-perspective insights; OKRs align goals; annual reviews are too infrequent for development.",
    },
    {
        "question_text": "Describe how you'd build a company-wide leadership development program from scratch for a 500-person company with no existing L&D infrastructure.",
        "question_type": "reasoning",
        "difficulty_level": 5,
        "category": "learning_development",
        "options": {},
        "correct_answer": None,
        "scoring_weight": 1.4,
        "explanation": "Look for: needs assessment, leadership competency framework, tiered programs (emerging/mid/senior leaders), blended learning approach, mentoring, measurement plan, executive sponsorship.",
    },

    # ── HR Operations & Compliance (5 questions) ─────────────────────────
    {
        "question_text": "What does HRIS stand for?",
        "question_type": "multiple_choice",
        "difficulty_level": 1,
        "category": "hr_operations",
        "options": {
            "choices": [
                {"id": "A", "text": "Human Resource Information System"},
                {"id": "B", "text": "Human Resource Internal Standard"},
                {"id": "C", "text": "Hiring Resource Integration Software"},
                {"id": "D", "text": "Human Relations Improvement Strategy"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "HRIS (Human Resource Information System) is the technology backbone for managing employee data, payroll, benefits, and HR workflows.",
    },
    {
        "question_text": "Which document must be completed within 3 business days of an employee's start date in the US?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "hr_operations",
        "options": {
            "choices": [
                {"id": "A", "text": "Form I-9 (Employment Eligibility Verification)"},
                {"id": "B", "text": "W-4 (Tax Withholding)"},
                {"id": "C", "text": "NDA (Non-Disclosure Agreement)"},
                {"id": "D", "text": "Benefits enrollment form"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Federal law requires Form I-9 completion within 3 business days of hire. Section 1 must be completed on or before the first day of employment.",
    },
    {
        "question_text": "An employee requests their complete personnel file. Under most state laws, how should HR respond?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "hr_operations",
        "options": {
            "choices": [
                {"id": "A", "text": "Provide access within the legally required timeframe"},
                {"id": "B", "text": "Deny the request citing confidentiality"},
                {"id": "C", "text": "Require manager approval first"},
                {"id": "D", "text": "Charge a substantial administrative fee"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Most states grant employees the right to inspect their personnel files. HR must comply within specified timeframes, typically 7-30 days depending on jurisdiction.",
    },
    {
        "question_text": "During a routine audit, you discover that 20% of employee records are missing required documentation. What's your remediation plan?",
        "question_type": "scenario",
        "difficulty_level": 4,
        "category": "hr_operations",
        "options": {
            "choices": [
                {"id": "A", "text": "Prioritize by risk level, create a tracking spreadsheet, notify affected employees, set deadlines, and implement preventive controls"},
                {"id": "B", "text": "Backdate the missing documents"},
                {"id": "C", "text": "Fire the HR staff who failed to collect them"},
                {"id": "D", "text": "Wait until the next external audit to address it"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Systematic remediation with risk prioritization addresses the most critical gaps first while implementing controls to prevent recurrence.",
    },
    {
        "question_text": "Your company is expanding to 3 new countries. Describe how you'd establish compliant HR operations including entity setup, local labor law compliance, and payroll.",
        "question_type": "reasoning",
        "difficulty_level": 5,
        "category": "hr_operations",
        "options": {},
        "correct_answer": None,
        "scoring_weight": 1.4,
        "explanation": "Look for: EOR vs. entity setup analysis, local employment law research, payroll provider selection, benefits benchmarking, employment contract templates, data privacy compliance (GDPR etc.).",
    },

    # ── Strategic HR / People Strategy (6 questions) ──────────────────────
    {
        "question_text": "What is the primary purpose of workforce planning?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "people_strategy",
        "options": {
            "choices": [
                {"id": "A", "text": "Align talent strategy with business goals"},
                {"id": "B", "text": "Reduce headcount"},
                {"id": "C", "text": "Create organizational charts"},
                {"id": "D", "text": "Track employee attendance"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Workforce planning ensures the organization has the right people, skills, and capacity to execute its business strategy now and in the future.",
    },
    {
        "question_text": "Which framework is most effective for managing organizational change?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "people_strategy",
        "options": {
            "choices": [
                {"id": "A", "text": "Kotter's 8-step change model"},
                {"id": "B", "text": "Just announce and implement immediately"},
                {"id": "C", "text": "Hire external consultants to handle everything"},
                {"id": "D", "text": "Let change happen organically without structure"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Kotter's model provides a proven structure: create urgency, build coalition, form vision, enlist volunteers, enable action, generate wins, sustain acceleration, institute change.",
    },
    {
        "question_text": "The CEO wants to reduce headcount by 15% while maintaining productivity. How do you approach this as the HR lead?",
        "question_type": "scenario",
        "difficulty_level": 3,
        "category": "people_strategy",
        "options": {
            "choices": [
                {"id": "A", "text": "Analyze workforce data to identify redundancies, present alternatives (attrition, restructuring), and create a legally compliant reduction plan with communication strategy"},
                {"id": "B", "text": "Cut the bottom 15% performers immediately"},
                {"id": "C", "text": "Implement a hiring freeze and hope attrition handles it"},
                {"id": "D", "text": "Push back and refuse to participate in layoffs"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Data-driven analysis with multiple scenarios, legal compliance, and a communication plan protects the organization while demonstrating HR's strategic value.",
    },
    {
        "question_text": "When measuring DE&I program effectiveness, which metrics provide the most actionable insights?",
        "question_type": "multiple_choice",
        "difficulty_level": 4,
        "category": "people_strategy",
        "options": {
            "choices": [
                {"id": "A", "text": "Representation data + belonging scores + promotion equity + retention by demographic"},
                {"id": "B", "text": "Headcount diversity only"},
                {"id": "C", "text": "Training attendance numbers"},
                {"id": "D", "text": "Employee survey scores alone"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Effective DE&I measurement combines representation (who's here), inclusion (belonging), equity (promotion/pay), and retention (who stays) for a complete picture.",
    },
    {
        "question_text": "Rank these organizational design factors by impact on company performance.",
        "question_type": "ranking",
        "difficulty_level": 4,
        "category": "people_strategy",
        "options": {
            "items": ["Role clarity", "Decision-making authority", "Cross-functional collaboration", "Span of control"]
        },
        "correct_answer": ["Role clarity", "Decision-making authority", "Cross-functional collaboration", "Span of control"],
        "scoring_weight": 1.2,
        "explanation": "Role clarity eliminates duplication and confusion; decision authority enables speed; cross-functional collaboration drives innovation; span of control affects management efficiency.",
    },
    {
        "question_text": "Describe your approach to designing a hybrid work policy for a 2000-person company where engineering wants full remote, sales wants in-office, and leadership is split.",
        "question_type": "reasoning",
        "difficulty_level": 5,
        "category": "people_strategy",
        "options": {},
        "correct_answer": None,
        "scoring_weight": 1.4,
        "explanation": "Look for: stakeholder input gathering, role-based flexibility framework, core collaboration days, outcome-based metrics, pilot program, iteration plan, equity considerations.",
    },

    # ── Behavioral (5 questions) ──────────────────────────────────────────
    {
        "question_text": "When an employee shares confidential personal information with you, you tend to...",
        "question_type": "behavioral_most",
        "difficulty_level": 2,
        "category": "behavioral",
        "options": {
            "statements": [
                "Protect confidentiality absolutely and only escalate when legally required",
                "Share with your direct manager for guidance",
                "Document it in the personnel file immediately",
                "Discuss it in the next HR team meeting for collective advice",
            ]
        },
        "correct_answer": None,
        "scoring_weight": 0.8,
    },
    {
        "question_text": "When leadership makes a decision you disagree with, you would least likely...",
        "question_type": "behavioral_least",
        "difficulty_level": 2,
        "category": "behavioral",
        "options": {
            "statements": [
                "Publicly challenge the decision in a meeting",
                "Implement while documenting your concerns privately",
                "Ignore the decision and let it fail on its own",
                "Complain to peers about the decision",
            ]
        },
        "correct_answer": None,
        "scoring_weight": 0.8,
    },
    {
        "question_text": "Facing an ambiguous policy situation with no precedent, you tend to...",
        "question_type": "behavioral_most",
        "difficulty_level": 3,
        "category": "behavioral",
        "options": {
            "statements": [
                "Research best practices and propose a framework for decision-making",
                "Wait for someone else to decide",
                "Apply the strictest possible interpretation",
                "Make a one-time exception and move on",
            ]
        },
        "correct_answer": None,
        "scoring_weight": 0.8,
    },
    {
        "question_text": "A manager asks you to overlook a compliance issue for a top performer. You would least likely...",
        "question_type": "behavioral_least",
        "difficulty_level": 3,
        "category": "behavioral",
        "options": {
            "statements": [
                "Agree to keep the peace and maintain the relationship",
                "Report immediately to legal without discussing with the manager",
                "Address the issue with the manager privately and explain the risk",
                "Ignore it and hope it resolves itself",
            ]
        },
        "correct_answer": None,
        "scoring_weight": 0.8,
    },
    {
        "question_text": "Your team disagrees on the approach to a sensitive restructuring. You tend to...",
        "question_type": "behavioral_most",
        "difficulty_level": 4,
        "category": "behavioral",
        "options": {
            "statements": [
                "Facilitate a structured discussion with data to guide the decision",
                "Defer to the most senior person in the room",
                "Let the CEO make the final call",
                "Delay the decision until consensus emerges naturally",
            ]
        },
        "correct_answer": None,
        "scoring_weight": 0.8,
    },
]
