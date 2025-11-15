from rest_framework import serializers

from .models import DigitalMarketingAssessmentSession, DigitalMarketingQuestion


class AssessmentStartSerializer(serializers.Serializer):
    candidate_id = serializers.CharField(max_length=120)


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DigitalMarketingQuestion
        fields = [
            "id",
            "question_text",
            "question_type",
            "difficulty_level",
            "category",
            "options",
            "scoring_weight",
        ]


class CandidateResponseSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    answer = serializers.JSONField(required=False)
    selected = serializers.CharField(required=False)


class AssessmentResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = DigitalMarketingAssessmentSession
        fields = [
            "candidate_id",
            "hard_skill_score",
            "soft_skill_score",
            "overall_score",
            "category_breakdown",
            "recommendations",
        ]
