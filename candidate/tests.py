from django.test import TestCase
from django.urls import reverse

from assessments.models import (
    Assessment,
    AssessmentSession,
    CandidateProfile,
    Choice,
    Question,
    RoleCategory,
)
from .forms import AssessmentResponseForm


class AssessmentResponseFormTests(TestCase):
    def setUp(self):
        self.category = RoleCategory.objects.create(
            name="Test Category", slug="test-category"
        )
        self.assessment = Assessment.objects.create(
            category=self.category,
            title="Test Assessment",
            slug="test-assessment",
            summary="Summary",
            level="intro",
            duration_minutes=10,
        )
        self.single_question = Question.objects.create(
            assessment=self.assessment,
            prompt="Single select?",
            question_type=Question.TYPE_SINGLE,
            order=1,
        )
        self.multi_question = Question.objects.create(
            assessment=self.assessment,
            prompt="Multi select?",
            question_type=Question.TYPE_MULTI,
            order=2,
        )
        self.text_question = Question.objects.create(
            assessment=self.assessment,
            prompt="Tell us more",
            question_type=Question.TYPE_TEXT,
            order=3,
        )
        self.choice_a = Choice.objects.create(
            question=self.single_question, label="A", weight=1.0
        )
        self.choice_b = Choice.objects.create(
            question=self.multi_question, label="B", weight=1.0
        )

    def test_to_answers_returns_choice_ids_and_text(self):
        data = {
            f"question_{self.single_question.id}": str(self.choice_a.id),
            f"question_{self.multi_question.id}": [str(self.choice_b.id)],
            f"question_{self.text_question.id}": "Free text",
        }
        form = AssessmentResponseForm(data=data, assessment=self.assessment)
        self.assertTrue(form.is_valid())
        answers = form.to_answers()
        self.assertEqual(len(answers), 3)
        single = next(a for a in answers if a["question_id"] == self.single_question.id)
        self.assertEqual(single["choice_ids"], [self.choice_a.id])
        multi = next(a for a in answers if a["question_id"] == self.multi_question.id)
        self.assertEqual(multi["choice_ids"], [self.choice_b.id])
        text = next(a for a in answers if a["question_id"] == self.text_question.id)
        self.assertEqual(text["answer_text"], "Free text")


class CandidateSessionFlowTests(TestCase):
    def setUp(self):
        category = RoleCategory.objects.create(name="Cat", slug="cat")
        self.assessment = Assessment.objects.create(
            category=category,
            title="Assessment",
            slug="assessment",
            summary="Summary",
            level="intro",
            duration_minutes=5,
        )
        self.question = Question.objects.create(
            assessment=self.assessment,
            prompt="Pick one",
            question_type=Question.TYPE_SINGLE,
            order=1,
        )
        self.choice = Choice.objects.create(
            question=self.question,
            label="Choice",
            weight=1.0,
        )
        self.candidate = CandidateProfile.objects.create(
            first_name="Casey", email="casey@example.com"
        )
        self.session = AssessmentSession.objects.create(
            candidate=self.candidate, assessment=self.assessment, status="invited"
        )

    def test_visit_marks_session_in_progress_and_submit(self):
        entry_url = reverse("candidate:session-entry", args=[self.session.uuid])
        response = self.client.get(entry_url)
        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, "invited")
        start_url = reverse("candidate:session-start", args=[self.session.uuid])
        response = self.client.get(start_url)
        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, "in_progress")
        post_data = {
            f"question_{self.question.id}": str(self.choice.id),
        }
        response = self.client.post(start_url, data=post_data)
        self.assertRedirects(
            response, reverse("candidate:session-complete", args=[self.session.uuid])
        )
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, "completed")
        self.assertTrue(self.session.submitted_at)
        self.assertEqual(self.session.responses.count(), 1)
