"""
Auto-advance hiring pipelines when assessment sessions are submitted.
Listens for post_save on all assessment session models and triggers
pipeline processing for the relevant candidate.
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
