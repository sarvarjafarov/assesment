from django.test import TestCase

from assessments.models import (
    Assessment,
    AssessmentSession,
    CandidateProfile,
    Choice,
    Question,
    RoleCategory,
)
from assessments.services import record_responses


class RecordResponsesEvaluationTests(TestCase):
    def setUp(self):
        category = RoleCategory.objects.create(name="Ops", slug="ops")
        self.assessment = Assessment.objects.create(
            category=category,
            title="Ops Readiness",
            slug="ops-readiness",
            summary="Test",
        )
        self.single_question = Question.objects.create(
            assessment=self.assessment,
            prompt="Primary KPI?",
            question_type=Question.TYPE_SINGLE,
            order=1,
        )
        self.good_choice = Choice.objects.create(
            question=self.single_question, label="Right", weight=1.0
        )
        self.bad_choice = Choice.objects.create(
            question=self.single_question, label="Wrong", weight=0.0
        )
        self.multi_question = Question.objects.create(
            assessment=self.assessment,
            prompt="Pick tools",
            question_type=Question.TYPE_MULTI,
            order=2,
        )
        self.multi_primary = Choice.objects.create(
            question=self.multi_question, label="Tool A", weight=0.6
        )
        self.multi_secondary = Choice.objects.create(
            question=self.multi_question, label="Tool B", weight=0.4
        )
        candidate = CandidateProfile.objects.create(
            first_name="Ava", email="ava@example.com"
        )
        self.session = AssessmentSession.objects.create(
            candidate=candidate, assessment=self.assessment, status="invited"
        )

    def test_scores_and_advances_high_performance(self):
        answers = [
            {"question_id": self.single_question.id, "choice_ids": [self.good_choice.id]},
            {"question_id": self.multi_question.id, "choice_ids": [self.multi_primary.id]},
        ]
        record_responses(session=self.session, answers=answers)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, "completed")
        self.assertAlmostEqual(self.session.overall_score, 80.0)
        self.assertEqual(self.session.decision, "advance")
        self.assertIn("question_scores", self.session.score_breakdown)
        self.assertEqual(
            self.session.score_breakdown.get("auto_decision"),
            "advance",
        )

    def test_scores_and_rejects_low_performance(self):
        answers = [
            {"question_id": self.single_question.id, "choice_ids": [self.bad_choice.id]},
            {"question_id": self.multi_question.id, "choice_ids": [self.multi_secondary.id]},
        ]
        record_responses(session=self.session, answers=answers)
        self.session.refresh_from_db()
        self.assertEqual(self.session.decision, "reject")
        self.assertAlmostEqual(self.session.overall_score, 20.0)
