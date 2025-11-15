import json

from django.test import TestCase
from django.urls import reverse

from assessments.behavioral import get_behavioral_blocks
from assessments.models import (
    Assessment,
    AssessmentSession,
    CandidateProfile,
    Choice,
    Question,
    RoleCategory,
)
from .forms import QuestionStepForm


class QuestionStepFormTests(TestCase):
    def setUp(self):
        category = RoleCategory.objects.create(name="Test", slug="test")
        self.assessment = Assessment.objects.create(
            category=category,
            title="Test Assessment",
            slug="test-assessment",
            summary="Summary",
        )
        self.single_question = Question.objects.create(
            assessment=self.assessment,
            prompt="Single select?",
            question_type=Question.TYPE_SINGLE,
            order=1,
        )
        self.choice = Choice.objects.create(
            question=self.single_question, label="Option", weight=1.0
        )
        self.behavioral_question = Question.objects.create(
            assessment=self.assessment,
            prompt="Behavioral matrix",
            question_type=Question.TYPE_BEHAVIORAL,
            order=2,
            metadata={"behavioral_bank": {"blocks": [1]}},
        )

    def test_single_choice_to_answer(self):
        form = QuestionStepForm(
            data={"response": str(self.choice.id)}, question=self.single_question
        )
        self.assertTrue(form.is_valid())
        payload = form.to_answer()
        self.assertEqual(payload["choice_ids"], [self.choice.id])

    def test_behavioral_block_to_answer(self):
        block = get_behavioral_blocks([1])[0]
        form = QuestionStepForm(
            data={"most_like": "1A", "least_like": "1B"},
            question=self.behavioral_question,
            behavioral_block=block,
        )
        self.assertTrue(form.is_valid(), form.errors)
        payload = form.to_answer()
        self.assertEqual(len(payload["behavioral_responses"]), 2)
        self.assertEqual(payload["behavioral_responses"][0]["statement_id"], "1A")


class CandidateSessionFlowTests(TestCase):
    def setUp(self):
        category = RoleCategory.objects.create(name="General", slug="general")
        self.assessment = Assessment.objects.create(
            category=category,
            title="Assessment",
            slug="assessment",
            summary="Summary",
            level="intro",
            duration_minutes=5,
        )
        self.single_question = Question.objects.create(
            assessment=self.assessment,
            prompt="Pick one",
            question_type=Question.TYPE_SINGLE,
            order=1,
        )
        self.choice = Choice.objects.create(
            question=self.single_question, label="Choice", weight=1.0
        )
        self.text_question = Question.objects.create(
            assessment=self.assessment,
            prompt="Describe your approach",
            question_type=Question.TYPE_TEXT,
            order=2,
        )
        candidate = CandidateProfile.objects.create(
            first_name="Casey", email="casey@example.com"
        )
        self.session = AssessmentSession.objects.create(
            candidate=candidate, assessment=self.assessment, status="invited"
        )

    def test_sequential_flow(self):
        start_url = reverse("candidate:session-start", args=[self.session.uuid])
        response = self.client.get(start_url)
        self.assertContains(response, "Pick one")
        post_data = {"response": str(self.choice.id)}
        response = self.client.post(start_url, data=post_data, follow=False)
        self.assertRedirects(response, start_url)
        self.session.refresh_from_db()
        self.assertEqual(self.session.responses.count(), 1)
        response = self.client.get(start_url)
        self.assertContains(response, "Describe your approach")
        response = self.client.post(start_url, data={"response": "Thoughtful"}, follow=False)
        self.assertRedirects(
            response, reverse("candidate:session-complete", args=[self.session.uuid])
        )
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, "completed")


class BehavioralCandidateFlowTests(TestCase):
    def setUp(self):
        category = RoleCategory.objects.create(name="Behaviors", slug="behaviors")
        self.assessment = Assessment.objects.create(
            category=category,
            title="Behavioral",
            slug="behavioral",
            summary="Summary",
        )
        self.behavioral_question = Question.objects.create(
            assessment=self.assessment,
            prompt="Behavioral inventory",
            question_type=Question.TYPE_BEHAVIORAL,
            order=1,
            metadata={"behavioral_bank": {"blocks": [1, 2]}},
        )
        candidate = CandidateProfile.objects.create(
            first_name="Avery", email="avery@example.com"
        )
        self.session = AssessmentSession.objects.create(
            candidate=candidate, assessment=self.assessment, status="invited"
        )

    def test_behavioral_blocks_progress_sequentially(self):
        start_url = reverse("candidate:session-start", args=[self.session.uuid])
        response = self.client.get(start_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["behavioral_block_index"], 1)
        block1 = get_behavioral_blocks([1])[0]
        self.client.post(
            start_url,
            data={"most_like": block1["statements"][0]["id"], "least_like": block1["statements"][1]["id"]},
        )
        self.session.refresh_from_db()
        response_record = self.session.responses.get(question=self.behavioral_question)
        self.assertEqual(len(json.loads(response_record.answer_text)), 2)
        progress_store = self.session.score_breakdown.get("behavioral_progress", {})
        self.assertIn(str(self.behavioral_question.id), progress_store)
        fresh = AssessmentSession.objects.get(pk=self.session.pk)
        stored = fresh.score_breakdown.get("behavioral_progress", {})
        self.assertIn(str(self.behavioral_question.id), stored)
        response = self.client.get(start_url)
        self.assertContains(response, "Set 2 of 2")
        block2 = get_behavioral_blocks([2])[0]
        response = self.client.post(
            start_url,
            data={"most_like": block2["statements"][0]["id"], "least_like": block2["statements"][1]["id"]},
        )
        self.assertRedirects(
            response, reverse("candidate:session-complete", args=[self.session.uuid])
        )
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, "completed")
        response_record.refresh_from_db()
        self.assertEqual(len(json.loads(response_record.answer_text)), 4)
