"""
Auto-advance hiring pipelines when assessment sessions are submitted.
Listens for post_save on all assessment session models and triggers
pipeline processing for the relevant candidate.

Also syncs PipelineCandidate stage changes back to linked PositionApplication.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from marketing_assessments.models import DigitalMarketingAssessmentSession
from pm_assessments.models import ProductAssessmentSession
from behavioral_assessments.models import BehavioralAssessmentSession
from ux_assessments.models import UXDesignAssessmentSession
from hr_assessments.models import HRAssessmentSession
from finance_assessments.models import FinanceAssessmentSession

logger = logging.getLogger(__name__)

# Map pipeline stages → application statuses
_STAGE_TO_APP_STATUS = {
    'shortlisted': 'reviewed',
    'assessment_pending': 'assessment_sent',
    'assessment_sent': 'assessment_sent',
    'assessment_completed': 'assessment_sent',
    'decision_made': 'reviewed',
    'hired': 'hired',
    'rejected': 'rejected',
    'rejected_at_screen': 'rejected',
}

SESSION_MODELS = [
    DigitalMarketingAssessmentSession,
    ProductAssessmentSession,
    BehavioralAssessmentSession,
    UXDesignAssessmentSession,
    HRAssessmentSession,
    FinanceAssessmentSession,
]


@receiver(post_save, sender=DigitalMarketingAssessmentSession)
@receiver(post_save, sender=ProductAssessmentSession)
@receiver(post_save, sender=BehavioralAssessmentSession)
@receiver(post_save, sender=UXDesignAssessmentSession)
@receiver(post_save, sender=HRAssessmentSession)
@receiver(post_save, sender=FinanceAssessmentSession)
def on_assessment_submitted(sender, instance, **kwargs):
    """When an assessment session is submitted, advance the hiring pipeline."""
    if instance.status != 'submitted':
        return

    candidate_email = getattr(instance, 'candidate_id', None)
    if not candidate_email:
        return

    from .models import PipelineCandidate
    from .services import process_pipeline

    # Find pipeline candidates with this email in assessment_sent stage
    pipeline_candidates = PipelineCandidate.objects.filter(
        candidate__email=candidate_email,
        stage='assessment_sent',
    ).select_related('pipeline')

    for pc in pipeline_candidates:
        pipeline = pc.pipeline
        if pipeline.status != 'active':
            continue

        try:
            logger.info(
                'Assessment submitted for %s — auto-processing pipeline "%s"',
                candidate_email, pipeline.title,
            )
            process_pipeline(pipeline)
        except Exception:
            logger.exception(
                'Failed to auto-process pipeline %s after assessment submission',
                pipeline.id,
            )


# ---------------------------------------------------------------------------
# Sync PipelineCandidate stage → PositionApplication status
# ---------------------------------------------------------------------------

from .models import PipelineCandidate  # noqa: E402


@receiver(post_save, sender=PipelineCandidate)
def sync_application_status(sender, instance, **kwargs):
    """When a PipelineCandidate stage changes, update the linked PositionApplication."""
    new_status = _STAGE_TO_APP_STATUS.get(instance.stage)
    if not new_status:
        return

    # Check if this PipelineCandidate has a linked application (reverse OneToOne)
    try:
        app = instance.application
    except PipelineCandidate.application.RelatedObjectDoesNotExist:
        return

    if app.status != new_status:
        app.status = new_status
        app.save(update_fields=['status'])
