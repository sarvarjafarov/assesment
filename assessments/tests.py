import json

from django.test import TestCase, override_settings
from django.urls import reverse

from assessments.behavioral import build_behavioral_profile
from assessments.constants import BEHAVIORAL_TRAITS
from assessments.models import (
    Assessment,
    AssessmentSession,
    CandidateProfile,
    Choice,
    CompanyProfile,
    PositionTask,
    Question,
    RoleCategory,
)
from assessments.services import invite_candidate, record_responses


class RecordResponsesEvaluationTests(TestCase):
    def setUp(self):
        category = RoleCategory.objects.create(name="Ops", slug="ops")
        self.assessment = Assessment.objects.create(
            category=category,
            title="Ops Readiness",
            slug="ops-readiness",
            summary="Test",
            scoring_rubric={"behavioral_weight_profile": "software_engineer"},
        )
        self.single_question = Question.objects.create(
            assessment=self.assessment,
            prompt="Primary KPI?",
            question_type=Question.TYPE_SINGLE,
            order=1,
        )
        self.good_choice = Choice.objects.create(
            question=self.single_question,
            label="Right",
            weight=1.0,
            value=json.dumps(
                {"statement_id": "1A", "response_type": "most_like_me"}
            ),
        )
        self.bad_choice = Choice.objects.create(
            question=self.single_question,
            label="Wrong",
            weight=0.0,
            value=json.dumps(
                {"statement_id": "1B", "response_type": "least_like_me"}
            ),
        )
        self.multi_question = Question.objects.create(
            assessment=self.assessment,
            prompt="Pick tools",
            question_type=Question.TYPE_MULTI,
            order=2,
        )
        self.multi_primary = Choice.objects.create(
            question=self.multi_question,
            label="Tool A",
            weight=0.6,
            value=json.dumps(
                {"statement_id": "2A", "response_type": "most_like_me"}
            ),
        )
        self.multi_secondary = Choice.objects.create(
            question=self.multi_question,
            label="Tool B",
            weight=0.4,
            value=json.dumps(
                {"statement_id": "2B", "response_type": "neutral"}
            ),
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

    def test_records_behavioral_profile(self):
        answers = [
            {"question_id": self.single_question.id, "choice_ids": [self.good_choice.id]},
            {"question_id": self.multi_question.id, "choice_ids": [self.multi_secondary.id]},
        ]
        record_responses(session=self.session, answers=answers)
        self.session.refresh_from_db()
        profile = self.session.score_breakdown.get("behavioral_profile")
        self.assertIsNotNone(profile)
        self.assertIn("focus_traits", profile)
        self.assertEqual(set(profile["focus_traits"]), set(BEHAVIORAL_TRAITS))
        self.assertEqual(profile["total_responses"], 2)
        self.assertIn("communication", profile["dominant_traits"])
        self.assertIn("eligibility", profile)
        self.assertIn("red_flags", profile)
        self.assertIn("raw_scores", profile)
        self.assertIsNotNone(profile["behavior_labels"]["communication"])
        self.assertIn(profile["eligibility"]["decision"], {"invite_to_interview", "consider_interview", "reject"})
        summary = profile.get("candidate_summary")
        self.assertIsNotNone(summary)
        self.assertTrue(summary["intro"].startswith("This report summarizes"))
        self.assertIn("communication", summary["traits"])
        self.assertIn("eligibility_message", summary)
        report = profile.get("red_flag_report")
        self.assertIsNotNone(report)
        self.assertIn(report["overall_risk_level"], {"low_risk", "moderate_risk", "high_risk"})
        self.assertIn("red_flags", report)
        self.assertIn("follow_up_questions", report)
        if report["red_flags"]:
            self.assertIn("trait", report["red_flags"][0])

    def test_behavioral_focus_limits_traits(self):
        self.session.behavioral_focus = ["communication"]
        self.session.save(update_fields=["behavioral_focus"])
        answers = [
            {"question_id": self.single_question.id, "choice_ids": [self.good_choice.id]},
            {"question_id": self.multi_question.id, "choice_ids": [self.multi_secondary.id]},
        ]
        record_responses(session=self.session, answers=answers)
        self.session.refresh_from_db()
        profile = self.session.score_breakdown.get("behavioral_profile")
        self.assertEqual(profile["focus_traits"], ["communication"])
        self.assertEqual(set(profile["trait_counts"].keys()), {"communication"})
        self.assertEqual(set(profile["behavior_labels"].keys()), {"communication"})


class BehavioralProfileBuilderTests(TestCase):
    def test_build_behavioral_profile_returns_rankings(self):
        profile = build_behavioral_profile(
            [
                {"statement_id": "1A", "response_type": "most_like_me"},
                {"statement_id": "1B", "response_type": "least_like_me"},
                {"statement_id": "4C", "response_type": "neutral"},
                {"statement_id": "7C", "response_type": "most_like_me"},
            ],
            weight_profile="software_engineer",
        )
        self.assertEqual(profile["total_responses"], 4)
        self.assertEqual(profile["trait_counts"]["communication"], 2)
        self.assertIn("trait_rankings", profile)
        self.assertTrue(profile["dominant_traits"])
        self.assertIn("eligibility", profile)
        self.assertIn("red_flags", profile)
        summary = profile.get("candidate_summary")
        self.assertIsNotNone(summary)
        self.assertIn("closing", summary)
        self.assertIn("communication", summary["traits"])
        report = profile.get("red_flag_report")
        self.assertIsNotNone(report)
        self.assertIn("overall_risk_level", report)
        self.assertIn("follow_up_questions", report)


class InviteCandidateWorkflowTests(TestCase):
    def setUp(self):
        category = RoleCategory.objects.create(name="Behavioral", slug="behavioral")
        self.assessment = Assessment.objects.create(
            category=category,
            title="Behavioral Core",
            slug="behavioral-core",
            summary="Behavioral",
        )
        self.company = CompanyProfile.objects.create(
            name="Atlas Labs",
            slug="atlas-labs",
            allowed_assessment_types=["behavioral"],
        )
        self.task = PositionTask.objects.create(
            company=self.company,
            title="Product Manager · Growth",
            slug="pm-growth",
            assessment_type="behavioral",
            assessment=self.assessment,
            status="active",
            behavioral_focus=["communication", "teamwork"],
        )

    def test_invite_links_company_and_task(self):
        result = invite_candidate(
            assessment=self.assessment,
            first_name="June",
            last_name="Rowe",
            email="june@example.com",
            invited_by="Tests",
            company=self.company,
            position_task=self.task,
        )
        session = result.session
        self.assertEqual(session.company, self.company)
        self.assertEqual(session.position_task, self.task)
        self.assertEqual(session.assessment, self.assessment)
        self.assertEqual(session.status, "invited")
        self.assertEqual(session.behavioral_focus, ["communication", "teamwork"])

    def test_follow_up_questions_attached_for_flags(self):
        profile = build_behavioral_profile(
            [
                {"statement_id": "4A", "response_type": "least_like_me"},
                {"statement_id": "7C", "response_type": "most_like_me"},
            ]
        )
        report = profile["red_flag_report"]
        self.assertTrue(report["red_flags"])
        follow_ups = report["follow_up_questions"]
        self.assertTrue(follow_ups)
        self.assertEqual(follow_ups[0]["code"], report["red_flags"][0]["code"])
        self.assertTrue(follow_ups[0]["questions"])

    def test_focus_selection_limits_traits(self):
        profile = build_behavioral_profile(
            [
                {"statement_id": "1A", "response_type": "most_like_me"},
                {"statement_id": "2A", "response_type": "least_like_me"},
                {"statement_id": "3C", "response_type": "most_like_me"},
            ],
            focus_traits=["communication", "teamwork"],
        )
        self.assertEqual(profile["focus_traits"], ["communication", "teamwork"])
        self.assertEqual(set(profile["trait_counts"].keys()), {"communication", "teamwork"})
        self.assertNotIn("adaptability", profile["behavior_labels"])


@override_settings(API_ACCESS_TOKEN="apitoken")
class SessionResponseApiViewTests(TestCase):
    def setUp(self):
        category = RoleCategory.objects.create(name="Ops", slug="ops")
        assessment = Assessment.objects.create(
            category=category,
            title="Ops Readiness",
            slug="ops-readiness",
            summary="Test",
        )
        question = Question.objects.create(
            assessment=assessment,
            prompt="Primary KPI?",
            question_type=Question.TYPE_SINGLE,
            order=1,
        )
        self.choice = Choice.objects.create(
            question=question,
            label="Right",
            weight=1.0,
            value=json.dumps({"statement_id": "1A", "response_type": "most_like_me"}),
        )
        candidate = CandidateProfile.objects.create(
            first_name="Ava", email="ava@example.com"
        )
        self.session = AssessmentSession.objects.create(
            candidate=candidate, assessment=assessment, status="invited"
        )

    def test_get_returns_behavioral_profile(self):
        record_responses(
            session=self.session,
            answers=[
                {
                    "question_id": self.choice.question_id,
                    "choice_ids": [self.choice.id],
                }
            ],
        )
        url = reverse("assessments:session-responses", args=[self.session.uuid])
        response = self.client.get(url, HTTP_X_API_KEY="apitoken")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["session_uuid"], str(self.session.uuid))
        self.assertIn("behavioral_profile", payload)
        self.assertIsNotNone(payload["behavioral_profile"])
        self.assertIn("score_breakdown", payload)
        self.assertIn("behavioral_focus", payload)
