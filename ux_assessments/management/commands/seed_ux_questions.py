from django.core.management.base import BaseCommand

from ux_assessments.models import UXDesignQuestion


class Command(BaseCommand):
    help = "Seed the UX/UI design question bank with starter prompts."

    def handle(self, *args, **options):
        created = 0
        for payload in SAMPLE_QUESTIONS:
            obj, was_created = UXDesignQuestion.objects.get_or_create(
                question_text=payload["question_text"],
                defaults={k: v for k, v in payload.items() if k != "question_text"},
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} questions."))


SAMPLE_QUESTIONS = [
    # ── User Research (6 questions) ──────────────────────────────────────
    {
        "question_text": "What is the primary goal of a usability test?",
        "question_type": "multiple_choice",
        "difficulty_level": 1,
        "category": "user_research",
        "options": {
            "choices": [
                {"id": "A", "text": "Validate design assumptions by observing real users"},
                {"id": "B", "text": "Make the interface look prettier"},
                {"id": "C", "text": "Impress stakeholders with test footage"},
                {"id": "D", "text": "Replace surveys entirely"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Usability tests reveal how real users interact with a product to validate or invalidate design decisions.",
    },
    {
        "question_text": "Which research method is best for understanding *why* users abandon a checkout flow?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "user_research",
        "options": {
            "choices": [
                {"id": "A", "text": "Moderated usability testing with think-aloud protocol"},
                {"id": "B", "text": "A/B testing two checkout layouts"},
                {"id": "C", "text": "Analytics funnel review"},
                {"id": "D", "text": "Competitive audit of rival checkouts"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Think-aloud usability testing reveals the reasoning behind user behaviour, not just what they do.",
    },
    {
        "question_text": "You have 2 weeks and $500 budget. Stakeholders want user validation for a new onboarding flow. Which approach do you take?",
        "question_type": "scenario",
        "difficulty_level": 3,
        "category": "user_research",
        "options": {
            "choices": [
                {"id": "A", "text": "Guerrilla testing with 5 users in a coffee shop using a prototype"},
                {"id": "B", "text": "Online unmoderated study with 20 participants via a tool like Maze"},
                {"id": "C", "text": "Send a 200-person survey about onboarding preferences"},
                {"id": "D", "text": "Wait for more budget to run a proper lab study"},
            ]
        },
        "correct_answer": "B",
        "scoring_weight": 1.2,
        "explanation": "Unmoderated testing scales well within budget, provides task-level data, and 20 users gives statistical confidence.",
    },
    {
        "question_text": "A PM asks you to validate a redesign but the launch date is in 3 days. Explain how you'd gather meaningful feedback under this constraint.",
        "question_type": "reasoning",
        "difficulty_level": 4,
        "category": "user_research",
        "options": {},
        "correct_answer": None,
        "scoring_weight": 1.4,
        "explanation": "Look for: rapid guerrilla tests, 5-second tests, internal hallway testing, lightweight prototype review, or post-launch monitoring plan.",
    },
    {
        "question_text": "When triangulating research data, which combination yields the most robust insights?",
        "question_type": "multiple_choice",
        "difficulty_level": 5,
        "category": "user_research",
        "options": {
            "choices": [
                {"id": "A", "text": "User interviews + analytics data + diary study"},
                {"id": "B", "text": "Surveys + heatmaps + A/B tests"},
                {"id": "C", "text": "Card sorting + tree testing + competitive audit"},
                {"id": "D", "text": "Focus groups + stakeholder interviews + benchmarking"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Combining qualitative depth (interviews), quantitative behaviour (analytics), and longitudinal context (diary study) provides the strongest triangulation.",
    },
    {
        "question_text": "You receive conflicting feedback from user interviews: half the users love a feature and half find it confusing. What do you do?",
        "question_type": "behavioral_most",
        "difficulty_level": 2,
        "category": "user_research",
        "options": {
            "statements": [
                "Segment users by experience level and analyze patterns within each group",
                "Go with the majority opinion since more people liked it",
                "Discard the research and run a quantitative survey instead",
                "Ask stakeholders to make the final call",
            ]
        },
        "correct_answer": None,
        "scoring_weight": 0.8,
    },

    # ── Information Architecture (5 questions) ───────────────────────────
    {
        "question_text": "What is card sorting primarily used for?",
        "question_type": "multiple_choice",
        "difficulty_level": 1,
        "category": "information_architecture",
        "options": {
            "choices": [
                {"id": "A", "text": "Organizing content structure based on user mental models"},
                {"id": "B", "text": "Testing visual design preferences"},
                {"id": "C", "text": "Measuring page load performance"},
                {"id": "D", "text": "Creating wireframes for stakeholder review"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Card sorting reveals how users group and label content, directly informing navigation and IA decisions.",
    },
    {
        "question_text": "An e-commerce site has 500+ products. Which IA pattern best helps users find items quickly?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "information_architecture",
        "options": {
            "choices": [
                {"id": "A", "text": "Faceted navigation with filters for price, category, and attributes"},
                {"id": "B", "text": "A single flat list sorted alphabetically"},
                {"id": "C", "text": "A search bar as the only navigation method"},
                {"id": "D", "text": "Alphabetical category pages without filters"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Faceted navigation lets users progressively narrow results using multiple dimensions, ideal for large catalogs.",
    },
    {
        "question_text": "Users report they can't find the 'Billing' section in your B2B SaaS product. Analytics show 40% use search to reach it. What's your recommended approach?",
        "question_type": "scenario",
        "difficulty_level": 3,
        "category": "information_architecture",
        "options": {
            "choices": [
                {"id": "A", "text": "Run a tree test to identify where users expect Billing, then restructure navigation"},
                {"id": "B", "text": "Add a prominent Billing shortcut to the main sidebar"},
                {"id": "C", "text": "Improve the search algorithm to surface Billing faster"},
                {"id": "D", "text": "Add a tooltip to help users find Billing the first time"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Tree testing validates the right location data-driven before committing to a structural change.",
    },
    {
        "question_text": "Rank these IA validation methods by effectiveness for a B2B SaaS dashboard redesign.",
        "question_type": "ranking",
        "difficulty_level": 4,
        "category": "information_architecture",
        "options": {
            "items": ["Tree testing", "Card sorting", "First-click testing", "Analytics review"]
        },
        "correct_answer": ["Tree testing", "First-click testing", "Card sorting", "Analytics review"],
        "scoring_weight": 1.2,
        "explanation": "Tree testing directly validates findability; first-click shows entry points; card sorting informs grouping; analytics confirms patterns but doesn't explain why.",
    },
    {
        "question_text": "Describe how you'd restructure a healthcare portal's navigation that has grown from 12 to 85 pages over 3 years with no IA review.",
        "question_type": "reasoning",
        "difficulty_level": 5,
        "category": "information_architecture",
        "options": {},
        "correct_answer": None,
        "scoring_weight": 1.4,
        "explanation": "Look for: content audit, open card sort with users, stakeholder alignment, tree testing validation, phased migration, redirect strategy.",
    },

    # ── Interaction Design (7 questions) ─────────────────────────────────
    {
        "question_text": "Which UX principle explains why buttons should look clickable?",
        "question_type": "multiple_choice",
        "difficulty_level": 1,
        "category": "interaction_design",
        "options": {
            "choices": [
                {"id": "A", "text": "Affordance — elements should suggest their function"},
                {"id": "B", "text": "Fitts's Law — larger targets are easier to click"},
                {"id": "C", "text": "Hick's Law — fewer choices speed decisions"},
                {"id": "D", "text": "Gestalt closure — users complete incomplete shapes"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Affordance (Norman) means the perceived properties of an object suggest how it can be used.",
    },
    {
        "question_text": "A modal dialog opens but users don't notice the close button. What's the most likely issue?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "interaction_design",
        "options": {
            "choices": [
                {"id": "A", "text": "Low contrast and poor placement of the close button"},
                {"id": "B", "text": "The modal is too small on screen"},
                {"id": "C", "text": "Users see too many modals in general"},
                {"id": "D", "text": "The font size inside the modal is too large"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "The most common cause is a low-contrast X icon placed in a non-standard position, violating expectations.",
    },
    {
        "question_text": "You're designing a multi-step form with 8 steps. Which pattern best reduces abandonment?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "interaction_design",
        "options": {
            "choices": [
                {"id": "A", "text": "Progress stepper with save-as-draft at each step"},
                {"id": "B", "text": "A single scrolling page with all fields visible"},
                {"id": "C", "text": "Accordion sections that expand one at a time"},
                {"id": "D", "text": "Tab navigation across the 8 sections"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "A progress stepper shows completion status and save-as-draft prevents data loss — the combination reduces form abandonment the most.",
    },
    {
        "question_text": "Users report your drag-and-drop kanban board is unusable on mobile. How do you approach a redesign?",
        "question_type": "scenario",
        "difficulty_level": 3,
        "category": "interaction_design",
        "options": {
            "choices": [
                {"id": "A", "text": "Replace drag-and-drop with a tap-to-move dropdown on mobile while keeping drag on desktop"},
                {"id": "B", "text": "Shrink the kanban columns to fit mobile width"},
                {"id": "C", "text": "Hide the board on mobile and show a list view only"},
                {"id": "D", "text": "Add a tutorial overlay explaining how to drag on touch screens"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Adapting the interaction pattern per device (progressive disclosure) preserves functionality without forcing a touch-unfriendly paradigm.",
    },
    {
        "question_text": "Rank these micro-interaction principles by impact on perceived performance.",
        "question_type": "ranking",
        "difficulty_level": 4,
        "category": "interaction_design",
        "options": {
            "items": ["Skeleton screens", "Progress indicators", "Optimistic UI", "Loading spinners"]
        },
        "correct_answer": ["Optimistic UI", "Skeleton screens", "Progress indicators", "Loading spinners"],
        "scoring_weight": 1.2,
        "explanation": "Optimistic UI feels instant; skeleton screens create anticipation; progress indicators set expectations; spinners are the least informative.",
    },
    {
        "question_text": "A multi-step form has a 60% abandonment rate at step 3 of 5. Walk through your process to diagnose and fix this.",
        "question_type": "reasoning",
        "difficulty_level": 4,
        "category": "interaction_design",
        "options": {},
        "correct_answer": None,
        "scoring_weight": 1.4,
        "explanation": "Look for: analytics deep dive, session recordings, field-level analysis, user interviews, hypothesis-driven A/B tests, and possible step consolidation.",
    },
    {
        "question_text": "When designing a real-time collaborative editor (like Figma), which conflict resolution pattern is most appropriate?",
        "question_type": "multiple_choice",
        "difficulty_level": 5,
        "category": "interaction_design",
        "options": {
            "choices": [
                {"id": "A", "text": "Operational Transform (OT) for concurrent edit merging"},
                {"id": "B", "text": "Last-write-wins with timestamp comparison"},
                {"id": "C", "text": "Lock-based editing where one user edits at a time"},
                {"id": "D", "text": "Manual merge dialog when conflicts are detected"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "OT (or CRDTs) enables simultaneous edits by transforming operations against each other, the standard for real-time collaboration.",
    },

    # ── Visual Design (6 questions) ──────────────────────────────────────
    {
        "question_text": "What is the recommended minimum contrast ratio for body text under WCAG AA?",
        "question_type": "multiple_choice",
        "difficulty_level": 1,
        "category": "visual_design",
        "options": {
            "choices": [
                {"id": "A", "text": "4.5:1"},
                {"id": "B", "text": "3:1"},
                {"id": "C", "text": "7:1"},
                {"id": "D", "text": "2:1"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "WCAG AA requires a minimum 4.5:1 contrast ratio for normal text and 3:1 for large text.",
    },
    {
        "question_text": "Which typographic scale creates the most harmonious heading hierarchy?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "visual_design",
        "options": {
            "choices": [
                {"id": "A", "text": "Major third (1.25) with consistent ratio between levels"},
                {"id": "B", "text": "Random sizes chosen by visual feel"},
                {"id": "C", "text": "Doubling font size at each heading level"},
                {"id": "D", "text": "Same font size for all headings, differentiated only by bold weight"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "A modular scale (like major third 1.25) creates mathematically harmonious proportions between type sizes.",
    },
    {
        "question_text": "A client's brand uses red (#FF0000) as the primary color. How do you handle error states without confusing users?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "visual_design",
        "options": {
            "choices": [
                {"id": "A", "text": "Use a distinctly different red shade for errors plus an icon and descriptive text"},
                {"id": "B", "text": "Change the brand color to avoid the conflict"},
                {"id": "C", "text": "Use only text (no color) for error messages"},
                {"id": "D", "text": "Use orange for all error states instead"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Multi-signal error design (color differentiation + icon + text) ensures clarity even when brand and error colors overlap.",
    },
    {
        "question_text": "Stakeholders want to use 5 different fonts across the product for 'visual variety'. How do you push back constructively?",
        "question_type": "scenario",
        "difficulty_level": 3,
        "category": "visual_design",
        "options": {
            "choices": [
                {"id": "A", "text": "Present data on performance (load time), readability, and brand consistency; propose 2 fonts max with weight/size variations"},
                {"id": "B", "text": "Agree and implement all 5 fonts as requested"},
                {"id": "C", "text": "Refuse and use only 1 font throughout the product"},
                {"id": "D", "text": "Implement 5 fonts but hide 3 behind a feature flag"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Educating stakeholders with data while offering an alternative achieves both design quality and stakeholder respect.",
    },
    {
        "question_text": "Rank these visual hierarchy techniques by effectiveness for drawing user attention to a primary CTA.",
        "question_type": "ranking",
        "difficulty_level": 4,
        "category": "visual_design",
        "options": {
            "items": ["Size contrast", "Color contrast", "Whitespace isolation", "Subtle motion"]
        },
        "correct_answer": ["Color contrast", "Size contrast", "Whitespace isolation", "Subtle motion"],
        "scoring_weight": 1.2,
        "explanation": "Color contrast is the strongest initial attention-getter; size amplifies it; whitespace isolates; motion should be used sparingly.",
    },
    {
        "question_text": "Design a color system for a fintech app that needs to work in dark mode, light mode, and high-contrast accessibility mode. Describe your approach and the token structure you'd create.",
        "question_type": "reasoning",
        "difficulty_level": 5,
        "category": "visual_design",
        "options": {},
        "correct_answer": None,
        "scoring_weight": 1.4,
        "explanation": "Look for: semantic token layers (primary, surface, on-surface), theme switching via CSS custom properties, WCAG AAA ratios for high-contrast, systematic naming conventions.",
    },

    # ── Usability & Accessibility (6 questions) ─────────────────────────
    {
        "question_text": "Which of Nielsen's 10 usability heuristics does a 'Back' button satisfy?",
        "question_type": "multiple_choice",
        "difficulty_level": 1,
        "category": "usability_accessibility",
        "options": {
            "choices": [
                {"id": "A", "text": "User control and freedom"},
                {"id": "B", "text": "Visibility of system status"},
                {"id": "C", "text": "Error prevention"},
                {"id": "D", "text": "Consistency and standards"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "User control and freedom (heuristic #3) provides users with an 'emergency exit' to undo or leave an unwanted state.",
    },
    {
        "question_text": "A screen reader user cannot navigate your web form. What's the most likely missing element?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "usability_accessibility",
        "options": {
            "choices": [
                {"id": "A", "text": "Proper label elements associated with inputs and ARIA attributes"},
                {"id": "B", "text": "CSS animations for focus indicators"},
                {"id": "C", "text": "Custom hover states on form fields"},
                {"id": "D", "text": "Responsive breakpoints for mobile screens"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Screen readers rely on <label> elements and ARIA attributes to announce form fields. Without them, forms are inaccessible.",
    },
    {
        "question_text": "You discover 15 usability issues during testing. How do you prioritize which to fix first?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "usability_accessibility",
        "options": {
            "choices": [
                {"id": "A", "text": "Use a severity x frequency matrix to rank by user impact"},
                {"id": "B", "text": "Fix all 15 at once before the next release"},
                {"id": "C", "text": "Fix them in the order they were discovered"},
                {"id": "D", "text": "Only fix the ones stakeholders noticed"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "A severity-frequency matrix ensures the highest-impact issues get attention first, maximizing value per engineering effort.",
    },
    {
        "question_text": "Your product team says accessibility is 'nice to have' and won't allocate sprint time. How do you advocate for it?",
        "question_type": "scenario",
        "difficulty_level": 4,
        "category": "usability_accessibility",
        "options": {
            "choices": [
                {"id": "A", "text": "Present legal risk (ADA/WCAG lawsuits), market size data, and propose baking a11y into existing tickets rather than separate work"},
                {"id": "B", "text": "Quietly implement accessibility improvements without telling the team"},
                {"id": "C", "text": "Escalate to executive leadership immediately"},
                {"id": "D", "text": "Accept the decision and move on to other priorities"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Framing accessibility as risk mitigation and an integrated practice (not extra work) is the most effective advocacy approach.",
    },
    {
        "question_text": "Rank these accessibility improvements by impact for a content-heavy news website.",
        "question_type": "ranking",
        "difficulty_level": 4,
        "category": "usability_accessibility",
        "options": {
            "items": ["Alt text for images", "Keyboard navigation", "Color contrast", "Semantic HTML"]
        },
        "correct_answer": ["Semantic HTML", "Keyboard navigation", "Color contrast", "Alt text for images"],
        "scoring_weight": 1.2,
        "explanation": "Semantic HTML is foundational (affects all assistive tech); keyboard navigation enables interaction; contrast aids readability; alt text provides image context.",
    },
    {
        "question_text": "Describe how you'd conduct a comprehensive accessibility audit for a 50-page web application, including tools, process, and deliverables.",
        "question_type": "reasoning",
        "difficulty_level": 5,
        "category": "usability_accessibility",
        "options": {},
        "correct_answer": None,
        "scoring_weight": 1.4,
        "explanation": "Look for: automated scanning (axe, Lighthouse), manual keyboard testing, screen reader testing (NVDA/VoiceOver), WCAG checklist, prioritized report, remediation roadmap.",
    },

    # ── Design Strategy (5 questions) ────────────────────────────────────
    {
        "question_text": "What is the primary purpose of a design system?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "design_strategy",
        "options": {
            "choices": [
                {"id": "A", "text": "Consistency and efficiency at scale across products and teams"},
                {"id": "B", "text": "Making designers unnecessary by automating layouts"},
                {"id": "C", "text": "Locking down creativity to prevent experimentation"},
                {"id": "D", "text": "Documenting every pixel for developer hand-off"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Design systems provide shared components, patterns, and guidelines that ensure consistency while enabling faster iteration.",
    },
    {
        "question_text": "Engineering pushes back on your design because implementation would take 3 sprints. How do you proceed?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "design_strategy",
        "options": {
            "choices": [
                {"id": "A", "text": "Negotiate scope with phased delivery: launch MVP first, enhance iteratively"},
                {"id": "B", "text": "Redesign everything simpler to fit one sprint"},
                {"id": "C", "text": "Escalate to the PM to override engineering's estimate"},
                {"id": "D", "text": "Learn to code and implement it yourself"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Phased delivery balances design quality with engineering reality. Shipping an MVP first gets user feedback earlier.",
    },
    {
        "question_text": "You inherit a design system with 47 button variants. Stakeholders resist consolidation because 'every team needs their buttons'. What's your strategy?",
        "question_type": "scenario",
        "difficulty_level": 4,
        "category": "design_strategy",
        "options": {
            "choices": [
                {"id": "A", "text": "Audit usage data to show overlap, propose 8-10 core variants, deprecate unused ones gradually with a migration guide"},
                {"id": "B", "text": "Delete all variants and start from scratch with 3 buttons"},
                {"id": "C", "text": "Keep all 47 but rename them for consistency"},
                {"id": "D", "text": "Let each team maintain their own button library separately"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Data-driven consolidation with a migration path respects existing work while reducing debt systematically.",
    },
    {
        "question_text": "Describe how you'd measure the ROI of investing in a design system for a company with 8 product teams.",
        "question_type": "reasoning",
        "difficulty_level": 4,
        "category": "design_strategy",
        "options": {},
        "correct_answer": None,
        "scoring_weight": 1.4,
        "explanation": "Look for: time savings (design + dev), consistency audits, adoption metrics, reduced QA cycles, component reuse rates, developer satisfaction surveys.",
    },
    {
        "question_text": "When scaling design operations across multiple product lines, which governance model works best?",
        "question_type": "multiple_choice",
        "difficulty_level": 5,
        "category": "design_strategy",
        "options": {
            "choices": [
                {"id": "A", "text": "Federated model with a central foundation team and embedded product designers"},
                {"id": "B", "text": "Fully centralized design team that handles all products"},
                {"id": "C", "text": "Fully decentralized with no shared standards or tools"},
                {"id": "D", "text": "Rotating ownership where each team leads design for a quarter"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Federated governance balances consistency (central standards) with agility (embedded designers who know product context).",
    },

    # ── Behavioral (5 questions) ─────────────────────────────────────────
    {
        "question_text": "When receiving critical feedback on a design you've invested significant time in, you tend to...",
        "question_type": "behavioral_most",
        "difficulty_level": 2,
        "category": "behavioral",
        "options": {
            "statements": [
                "Welcome it and start iterating immediately",
                "Defend your rationale with the research behind it",
                "Ask for specific examples before reacting",
                "Take time to process privately before responding",
            ]
        },
        "correct_answer": None,
        "scoring_weight": 0.8,
    },
    {
        "question_text": "In a design review, a developer says your design is impossible to build within the timeline. You would least likely...",
        "question_type": "behavioral_least",
        "difficulty_level": 2,
        "category": "behavioral",
        "options": {
            "statements": [
                "Simplify the design immediately to fit the timeline",
                "Explain the user value to justify the complexity",
                "Ask what's feasible and collaborate on alternatives",
                "Escalate to the PM to resolve the disagreement",
            ]
        },
        "correct_answer": None,
        "scoring_weight": 0.8,
    },
    {
        "question_text": "Faced with an ambiguous brief and a tight deadline, you tend to...",
        "question_type": "behavioral_most",
        "difficulty_level": 3,
        "category": "behavioral",
        "options": {
            "statements": [
                "Make informed assumptions and iterate based on feedback",
                "Request complete requirements before starting any work",
                "Benchmark competitors to fill in the gaps",
                "Sketch multiple concepts and let stakeholders choose",
            ]
        },
        "correct_answer": None,
        "scoring_weight": 0.8,
    },
    {
        "question_text": "A stakeholder overrides your research-backed design decision. You would least likely...",
        "question_type": "behavioral_least",
        "difficulty_level": 3,
        "category": "behavioral",
        "options": {
            "statements": [
                "Comply and document your concerns for future reference",
                "Push back firmly with data and user quotes",
                "Escalate to senior leadership for a final decision",
                "Find a compromise that addresses both the stakeholder's concern and user needs",
            ]
        },
        "correct_answer": None,
        "scoring_weight": 0.8,
    },
    {
        "question_text": "Your team disagrees on the design direction for a critical feature. You tend to...",
        "question_type": "behavioral_most",
        "difficulty_level": 4,
        "category": "behavioral",
        "options": {
            "statements": [
                "Facilitate a structured design critique with clear evaluation criteria",
                "Defer to the most senior designer on the team",
                "Propose A/B testing both directions with real users",
                "Let the product manager make the final call",
            ]
        },
        "correct_answer": None,
        "scoring_weight": 0.8,
    },
]
