from __future__ import annotations

import logging
import os
import re

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from assessments.models import CandidateProfile
from .forms import CandidateReviewForm, HiringPipelineForm, ResumeUploadForm
from .models import AgentActionLog, HiringPipeline, PipelineCandidate
from .services import parse_resume, process_pipeline

logger = logging.getLogger(__name__)


class HiringAgentMixin(LoginRequiredMixin):
    """Base mixin for all hiring agent views. Ensures client account access."""
    login_url = reverse_lazy('clients:login')

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'client_account'):
            return redirect('clients:login')
        self.account = request.user.client_account
        if self.account.status != 'approved':
            return redirect('clients:pending_approval')
        if not self.account.can_use_ai_hiring:
            return redirect('hiring_agent:upgrade')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['account'] = self.account
        return ctx


class PipelineMixin(HiringAgentMixin):
    """Mixin that resolves the pipeline from the URL."""

    def get_pipeline(self):
        if not hasattr(self, '_pipeline'):
            self._pipeline = get_object_or_404(
                HiringPipeline,
                uuid=self.kwargs['pipeline_uuid'],
                client=self.account,
            )
        return self._pipeline

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pipeline'] = self.get_pipeline()
        return ctx


# ---------------------------------------------------------------------------
# Pipeline CRUD
# ---------------------------------------------------------------------------

class PipelineListView(HiringAgentMixin, TemplateView):
    template_name = 'hiring_agent/pipeline_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pipelines'] = HiringPipeline.objects.filter(
            client=self.account
        ).select_related('project')
        return ctx


class PipelineCreateView(HiringAgentMixin, TemplateView):
    template_name = 'hiring_agent/pipeline_create.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = HiringPipelineForm(client=self.account)
        return ctx

    def post(self, request, *args, **kwargs):
        form = HiringPipelineForm(request.POST, client=self.account)
        if form.is_valid():
            pipeline = form.save()
            messages.success(request, f'Pipeline "{pipeline.title}" created.')
            return redirect('hiring_agent:pipeline-detail', pipeline_uuid=pipeline.uuid)
        return self.render_to_response(self.get_context_data(form=form))


class PipelineEditView(PipelineMixin, TemplateView):
    template_name = 'hiring_agent/pipeline_create.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pipeline = self.get_pipeline()
        ctx['form'] = kwargs.get('form') or HiringPipelineForm(
            instance=pipeline, client=self.account,
        )
        ctx['is_edit'] = True
        return ctx

    def post(self, request, *args, **kwargs):
        pipeline = self.get_pipeline()
        form = HiringPipelineForm(
            request.POST, instance=pipeline, client=self.account,
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Pipeline updated.')
            return redirect('hiring_agent:pipeline-detail', pipeline_uuid=pipeline.uuid)
        return self.render_to_response(self.get_context_data(form=form))


class PipelineDetailView(PipelineMixin, TemplateView):
    template_name = 'hiring_agent/pipeline_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pipeline = self.get_pipeline()
        candidates = pipeline.candidates.select_related('candidate').order_by('-created_at')

        # Group candidates by stage
        stage_groups = {}
        for stage_code, stage_label in PipelineCandidate.STAGE_CHOICES:
            stage_groups[stage_code] = {
                'label': stage_label,
                'candidates': [],
                'count': 0,
            }

        for c in candidates:
            if c.stage in stage_groups:
                stage_groups[c.stage]['candidates'].append(c)
                stage_groups[c.stage]['count'] += 1

        ctx['candidates'] = candidates
        ctx['stage_groups'] = stage_groups
        ctx['total_candidates'] = candidates.count()
        ctx['upload_form'] = ResumeUploadForm()
        return ctx


# ---------------------------------------------------------------------------
# Resume Upload
# ---------------------------------------------------------------------------

class ResumeUploadView(HiringAgentMixin, View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        pipeline = get_object_or_404(
            HiringPipeline, uuid=kwargs.get('pipeline_uuid'), client=self.account,
        )
        files = request.FILES.getlist('resumes')

        if not files:
            messages.error(request, 'No files selected.')
            return redirect('hiring_agent:pipeline-detail', pipeline_uuid=pipeline.uuid)

        uploaded = 0
        errors = 0
        max_resume_size = 10 * 1024 * 1024  # 10 MB

        for f in files:
            # Check file size before processing
            if f.size > max_resume_size:
                errors += 1
                continue

            name = f.name.lower()
            if not (name.endswith('.pdf') or name.endswith('.docx')):
                errors += 1
                continue

            # Validate magic bytes
            header = f.read(4)
            f.seek(0)
            if name.endswith('.pdf') and not header.startswith(b'%PDF'):
                errors += 1
                continue
            if name.endswith('.docx') and not header.startswith(b'PK'):
                errors += 1
                continue

            try:
                resume_text = parse_resume(f)
                if not resume_text.strip():
                    errors += 1
                    continue

                # Extract email from resume text
                email_match = re.search(
                    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
                    resume_text,
                )
                if not email_match:
                    messages.warning(
                        request,
                        f'No email found in {f.name} — skipped.',
                    )
                    errors += 1
                    continue
                candidate_email = email_match.group(0).lower()

                # Extract name from filename as fallback
                base_name = f.name.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
                parts = base_name.split()
                first_name = parts[0].title() if parts else 'Candidate'
                last_name = ' '.join(parts[1:]).title() if len(parts) > 1 else ''
                candidate, _ = CandidateProfile.objects.get_or_create(
                    email=candidate_email,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                    },
                )

                # Create pipeline candidate entry
                f.seek(0)
                pc, created = PipelineCandidate.objects.get_or_create(
                    pipeline=pipeline,
                    candidate=candidate,
                    defaults={
                        'resume_text': resume_text,
                        'stage': 'uploaded',
                    },
                )
                if created:
                    safe_name = os.path.basename(f.name)
                    pc.resume_file.save(safe_name, f, save=True)
                    uploaded += 1
                else:
                    # Update resume if candidate already exists
                    safe_name = os.path.basename(f.name)
                    pc.resume_text = resume_text
                    pc.resume_file.save(safe_name, f, save=False)
                    pc.stage = 'uploaded'
                    pc.save(update_fields=['resume_text', 'resume_file', 'stage', 'updated_at'])
                    uploaded += 1

            except Exception as exc:
                logger.error('Failed to process resume %s: %s', f.name, exc)
                errors += 1

        msg = f'{uploaded} resume(s) uploaded successfully.'
        if errors:
            msg += f' {errors} file(s) failed.'
        messages.success(request, msg)
        return redirect('hiring_agent:pipeline-detail', pipeline_uuid=pipeline.uuid)


# ---------------------------------------------------------------------------
# Pipeline Actions
# ---------------------------------------------------------------------------

class TriggerProcessView(HiringAgentMixin, View):
    """Trigger AI processing for all candidates in the pipeline."""
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        pipeline = get_object_or_404(
            HiringPipeline, uuid=kwargs.get('pipeline_uuid'), client=self.account,
        )
        if pipeline.status == 'draft':
            pipeline.status = 'active'
            pipeline.save(update_fields=['status', 'updated_at'])

        try:
            stats = process_pipeline(pipeline)
            if stats.get('skipped'):
                messages.warning(request, f'Pipeline skipped: {stats["reason"]}')
            else:
                msg_parts = []
                if stats['screened']:
                    msg_parts.append(f"{stats['screened']} screened")
                if stats['assessments_sent']:
                    msg_parts.append(f"{stats['assessments_sent']} assessments sent")
                if stats['decisions_made']:
                    msg_parts.append(f"{stats['decisions_made']} decisions made")
                if stats['errors']:
                    msg_parts.append(f"{stats['errors']} errors")
                messages.success(
                    request,
                    'Pipeline processed: ' + ', '.join(msg_parts) if msg_parts else 'No actions needed.'
                )
        except Exception as exc:
            messages.error(request, f'Processing error: {exc}')

        return redirect('hiring_agent:pipeline-detail', pipeline_uuid=pipeline.uuid)


class PipelinePauseView(HiringAgentMixin, View):
    """Toggle pipeline between active and paused."""
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        pipeline = get_object_or_404(
            HiringPipeline, uuid=kwargs.get('pipeline_uuid'), client=self.account,
        )
        if pipeline.status == 'active':
            pipeline.status = 'paused'
            messages.info(request, 'Pipeline paused.')
        elif pipeline.status in ('paused', 'draft'):
            pipeline.status = 'active'
            messages.success(request, 'Pipeline activated.')
        pipeline.save(update_fields=['status', 'updated_at'])
        return redirect('hiring_agent:pipeline-detail', pipeline_uuid=pipeline.uuid)


# ---------------------------------------------------------------------------
# Candidate Detail & Review
# ---------------------------------------------------------------------------

class CandidateDetailView(PipelineMixin, TemplateView):
    template_name = 'hiring_agent/candidate_detail.html'

    def get_pipeline_candidate(self):
        if not hasattr(self, '_pipeline_candidate'):
            self._pipeline_candidate = get_object_or_404(
                PipelineCandidate, pk=self.kwargs['pk'], pipeline=self.get_pipeline(),
            )
        return self._pipeline_candidate

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pc = self.get_pipeline_candidate()
        ctx['pc'] = pc
        ctx['review_form'] = CandidateReviewForm()
        ctx['action_logs'] = AgentActionLog.objects.filter(
            candidate=pc,
        ).order_by('-created_at')[:20]
        return ctx


class CandidateReviewView(HiringAgentMixin, View):
    """Handle human review decisions for a candidate."""
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        pipeline = get_object_or_404(
            HiringPipeline, uuid=kwargs.get('pipeline_uuid'), client=self.account,
        )
        pc = get_object_or_404(
            PipelineCandidate, pk=kwargs.get('pk'), pipeline=pipeline,
        )
        form = CandidateReviewForm(request.POST)
        if form.is_valid():
            pc.human_decision = form.cleaned_data['decision']
            pc.human_notes = form.cleaned_data.get('notes', '')
            pc.save(update_fields=['human_decision', 'human_notes', 'updated_at'])
            messages.success(
                request,
                f'Decision recorded: {form.cleaned_data["decision"].title()}'
            )
        else:
            messages.error(request, 'Invalid form submission.')

        return redirect(
            'hiring_agent:candidate-detail',
            pipeline_uuid=pipeline.uuid,
            pk=pc.pk,
        )


# ---------------------------------------------------------------------------
# Pipeline Stats (JSON endpoint)
# ---------------------------------------------------------------------------

class UpgradeView(LoginRequiredMixin, TemplateView):
    """Show upgrade page for non-enterprise users trying to access AI Hiring."""
    template_name = 'hiring_agent/upgrade.html'
    login_url = reverse_lazy('clients:login')

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'client_account'):
            return redirect('clients:login')
        # If user already has enterprise, redirect to pipeline list
        if request.user.client_account.can_use_ai_hiring:
            return redirect('hiring_agent:pipeline-list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['account'] = self.request.user.client_account
        return ctx


class PipelineStatsView(HiringAgentMixin, View):
    """Return pipeline statistics as JSON."""

    def get(self, request, *args, **kwargs):
        pipeline = get_object_or_404(
            HiringPipeline, uuid=kwargs.get('pipeline_uuid'), client=self.account,
        )
        candidates = pipeline.candidates.all()
        stage_counts = {}
        for code, label in PipelineCandidate.STAGE_CHOICES:
            stage_counts[code] = candidates.filter(stage=code).count()

        return JsonResponse({
            'total': candidates.count(),
            'stages': stage_counts,
            'status': pipeline.status,
        })
