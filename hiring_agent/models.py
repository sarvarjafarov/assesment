import uuid

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class HiringPipeline(TimeStampedModel):
    SENIORITY_CHOICES = [
        ('junior', 'Junior'),
        ('mid', 'Mid-Level'),
        ('senior', 'Senior'),
        ('lead', 'Lead'),
        ('executive', 'Executive'),
    ]
    AUTOMATION_CHOICES = [
        ('recommend', 'Recommend (human approves all)'),
        ('semi_auto', 'Semi-Auto (auto-screen, human decides)'),
        ('full_auto', 'Full Auto (AI handles all)'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]

    client = models.ForeignKey(
        'clients.ClientAccount',
        related_name='hiring_pipelines',
        on_delete=models.CASCADE,
    )
    project = models.ForeignKey(
        'clients.ClientProject',
        related_name='hiring_pipelines',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=200)
    job_description = models.TextField()
    required_skills = models.JSONField(default=list, blank=True)
    preferred_skills = models.JSONField(default=list, blank=True)
    experience_range = models.CharField(max_length=50, blank=True)
    seniority_level = models.CharField(
        max_length=20,
        choices=SENIORITY_CHOICES,
        default='mid',
    )
    assessment_types = models.JSONField(
        default=list,
        blank=True,
        help_text='Assessment type codes to send, e.g. ["marketing", "behavioral"]',
    )
    automation_mode = models.CharField(
        max_length=20,
        choices=AUTOMATION_CHOICES,
        default='recommend',
    )
    screening_threshold = models.PositiveIntegerField(
        default=60,
        help_text='Minimum AI resume score (0-100) to shortlist a candidate',
    )
    passing_score = models.PositiveIntegerField(
        default=70,
        help_text='Minimum assessment score (0-100) to advance a candidate',
    )
    max_candidates = models.PositiveIntegerField(default=50)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
    )

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.title

    def candidate_count(self):
        return self.candidates.count()

    def candidates_by_stage(self):
        from django.db.models import Count
        return dict(
            self.candidates.values_list('stage')
            .annotate(count=Count('id'))
            .values_list('stage', 'count')
        )


class PipelineCandidate(TimeStampedModel):
    STAGE_CHOICES = [
        ('uploaded', 'Resume Uploaded'),
        ('screening', 'AI Screening'),
        ('shortlisted', 'Shortlisted'),
        ('rejected_at_screen', 'Rejected (Screening)'),
        ('assessment_pending', 'Assessment Pending'),
        ('assessment_sent', 'Assessment Sent'),
        ('assessment_completed', 'Assessment Completed'),
        ('decision_made', 'Decision Made'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    ]
    DECISION_CHOICES = [
        ('', 'Pending'),
        ('advance', 'Advance'),
        ('hold', 'Hold'),
        ('reject', 'Reject'),
    ]

    pipeline = models.ForeignKey(
        HiringPipeline,
        related_name='candidates',
        on_delete=models.CASCADE,
    )
    candidate = models.ForeignKey(
        'assessments.CandidateProfile',
        related_name='pipeline_entries',
        on_delete=models.PROTECT,
    )
    resume_file = models.FileField(upload_to='resumes/', blank=True)
    resume_text = models.TextField(blank=True)
    stage = models.CharField(
        max_length=30,
        choices=STAGE_CHOICES,
        default='uploaded',
    )

    # AI screening results
    ai_screen_score = models.PositiveIntegerField(null=True, blank=True)
    ai_screen_summary = models.TextField(blank=True)
    ai_screen_skills_matched = models.JSONField(default=list, blank=True)
    ai_screen_skills_missing = models.JSONField(default=list, blank=True)

    # AI final decision results
    ai_final_score = models.PositiveIntegerField(null=True, blank=True)
    ai_final_summary = models.TextField(blank=True)
    ai_final_recommendation = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        blank=True,
    )

    # Human decision
    human_decision = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        blank=True,
    )
    human_notes = models.TextField(blank=True)

    # Assessment tracking
    assessment_sessions = models.JSONField(
        default=list,
        blank=True,
        help_text='[{"type": "marketing", "session_uuid": "...", "score": null, "status": "invited"}]',
    )

    processed_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)
        unique_together = ('pipeline', 'candidate')

    def __str__(self):
        return f"{self.candidate} — {self.get_stage_display()}"

    @property
    def full_name(self):
        return str(self.candidate)

    @property
    def email(self):
        return self.candidate.email


class AgentActionLog(TimeStampedModel):
    ACTION_CHOICES = [
        ('resume_screen', 'Resume Screen'),
        ('assessment_select', 'Assessment Selection'),
        ('assessment_send', 'Assessment Send'),
        ('score_check', 'Score Check'),
        ('final_decision', 'Final Decision'),
    ]
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('error', 'Error'),
    ]

    pipeline = models.ForeignKey(
        HiringPipeline,
        related_name='action_logs',
        on_delete=models.CASCADE,
    )
    candidate = models.ForeignKey(
        PipelineCandidate,
        related_name='action_logs',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    input_data = models.JSONField(default=dict, blank=True)
    output_data = models.JSONField(default=dict, blank=True)
    ai_model = models.CharField(max_length=100, blank=True)
    tokens_used = models.PositiveIntegerField(default=0)
    duration_ms = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='success')
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.get_action_display()} — {self.status} ({self.created_at:%Y-%m-%d %H:%M})"
