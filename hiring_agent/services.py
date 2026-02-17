"""
Services for the AI Hiring Agent pipeline.
Handles resume parsing, AI screening, assessment integration, and orchestration.
"""
from __future__ import annotations

import io
import json
import logging
import time
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags

from .models import AgentActionLog, PipelineCandidate

if TYPE_CHECKING:
    from .models import HiringPipeline

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Resume parsing
# ---------------------------------------------------------------------------

def parse_resume(file_obj) -> str:
    """
    Extract text from a PDF or DOCX file object.
    Returns cleaned text string.
    """
    name = getattr(file_obj, 'name', '') or ''
    file_obj.seek(0)
    content = file_obj.read()

    if name.lower().endswith('.pdf'):
        return _parse_pdf(content)
    elif name.lower().endswith('.docx'):
        return _parse_docx(content)
    else:
        # Try PDF first, then DOCX, then raw text
        try:
            return _parse_pdf(content)
        except Exception:
            try:
                return _parse_docx(content)
            except Exception:
                return content.decode('utf-8', errors='ignore')


def _parse_pdf(content: bytes) -> str:
    from PyPDF2 import PdfReader
    try:
        reader = PdfReader(io.BytesIO(content))
    except Exception as exc:
        raise ValueError(f'Failed to read PDF: {exc}') from exc
    pages = []
    for page in reader.pages:
        try:
            text = page.extract_text()
        except Exception:
            continue
        if text:
            pages.append(text)
    return '\n'.join(pages).strip()


def _parse_docx(content: bytes) -> str:
    import docx
    doc = docx.Document(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return '\n'.join(paragraphs).strip()


def parse_resume_bytes(content: bytes, filename: str = '') -> str:
    """Extract text from raw resume bytes using the filename to detect format."""
    if not content:
        return ''
    fname = filename.lower()
    if fname.endswith('.pdf'):
        return _parse_pdf(content)
    elif fname.endswith('.docx'):
        return _parse_docx(content)
    # Unknown extension — try PDF then DOCX then raw text
    try:
        return _parse_pdf(content)
    except Exception:
        try:
            return _parse_docx(content)
        except Exception:
            return content.decode('utf-8', errors='ignore')


# ---------------------------------------------------------------------------
# Anthropic client helper
# ---------------------------------------------------------------------------

def _get_anthropic_client():
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        raise ValueError('ANTHROPIC_API_KEY not configured')
    import anthropic
    return anthropic.Anthropic(api_key=api_key)


def _get_model():
    return getattr(settings, 'ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences from Claude responses."""
    if text.startswith('```'):
        lines = text.split('\n')
        # Remove first line (```json) and last line (```)
        if len(lines) >= 3:
            text = '\n'.join(lines[1:-1])
        elif len(lines) == 2:
            text = lines[1]
    return text.strip()


def _call_claude(prompt: str, max_tokens: int = 2048) -> dict:
    """Call Claude and return parsed JSON response + usage metadata."""
    client = _get_anthropic_client()
    model = _get_model()
    start = time.time()

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{'role': 'user', 'content': prompt}],
        timeout=60.0,
    )

    duration_ms = int((time.time() - start) * 1000)

    if not response.content:
        raise ValueError('Empty response from Claude API')
    text = response.content[0].text.strip()
    text = _strip_code_fences(text)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f'Failed to parse Claude response as JSON: {exc}') from exc

    return {
        'data': parsed,
        'model': model,
        'tokens': response.usage.input_tokens + response.usage.output_tokens,
        'duration_ms': duration_ms,
    }


# ---------------------------------------------------------------------------
# AI Resume Screening
# ---------------------------------------------------------------------------

def screen_resume(pipeline_candidate: PipelineCandidate) -> dict:
    """
    Screen a candidate's resume using Claude AI.
    Updates the PipelineCandidate with screening results.
    Returns the AI response data.
    """
    pipeline = pipeline_candidate.pipeline
    resume_text = pipeline_candidate.resume_text

    if not resume_text:
        raise ValueError('No resume text available for screening')

    prompt = f"""You are an expert recruiter screening resumes for the following position:

Job Title: {pipeline.title}
Job Description: {pipeline.job_description}
Required Skills: {', '.join(pipeline.required_skills or [])}
Preferred Skills: {', '.join(pipeline.preferred_skills or [])}
Experience Required: {pipeline.experience_range}
Seniority Level: {pipeline.get_seniority_level_display()}

Candidate Resume:
{resume_text[:8000]}

Evaluate this candidate and return ONLY a valid JSON object (no markdown, no extra text):
{{
  "score": <0-100 integer>,
  "summary": "<2-3 sentence evaluation>",
  "skills_matched": ["skill1", "skill2"],
  "skills_missing": ["skill3"],
  "experience_years_estimated": <number>,
  "recommendation": "advance" or "hold" or "reject"
}}"""

    try:
        result = _call_claude(prompt)
        data = result['data']

        pipeline_candidate.ai_screen_score = int(data.get('score', 0))
        pipeline_candidate.ai_screen_summary = data.get('summary', '')
        pipeline_candidate.ai_screen_skills_matched = data.get('skills_matched', [])
        pipeline_candidate.ai_screen_skills_missing = data.get('skills_missing', [])
        pipeline_candidate.processed_at = timezone.now()

        # Determine stage based on score vs threshold
        if pipeline_candidate.ai_screen_score >= pipeline.screening_threshold:
            pipeline_candidate.stage = 'shortlisted'
        else:
            pipeline_candidate.stage = 'rejected_at_screen'

        pipeline_candidate.save(update_fields=[
            'ai_screen_score', 'ai_screen_summary',
            'ai_screen_skills_matched', 'ai_screen_skills_missing',
            'stage', 'processed_at', 'updated_at',
        ])

        AgentActionLog.objects.create(
            pipeline=pipeline,
            candidate=pipeline_candidate,
            action='resume_screen',
            input_data={'resume_length': len(resume_text)},
            output_data=data,
            ai_model=result['model'],
            tokens_used=result['tokens'],
            duration_ms=result['duration_ms'],
            status='success',
        )

        return data

    except Exception as exc:
        AgentActionLog.objects.create(
            pipeline=pipeline,
            candidate=pipeline_candidate,
            action='resume_screen',
            input_data={'resume_length': len(resume_text)},
            output_data={},
            status='error',
            error_message=str(exc)[:2000],
        )
        raise


# ---------------------------------------------------------------------------
# Assessment Integration
# ---------------------------------------------------------------------------

# Map assessment type codes → (session model, question set generator)
def _get_assessment_config():
    from marketing_assessments.models import DigitalMarketingAssessmentSession
    from marketing_assessments.services import generate_question_set as gen_marketing
    from pm_assessments.models import ProductAssessmentSession
    from pm_assessments.services import generate_question_set as gen_pm
    from behavioral_assessments.models import BehavioralAssessmentSession
    from behavioral_assessments.services import generate_question_set as gen_behavioral
    from ux_assessments.models import UXDesignAssessmentSession
    from ux_assessments.services import generate_question_set as gen_ux
    from hr_assessments.models import HRAssessmentSession
    from hr_assessments.services import generate_question_set as gen_hr
    from finance_assessments.models import FinanceAssessmentSession
    from finance_assessments.services import generate_question_set as gen_finance

    return {
        'marketing': (DigitalMarketingAssessmentSession, gen_marketing),
        'product': (ProductAssessmentSession, gen_pm),
        'behavioral': (BehavioralAssessmentSession, gen_behavioral),
        'ux_design': (UXDesignAssessmentSession, gen_ux),
        'hr': (HRAssessmentSession, gen_hr),
        'finance': (FinanceAssessmentSession, gen_finance),
    }


def _seniority_to_level(seniority: str) -> str:
    """Map pipeline seniority to assessment level."""
    mapping = {
        'junior': 'junior',
        'mid': 'mid',
        'senior': 'senior',
        'lead': 'senior',
        'executive': 'senior',
    }
    return mapping.get(seniority, 'mid')


def _get_candidate_route():
    """Map assessment type codes to candidate-facing URL route names."""
    return {
        'marketing': 'candidate:marketing-session',
        'product': 'candidate:pm-session',
        'behavioral': 'candidate:behavioral-session',
        'ux_design': 'candidate:ux-session',
        'hr': 'candidate:hr-session',
        'finance': 'candidate:finance-session',
    }


def _get_assessment_labels():
    """Map assessment type codes to human-readable labels."""
    return {
        'marketing': 'Digital Marketing Assessment',
        'product': 'Product Management Assessment',
        'behavioral': 'Behavioral Assessment',
        'ux_design': 'UX Design Assessment',
        'hr': 'HR Assessment',
        'finance': 'Finance Assessment',
    }


def _send_candidate_assessment_email(
    candidate_email: str,
    candidate_first_name: str,
    company_name: str,
    session,
    assessment_label: str,
    route_name: str,
    client=None,
):
    """Send an assessment invite email to the candidate."""
    if not getattr(settings, 'EMAIL_ENABLED', True):
        logger.info('EMAIL_ENABLED is False. Skipping invite to %s for %s.', candidate_email, assessment_label)
        return
    site_url = getattr(settings, 'SITE_URL', 'https://www.evalon.tech')
    start_link = site_url.rstrip('/') + reverse(route_name, args=[session.uuid])

    context = {
        'company_name': company_name,
        'invited_by': company_name,
        'candidate': {'first_name': candidate_first_name},
        'assessment': {'title': assessment_label},
        'start_link': start_link,
        'session_link': start_link,
        'due_at': None,
        'notes': '',
    }
    # Add client branding if available
    if client:
        context['brand_primary'] = client.brand_primary_color or '#ff8a00'
        context['brand_secondary'] = client.brand_secondary_color or '#0e1428'
        context['hide_evalon_branding'] = client.hide_evalon_branding
        context['client_footer_text'] = client.get_footer_text()
    subject = f'{company_name} invited you to the {assessment_label}'
    html_body = render_to_string('emails/invite_candidate.html', context)
    text_body = strip_tags(html_body)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[candidate_email],
    )
    email.attach_alternative(html_body, 'text/html')
    email.send()
    logger.info('Assessment invite sent to %s for %s', candidate_email, assessment_label)


def send_assessments(pipeline_candidate: PipelineCandidate) -> list[dict]:
    """
    Send all configured assessment types to the candidate.
    Creates session objects, emails the candidate, and tracks in assessment_sessions JSON.
    Returns list of created session info dicts.
    """
    pipeline = pipeline_candidate.pipeline
    client = pipeline.client
    assessment_types = pipeline.assessment_types or []
    level = _seniority_to_level(pipeline.seniority_level)
    candidate_email = pipeline_candidate.candidate.email
    candidate_first_name = pipeline_candidate.candidate.first_name or 'Candidate'
    config = _get_assessment_config()
    routes = _get_candidate_route()
    labels = _get_assessment_labels()
    sessions_created = []

    for atype in assessment_types:
        if atype not in config:
            logger.warning('Unknown assessment type: %s', atype)
            continue

        SessionModel, gen_questions = config[atype]

        # Create or retrieve session (atomic to prevent duplicates)
        with transaction.atomic():
            session, created = SessionModel.objects.get_or_create(
                candidate_id=candidate_email,
                client=client,
                defaults={'status': 'draft'},
            )

            if created or session.status == 'draft':
                session.question_set = gen_questions(level=level)
                session.status = 'in_progress'
                session.level = level
                session.save(update_fields=[
                    'question_set', 'status', 'level', 'updated_at',
                ])

        # Email the candidate their assessment link
        email_sent = False
        route_name = routes.get(atype)
        if route_name and created:
            try:
                _send_candidate_assessment_email(
                    candidate_email=candidate_email,
                    candidate_first_name=candidate_first_name,
                    company_name=client.company_name,
                    session=session,
                    assessment_label=labels.get(atype, atype),
                    route_name=route_name,
                    client=client,
                )
                email_sent = True
            except Exception as exc:
                logger.error(
                    'Failed to email assessment invite to %s for %s: %s',
                    candidate_email, atype, exc,
                )

        sessions_created.append({
            'type': atype,
            'session_uuid': str(session.uuid),
            'score': None,
            'status': session.status,
            'email_sent': email_sent,
        })

    pipeline_candidate.assessment_sessions = sessions_created
    pipeline_candidate.stage = 'assessment_sent'
    pipeline_candidate.save(update_fields=[
        'assessment_sessions', 'stage', 'updated_at',
    ])

    AgentActionLog.objects.create(
        pipeline=pipeline,
        candidate=pipeline_candidate,
        action='assessment_send',
        input_data={'types': assessment_types, 'candidate_email': candidate_email},
        output_data={'sessions': sessions_created},
        status='success',
    )

    return sessions_created


def check_results(pipeline_candidate: PipelineCandidate) -> dict:
    """
    Check assessment completion status and scores for a candidate.
    Returns dict with overall status and per-assessment results.
    """
    config = _get_assessment_config()
    sessions = pipeline_candidate.assessment_sessions or []
    all_complete = True
    total_score = 0
    scored_count = 0
    updated_sessions = []

    for s in sessions:
        atype = s['type']
        session_uuid = s['session_uuid']
        SessionModel = config.get(atype, (None,))[0]

        if SessionModel is None:
            updated_sessions.append(s)
            continue

        try:
            session = SessionModel.objects.get(uuid=session_uuid)
        except SessionModel.DoesNotExist:
            updated_sessions.append(s)
            continue

        s['status'] = session.status

        # Get score — different models use different field names
        score = None
        if hasattr(session, 'overall_score') and session.overall_score is not None:
            score = float(session.overall_score)
        elif hasattr(session, 'eligibility_score') and session.eligibility_score is not None:
            score = float(session.eligibility_score)

        if score is not None:
            s['score'] = score
            total_score += score
            scored_count += 1

        if session.status != 'submitted':
            all_complete = False

        updated_sessions.append(s)

    pipeline_candidate.assessment_sessions = updated_sessions

    if all_complete and scored_count > 0:
        pipeline_candidate.stage = 'assessment_completed'

    pipeline_candidate.save(update_fields=[
        'assessment_sessions', 'stage', 'updated_at',
    ])

    avg_score = total_score / scored_count if scored_count > 0 else None

    return {
        'all_complete': all_complete,
        'average_score': avg_score,
        'scored_count': scored_count,
        'sessions': updated_sessions,
    }


# ---------------------------------------------------------------------------
# AI Final Decision
# ---------------------------------------------------------------------------

def make_final_decision(pipeline_candidate: PipelineCandidate) -> dict:
    """
    Use Claude to make a final hiring recommendation based on
    resume screening + assessment results.
    """
    pipeline = pipeline_candidate.pipeline
    candidate = pipeline_candidate.candidate

    # Format assessment results
    results_lines = []
    for s in pipeline_candidate.assessment_sessions or []:
        score_str = f"{s['score']:.0f}/100" if s.get('score') is not None else 'N/A'
        results_lines.append(f"- {s['type'].replace('_', ' ').title()}: {score_str} ({s.get('status', 'unknown')})")
    assessment_results = '\n'.join(results_lines) or 'No assessment results available.'

    prompt = f"""You are a senior hiring manager making a final hiring decision.

Position: {pipeline.title} ({pipeline.get_seniority_level_display()})
Job Description: {pipeline.job_description}

Candidate Summary:
- Name: {candidate.first_name} {candidate.last_name}
- Resume Screen Score: {pipeline_candidate.ai_screen_score or 'N/A'}/100
- Resume Summary: {pipeline_candidate.ai_screen_summary or 'N/A'}
- Skills Matched: {', '.join(pipeline_candidate.ai_screen_skills_matched or [])}
- Skills Missing: {', '.join(pipeline_candidate.ai_screen_skills_missing or [])}

Assessment Results:
{assessment_results}

Based on ALL data, provide your hiring recommendation as ONLY a valid JSON object (no markdown, no extra text):
{{
  "score": <0-100 integer>,
  "recommendation": "advance" or "hold" or "reject",
  "summary": "<3-4 sentence reasoning>",
  "strengths": ["strength1", "strength2"],
  "concerns": ["concern1"]
}}"""

    try:
        result = _call_claude(prompt)
        data = result['data']

        pipeline_candidate.ai_final_score = int(data.get('score', 0))
        pipeline_candidate.ai_final_summary = data.get('summary', '')
        pipeline_candidate.ai_final_recommendation = data.get('recommendation', 'hold')
        pipeline_candidate.stage = 'decision_made'
        pipeline_candidate.processed_at = timezone.now()
        pipeline_candidate.save(update_fields=[
            'ai_final_score', 'ai_final_summary',
            'ai_final_recommendation', 'stage',
            'processed_at', 'updated_at',
        ])

        AgentActionLog.objects.create(
            pipeline=pipeline,
            candidate=pipeline_candidate,
            action='final_decision',
            input_data={
                'screen_score': pipeline_candidate.ai_screen_score,
                'assessment_sessions': pipeline_candidate.assessment_sessions,
            },
            output_data=data,
            ai_model=result['model'],
            tokens_used=result['tokens'],
            duration_ms=result['duration_ms'],
            status='success',
        )

        return data

    except Exception as exc:
        AgentActionLog.objects.create(
            pipeline=pipeline,
            candidate=pipeline_candidate,
            action='final_decision',
            input_data={},
            output_data={},
            status='error',
            error_message=str(exc)[:2000],
        )
        raise


# ---------------------------------------------------------------------------
# Pipeline Orchestrator (state machine)
# ---------------------------------------------------------------------------

def process_pipeline(pipeline: "HiringPipeline") -> dict:
    """
    Process all candidates in a pipeline through the state machine.
    Idempotent — safe to call repeatedly.

    Returns summary dict with counts of actions taken.
    """
    if pipeline.status != 'active':
        return {'skipped': True, 'reason': f'Pipeline status is {pipeline.status}'}

    mode = pipeline.automation_mode
    stats = {
        'screened': 0,
        'shortlisted': 0,
        'rejected_at_screen': 0,
        'assessments_sent': 0,
        'results_checked': 0,
        'decisions_made': 0,
        'finalized': 0,
        'errors': 0,
    }

    candidates = pipeline.candidates.select_related('pipeline', 'candidate').all()

    for pc in candidates:
        try:
            _advance_candidate(pc, pipeline, mode, stats)
        except Exception as exc:
            logger.error(
                'Error processing candidate %s in pipeline %s: %s',
                pc.id, pipeline.id, exc,
            )
            stats['errors'] += 1

    # Send notifications
    if stats['shortlisted'] > 0:
        try:
            notify_shortlist_ready(pipeline, stats['shortlisted'])
        except Exception:
            logger.exception('Failed to send shortlist notification')

    if stats['assessments_sent'] > 0:
        try:
            notify_assessments_sent(pipeline, stats['assessments_sent'])
        except Exception:
            logger.exception('Failed to send assessment notification')

    if stats['decisions_made'] > 0:
        try:
            notify_decision_ready(pipeline, stats['decisions_made'])
        except Exception:
            logger.exception('Failed to send decision notification')

    return stats


def _advance_candidate(
    pc: PipelineCandidate,
    pipeline: "HiringPipeline",
    mode: str,
    stats: dict,
) -> None:
    """Advance a single candidate through the state machine."""

    # Stage: uploaded → screen resume
    if pc.stage == 'uploaded':
        # Clear any stale human decisions from previous runs
        if pc.human_decision:
            pc.human_decision = ''
            pc.human_notes = ''
            pc.save(update_fields=['human_decision', 'human_notes', 'updated_at'])
        screen_resume(pc)
        stats['screened'] += 1
        if pc.stage == 'shortlisted':
            stats['shortlisted'] += 1
        elif pc.stage == 'rejected_at_screen':
            stats['rejected_at_screen'] += 1

    # Stage: shortlisted → send assessments (if auto or human approved)
    if pc.stage == 'shortlisted':
        can_proceed = (
            mode in ('semi_auto', 'full_auto')
            or pc.human_decision == 'advance'
        )
        if can_proceed:
            pc.stage = 'assessment_pending'
            pc.save(update_fields=['stage', 'updated_at'])

    # Stage: assessment_pending → send assessments
    if pc.stage == 'assessment_pending':
        send_assessments(pc)
        stats['assessments_sent'] += 1

    # Stage: assessment_sent → check results
    if pc.stage == 'assessment_sent':
        check_results(pc)
        stats['results_checked'] += 1

    # Stage: assessment_completed → make final decision
    if pc.stage == 'assessment_completed':
        make_final_decision(pc)
        stats['decisions_made'] += 1

    # Stage: decision_made → finalize (if auto or human approved)
    if pc.stage == 'decision_made':
        can_finalize = (
            mode == 'full_auto'
            or pc.human_decision in ('advance', 'reject')
        )
        if can_finalize:
            # In full_auto mode, always use the AI recommendation.
            # In recommend/semi_auto modes, the human decision takes priority.
            if mode == 'full_auto':
                recommendation = pc.ai_final_recommendation
            else:
                recommendation = pc.human_decision or pc.ai_final_recommendation

            if recommendation == 'advance':
                pc.stage = 'hired'
            elif recommendation == 'reject':
                pc.stage = 'rejected'
            else:
                # 'hold' — stay at decision_made, but still record the timestamp
                # so the candidate isn't re-processed indefinitely
                if not pc.decided_at:
                    pc.decided_at = timezone.now()
                    pc.save(update_fields=['decided_at', 'updated_at'])
                return

            pc.decided_at = timezone.now()
            pc.save(update_fields=['stage', 'decided_at', 'updated_at'])
            stats['finalized'] += 1


# ---------------------------------------------------------------------------
# Email Notifications
# ---------------------------------------------------------------------------

def _send_pipeline_email(client, subject: str, html_body: str):
    """Send an email to the client account owner."""
    text_body = strip_tags(html_body)
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[client.email],
    )
    email.attach_alternative(html_body, 'text/html')
    try:
        email.send()
    except Exception as exc:
        logger.error('Failed to send pipeline email to %s: %s', client.email, exc)


def notify_shortlist_ready(pipeline: "HiringPipeline", count: int):
    """Notify client that candidates have been shortlisted and need review."""
    site_url = getattr(settings, 'SITE_URL', 'https://www.evalon.tech')
    detail_url = site_url.rstrip('/') + reverse(
        'hiring_agent:pipeline-detail', kwargs={'pipeline_uuid': pipeline.uuid}
    )
    html_body = render_to_string('emails/hiring_agent/shortlist_ready.html', {
        'pipeline': pipeline,
        'client': pipeline.client,
        'count': count,
        'detail_url': detail_url,
    })
    _send_pipeline_email(
        pipeline.client,
        f'{count} candidate(s) shortlisted for {pipeline.title} — Evalon',
        html_body,
    )

    # In-app notification
    try:
        from clients.services import create_notification

        link_url = reverse(
            'hiring_agent:pipeline-detail',
            kwargs={'pipeline_uuid': pipeline.uuid},
        )
        create_notification(
            client=pipeline.client,
            category="pipeline_update",
            title="Shortlist Ready",
            message=(
                f"{count} candidate(s) have been shortlisted "
                f"for {pipeline.title}."
            ),
            link_url=link_url,
        )
    except Exception:
        logger.exception('Failed to create shortlist ready notification')


def notify_assessments_sent(pipeline: "HiringPipeline", count: int):
    """Notify client that assessments have been sent to candidates."""
    site_url = getattr(settings, 'SITE_URL', 'https://www.evalon.tech')
    detail_url = site_url.rstrip('/') + reverse(
        'hiring_agent:pipeline-detail', kwargs={'pipeline_uuid': pipeline.uuid}
    )
    html_body = render_to_string('emails/hiring_agent/assessments_sent.html', {
        'pipeline': pipeline,
        'client': pipeline.client,
        'count': count,
        'detail_url': detail_url,
    })
    _send_pipeline_email(
        pipeline.client,
        f'Assessments sent to {count} candidate(s) for {pipeline.title} — Evalon',
        html_body,
    )

    # In-app notification
    try:
        from clients.services import create_notification

        link_url = reverse(
            'hiring_agent:pipeline-detail',
            kwargs={'pipeline_uuid': pipeline.uuid},
        )
        create_notification(
            client=pipeline.client,
            category="pipeline_update",
            title="Assessments Sent",
            message=(
                f"Assessments have been sent to {count} candidate(s) "
                f"for {pipeline.title}."
            ),
            link_url=link_url,
        )
    except Exception:
        logger.exception('Failed to create assessments sent notification')


def notify_decision_ready(pipeline: "HiringPipeline", count: int):
    """Notify client that AI final decisions are ready for review."""
    site_url = getattr(settings, 'SITE_URL', 'https://www.evalon.tech')
    detail_url = site_url.rstrip('/') + reverse(
        'hiring_agent:pipeline-detail', kwargs={'pipeline_uuid': pipeline.uuid}
    )
    html_body = render_to_string('emails/hiring_agent/decision_ready.html', {
        'pipeline': pipeline,
        'client': pipeline.client,
        'count': count,
        'detail_url': detail_url,
    })
    _send_pipeline_email(
        pipeline.client,
        f'{count} hiring decision(s) ready for {pipeline.title} — Evalon',
        html_body,
    )

    # In-app notification
    try:
        from clients.services import create_notification

        link_url = reverse(
            'hiring_agent:pipeline-detail',
            kwargs={'pipeline_uuid': pipeline.uuid},
        )
        create_notification(
            client=pipeline.client,
            category="decision_recorded",
            title="Decisions Ready",
            message=(
                f"{count} hiring decision(s) are ready for review "
                f"for {pipeline.title}."
            ),
            link_url=link_url,
        )
    except Exception:
        logger.exception('Failed to create decision ready notification')
