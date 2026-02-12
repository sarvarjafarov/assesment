"""
Management command to seed SEO roles and interview questions.
Creates ~30 roles across 6 departments with ~12 interview questions each.
Run with: python manage.py seed_seo_roles
"""
from django.core.management.base import BaseCommand
from pages.models import Role, InterviewQuestion, PublicAssessment

from ._seed_data.marketing import MARKETING_ROLES
from ._seed_data.product import PRODUCT_ROLES
from ._seed_data.design import DESIGN_ROLES
from ._seed_data.hr import HR_ROLES
from ._seed_data.finance import FINANCE_ROLES
from ._seed_data.leadership import LEADERSHIP_ROLES


class Command(BaseCommand):
    help = 'Seed SEO roles and interview questions for programmatic SEO pages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing roles and questions before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing roles and questions...')
            InterviewQuestion.objects.all().delete()
            Role.objects.all().delete()

        all_roles = (
            MARKETING_ROLES + PRODUCT_ROLES + DESIGN_ROLES +
            HR_ROLES + FINANCE_ROLES + LEADERSHIP_ROLES
        )

        # Cache assessment lookup
        assessment_map = {}
        for pa in PublicAssessment.objects.all():
            assessment_map[pa.slug] = pa

        roles_created = 0
        roles_updated = 0
        questions_created = 0
        questions_updated = 0

        for i, role_data in enumerate(all_roles, 1):
            questions = role_data.pop('questions')
            assessment_slugs = role_data.pop('assessment_slugs')

            role, created = Role.objects.update_or_create(
                slug=role_data['slug'],
                defaults={**role_data, 'order': i},
            )

            if created:
                roles_created += 1
            else:
                roles_updated += 1

            # Set M2M assessment_types
            assessments = [
                assessment_map[s] for s in assessment_slugs
                if s in assessment_map
            ]
            role.assessment_types.set(assessments)

            # Create/update questions
            for j, q_data in enumerate(questions, 1):
                # Resolve optional assessment_type FK
                at_slug = q_data.pop('assessment_type_slug', None)
                at = assessment_map.get(at_slug) if at_slug else None

                q, q_created = InterviewQuestion.objects.update_or_create(
                    role=role,
                    question_text=q_data['question_text'],
                    defaults={
                        'category': q_data['category'],
                        'difficulty': q_data['difficulty'],
                        'what_it_tests': q_data['what_it_tests'],
                        'sample_answer_outline': q_data.get('sample_answer_outline', ''),
                        'assessment_type': at,
                        'order': j,
                        'is_active': True,
                    },
                )

                if q_created:
                    questions_created += 1
                else:
                    questions_updated += 1

            self.stdout.write(f'  [{i}/{len(all_roles)}] {role.title} — {len(questions)} questions')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Roles: {roles_created} created, {roles_updated} updated. '
            f'Questions: {questions_created} created, {questions_updated} updated.'
        ))
