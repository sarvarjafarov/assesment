"""
Management command to seed initial public assessments.
Run with: python manage.py seed_assessments
"""
from django.core.management.base import BaseCommand
from pages.models import PublicAssessment


class Command(BaseCommand):
    help = 'Seed initial public assessments for the assessment library'

    def handle(self, *args, **options):
        assessments_data = [
            {
                'slug': 'marketing',
                'internal_code': 'marketing',
                'title': 'Marketing IQ Assessment',
                'subtitle': 'Evaluate digital marketing expertise across channels',
                'label': 'Marketing IQ',
                'summary': 'Real scenarios covering paid media, SEO, analytics, and copywriting. Identify candidates who can drive growth.',
                'description': 'The Marketing IQ Assessment evaluates candidates across the full spectrum of modern digital marketing. From paid acquisition to organic growth, analytics interpretation to creative copywriting, this assessment identifies marketers who can make an immediate impact on your team.',
                'duration_minutes': 32,
                'question_count': 40,
                'difficulty_level': 'adaptive',
                'icon_svg': '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path></svg>',
                'focus_areas': ['Paid Media', 'SEO', 'Analytics', 'Copywriting'],
                'skills_tested': [
                    {'name': 'Paid Media Strategy', 'description': 'Ability to plan, execute, and optimize paid campaigns across Google, Meta, and other platforms.'},
                    {'name': 'SEO & Content', 'description': 'Understanding of technical SEO, content strategy, and organic growth tactics.'},
                    {'name': 'Analytics & Attribution', 'description': 'Skills in setting up tracking, interpreting data, and making data-driven decisions.'},
                    {'name': 'Creative & Copywriting', 'description': 'Ability to craft compelling messages that resonate with target audiences.'},
                ],
                'sample_questions': [
                    {'question': 'You notice a 40% drop in organic traffic after a site migration. Walk us through your diagnostic process.', 'type': 'Scenario'},
                    {'question': 'A client has $50K/month for paid acquisition. How would you allocate it across channels for a B2B SaaS product?', 'type': 'Strategy'},
                    {'question': 'Rewrite this landing page headline to improve conversion: "We Offer The Best Software Solutions"', 'type': 'Creative'},
                ],
                'stats': [
                    {'label': 'Question bank', 'value': '40 real scenes'},
                    {'label': 'Avg completion', 'value': '32 minutes'},
                    {'label': 'Benchmarks', 'value': 'Marketing & growth roles'},
                ],
                'use_cases': [
                    {'title': 'Growth Marketing Hires', 'description': 'Evaluate candidates for roles focused on acquisition, conversion optimization, and revenue growth.'},
                    {'title': 'Marketing Manager Screening', 'description': 'Assess strategic thinking and hands-on execution skills for mid-level marketing positions.'},
                    {'title': 'Agency Team Building', 'description': 'Screen specialists for agency roles requiring deep channel expertise.'},
                ],
                'faqs': [
                    {'question': 'How long does the assessment take?', 'answer': 'The average completion time is 32 minutes, though candidates can take up to 45 minutes if needed.'},
                    {'question': 'What marketing channels are covered?', 'answer': 'The assessment covers paid search, paid social, SEO, content marketing, email, and analytics.'},
                    {'question': 'Can I customize the questions?', 'answer': 'Enterprise plans include the ability to add custom questions and adjust the assessment focus.'},
                ],
                'scoring_rubric': 'Candidates are scored across four dimensions: Strategic Thinking (25%), Technical Execution (30%), Analytical Skills (25%), and Communication (20%). Each response is evaluated against a structured rubric by our scoring system.',
                'is_active': True,
                'is_featured': True,
                'order': 1,
            },
            {
                'slug': 'product',
                'internal_code': 'product',
                'title': 'Product Sense Assessment',
                'subtitle': 'Measure product intuition and strategic thinking',
                'label': 'Product Sense',
                'summary': 'Hands-on reasoning, estimation, prioritization, and UX critiques for PM hires at any level.',
                'description': 'The Product Sense Assessment evaluates the core competencies that separate great product managers from good ones. Through real-world scenarios and structured problem-solving exercises, identify candidates who can drive product strategy and execution.',
                'duration_minutes': 45,
                'question_count': 25,
                'difficulty_level': 'adaptive',
                'icon_svg': '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>',
                'focus_areas': ['Prioritization', 'Estimation', 'UX Critique', 'Strategy'],
                'skills_tested': [
                    {'name': 'Product Strategy', 'description': 'Ability to define product vision, identify opportunities, and create compelling roadmaps.'},
                    {'name': 'Prioritization', 'description': 'Skills in evaluating trade-offs and making decisions with incomplete information.'},
                    {'name': 'User Empathy', 'description': 'Understanding of user needs, pain points, and how to translate them into product features.'},
                    {'name': 'Analytical Thinking', 'description': 'Capability to use data for product decisions and estimate market sizes.'},
                ],
                'sample_questions': [
                    {'question': 'You have 3 engineers for one quarter. How would you prioritize between: improving onboarding, adding a requested feature, or fixing technical debt?', 'type': 'Prioritization'},
                    {'question': 'Estimate the number of Uber rides taken in San Francisco on a typical weekday.', 'type': 'Estimation'},
                    {'question': 'Review this checkout flow mockup and identify 3 UX improvements with rationale.', 'type': 'UX Critique'},
                ],
                'stats': [
                    {'label': 'Prompt mix', 'value': 'Reasoning + scenario'},
                    {'label': 'Difficulty', 'value': 'Adjusts by seniority'},
                    {'label': 'Perspectives', 'value': 'Power-user & broad view'},
                ],
                'use_cases': [
                    {'title': 'PM Hiring', 'description': 'Evaluate product management candidates from APM to Director level with role-appropriate questions.'},
                    {'title': 'Internal Mobility', 'description': 'Assess employees transitioning into product roles from engineering, design, or other functions.'},
                    {'title': 'Promotion Decisions', 'description': 'Use structured assessment to inform PM leveling and promotion conversations.'},
                ],
                'faqs': [
                    {'question': 'Does difficulty adjust for seniority?', 'answer': 'Yes, you can configure the assessment for APM, PM, Senior PM, or Director-level candidates.'},
                    {'question': 'What types of products are covered?', 'answer': 'Questions span B2B SaaS, consumer apps, marketplaces, and platform products.'},
                    {'question': 'How is product sense scored?', 'answer': 'We evaluate structured thinking, user focus, business acumen, and communication clarity.'},
                ],
                'scoring_rubric': 'Product Sense scores are based on: Structured Thinking (30%), User Focus (25%), Business Acumen (25%), and Communication (20%). Responses are evaluated for depth of analysis and practical applicability.',
                'is_active': True,
                'is_featured': True,
                'order': 2,
            },
            {
                'slug': 'behavioral',
                'internal_code': 'behavioral',
                'title': 'Behavioral DNA Assessment',
                'subtitle': 'Understand work style, values, and team fit',
                'label': 'Behavioral DNA',
                'summary': 'Short reflections that reveal teamwork style, risk comfort, and coaching needs for any role.',
                'description': 'The Behavioral DNA Assessment goes beyond skills to understand how candidates work. Through carefully designed reflection prompts, uncover work styles, values, and potential fit with your team culture.',
                'duration_minutes': 15,
                'question_count': 12,
                'difficulty_level': 'adaptive',
                'icon_svg': '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>',
                'focus_areas': ['Collaboration', 'Risk Posture', 'Coaching', 'Values'],
                'skills_tested': [
                    {'name': 'Collaboration Style', 'description': 'How candidates prefer to work with others and handle team dynamics.'},
                    {'name': 'Decision Making', 'description': 'Approach to risk, ambiguity, and making choices under uncertainty.'},
                    {'name': 'Growth Mindset', 'description': 'Openness to feedback, learning from failure, and continuous improvement.'},
                    {'name': 'Values Alignment', 'description': 'What motivates the candidate and how they prioritize competing interests.'},
                ],
                'sample_questions': [
                    {'question': 'Describe a time when you disagreed with your manager. How did you handle it?', 'type': 'Reflection'},
                    {'question': 'What does a healthy team culture look like to you?', 'type': 'Values'},
                    {'question': 'Tell us about a project that failed and what you learned from it.', 'type': 'Growth'},
                ],
                'stats': [
                    {'label': 'Duration', 'value': '15 minutes'},
                    {'label': 'Signals', 'value': 'Integrity + engagement'},
                    {'label': 'Deliverable', 'value': 'Guided debrief points'},
                ],
                'use_cases': [
                    {'title': 'Culture Fit Assessment', 'description': 'Understand how candidates will mesh with your existing team dynamics and values.'},
                    {'title': 'Leadership Potential', 'description': 'Identify candidates with leadership qualities regardless of their current title.'},
                    {'title': 'Onboarding Preparation', 'description': 'Use insights to customize onboarding and set new hires up for success.'},
                ],
                'faqs': [
                    {'question': 'Is this a personality test?', 'answer': 'No, this is a structured reflection exercise. There are no right or wrong answers—we help you understand work style fit.'},
                    {'question': 'How should I use the results?', 'answer': 'Results come with guided debrief points for interviewers to explore in follow-up conversations.'},
                    {'question': 'Can this be used for any role?', 'answer': 'Yes, the Behavioral DNA assessment works for any role from individual contributor to executive.'},
                ],
                'scoring_rubric': 'Behavioral responses are analyzed for: Self-Awareness (25%), Communication Clarity (25%), Values Articulation (25%), and Growth Indicators (25%). Results include talking points for interviewers.',
                'is_active': True,
                'is_featured': True,
                'order': 3,
            },
        ]

        created_count = 0
        updated_count = 0

        for data in assessments_data:
            assessment, created = PublicAssessment.objects.update_or_create(
                slug=data['slug'],
                defaults=data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {assessment.label}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Updated: {assessment.label}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created {created_count}, updated {updated_count} assessments.'
        ))
