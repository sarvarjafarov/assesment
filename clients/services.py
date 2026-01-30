"""
Email services for client account management.
Handles verification emails, approval notifications, and welcome emails.
Also includes webhook delivery services.
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_verification_email(client_account):
    """
    Send email verification link to newly registered client.

    Args:
        client_account: ClientAccount instance

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Generate verification token
    token = client_account.generate_verification_token()

    # Build verification URL
    verification_url = settings.SITE_URL.rstrip('/') + reverse(
        'clients:verify-email',
        kwargs={'account_id': client_account.pk, 'token': token}
    )

    # Email context
    context = {
        'client': client_account,
        'full_name': client_account.full_name,
        'company_name': client_account.company_name,
        'verification_url': verification_url,
        'site_url': settings.SITE_URL,
    }

    # Render email templates
    subject = f'Verify your email for {client_account.company_name} · Evalon'
    html_body = render_to_string('emails/verify_email.html', context)
    text_body = strip_tags(html_body)

    # Create and send email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[client_account.email],
    )
    email.attach_alternative(html_body, "text/html")

    try:
        email.send()
        return True
    except Exception as e:
        # Log error in production
        print(f"Failed to send verification email: {e}")
        return False


def send_approval_notification(client_account):
    """
    Notify admin team that a new client has verified their email
    and is ready for approval.

    Args:
        client_account: ClientAccount instance

    Returns:
        bool: True if email was sent successfully
    """
    admin_emails = getattr(settings, 'ADMIN_NOTIFICATION_EMAILS', [settings.DEFAULT_FROM_EMAIL])

    context = {
        'client': client_account,
        'full_name': client_account.full_name,
        'company_name': client_account.company_name,
        'email': client_account.email,
        'phone_number': client_account.phone_number,
        'employee_size': client_account.employee_size,
        'requested_assessments': client_account.requested_labels(),
        'notes': client_account.notes,
        'admin_url': settings.SITE_URL.rstrip('/') + '/admin/clients/clientaccount/' + str(client_account.pk) + '/change/',
    }

    subject = f'New Client Ready for Approval: {client_account.company_name}'
    html_body = render_to_string('emails/admin_approval_notification.html', context)
    text_body = strip_tags(html_body)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=admin_emails,
    )
    email.attach_alternative(html_body, "text/html")

    try:
        email.send()
        return True
    except Exception as e:
        print(f"Failed to send admin notification: {e}")
        return False


def send_welcome_email(client_account):
    """
    Send welcome email with onboarding instructions after admin approval.

    Args:
        client_account: ClientAccount instance

    Returns:
        bool: True if email was sent successfully
    """
    # Build dashboard URL
    dashboard_url = settings.SITE_URL.rstrip('/') + reverse('clients:dashboard')
    assessments_url = settings.SITE_URL.rstrip('/') + reverse('clients:assessments')
    projects_url = settings.SITE_URL.rstrip('/') + reverse('clients:project-list')

    # Get approved assessment labels
    catalog = client_account.ASSESSMENT_DETAILS
    approved_assessment_labels = [
        catalog.get(code, {}).get('label', code.title())
        for code in (client_account.allowed_assessments or [])
    ]

    context = {
        'client': client_account,
        'full_name': client_account.full_name,
        'company_name': client_account.company_name,
        'dashboard_url': dashboard_url,
        'assessments_url': assessments_url,
        'projects_url': projects_url,
        'approved_assessments': approved_assessment_labels,
        'plan_name': client_account.plan_details()['label'],
        'project_quota': client_account.project_quota,
        'invite_quota': client_account.invite_quota,
        'site_url': settings.SITE_URL,
    }

    subject = f'Welcome to Evalon, {client_account.full_name}! 🎉'
    html_body = render_to_string('emails/welcome_onboarding.html', context)
    text_body = strip_tags(html_body)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[client_account.email],
    )
    email.attach_alternative(html_body, "text/html")

    try:
        email.send()
        return True
    except Exception as e:
        print(f"Failed to send welcome email: {e}")
        return False


def send_completion_alert(client_account, session, assessment_type):
    """
    Send email notification when a candidate completes an assessment.

    Args:
        client_account: ClientAccount instance
        session: Assessment session instance (Marketing, PM, or Behavioral)
        assessment_type: String identifying the assessment type

    Returns:
        bool: True if email was sent successfully
    """
    if not client_account.receive_completion_alerts:
        return False

    # Get assessment type label
    catalog = client_account.ASSESSMENT_DETAILS
    assessment_label = catalog.get(assessment_type, {}).get('label', assessment_type.title())

    # Build results URL
    results_url = settings.SITE_URL.rstrip('/') + reverse(
        'clients:assessment-detail',
        kwargs={'assessment_type': assessment_type, 'session_uuid': session.uuid}
    )

    # Get score if available
    score = None
    if hasattr(session, 'overall_score') and session.overall_score is not None:
        score = session.overall_score
    elif hasattr(session, 'eligibility_score') and session.eligibility_score is not None:
        score = session.eligibility_score

    context = {
        'client': client_account,
        'full_name': client_account.full_name,
        'company_name': client_account.company_name,
        'candidate_id': session.candidate_id,
        'assessment_type': assessment_label,
        'score': score,
        'results_url': results_url,
        'site_url': settings.SITE_URL,
    }

    subject = f'Assessment Completed: {session.candidate_id} finished {assessment_label}'
    html_body = render_to_string('emails/completion_alert.html', context)
    text_body = strip_tags(html_body)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[client_account.email],
    )
    email.attach_alternative(html_body, "text/html")

    try:
        email.send()
        return True
    except Exception as e:
        print(f"Failed to send completion alert: {e}")
        return False


def send_new_candidate_alert(client_account, session, assessment_type):
    """
    Send email notification when a new candidate starts an assessment.

    Args:
        client_account: ClientAccount instance
        session: Assessment session instance (Marketing, PM, or Behavioral)
        assessment_type: String identifying the assessment type

    Returns:
        bool: True if email was sent successfully
    """
    if not client_account.receive_new_candidate_alerts:
        return False

    # Get assessment type label
    catalog = client_account.ASSESSMENT_DETAILS
    assessment_label = catalog.get(assessment_type, {}).get('label', assessment_type.title())

    # Build manage URL
    manage_url = settings.SITE_URL.rstrip('/') + reverse(
        'clients:assessment-manage',
        kwargs={'assessment_type': assessment_type}
    )

    context = {
        'client': client_account,
        'full_name': client_account.full_name,
        'company_name': client_account.company_name,
        'candidate_id': session.candidate_id,
        'assessment_type': assessment_label,
        'manage_url': manage_url,
        'site_url': settings.SITE_URL,
    }

    subject = f'New Candidate: {session.candidate_id} started {assessment_label}'
    html_body = render_to_string('emails/new_candidate_alert.html', context)
    text_body = strip_tags(html_body)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[client_account.email],
    )
    email.attach_alternative(html_body, "text/html")

    try:
        email.send()
        return True
    except Exception as e:
        print(f"Failed to send new candidate alert: {e}")
        return False


# =============================================================================
# WEBHOOK SERVICES
# =============================================================================

def generate_webhook_signature(payload: str, secret: str) -> str:
    """
    Generate HMAC-SHA256 signature for webhook payload.

    Args:
        payload: JSON string of the webhook payload
        secret: The webhook secret key

    Returns:
        Hex-encoded HMAC signature
    """
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def send_webhook(client_account, event_type: str, data: dict) -> bool:
    """
    Send a webhook notification to the client's configured URL.

    Args:
        client_account: ClientAccount instance
        event_type: The type of event (e.g., 'session.completed')
        data: Dictionary containing the event data

    Returns:
        bool: True if webhook was sent successfully
    """
    try:
        from .models import WebhookDelivery
    except Exception:
        logger.warning("WebhookDelivery model not available, skipping webhook")
        return False

    try:
        # Check if webhook should be triggered
        if not client_account.should_trigger_webhook(event_type):
            return False
    except Exception:
        # Fields may not exist in DB if migrations haven't run
        return False

    # Build the payload
    payload = {
        "id": f"evt_{timezone.now().strftime('%Y%m%d%H%M%S')}_{client_account.pk}",
        "type": event_type,
        "created": timezone.now().isoformat(),
        "data": data,
    }

    payload_json = json.dumps(payload, default=str)

    # Create delivery record
    delivery = WebhookDelivery.objects.create(
        client=client_account,
        event_type=event_type,
        payload=payload,
        status=WebhookDelivery.STATUS_PENDING,
    )

    # Generate signature
    signature = generate_webhook_signature(payload_json, client_account.webhook_secret)

    # Send the webhook
    headers = {
        "Content-Type": "application/json",
        "X-Evalon-Signature": signature,
        "X-Evalon-Event": event_type,
        "X-Evalon-Delivery": str(delivery.pk),
        "User-Agent": "Evalon-Webhook/1.0",
    }

    try:
        response = requests.post(
            client_account.webhook_url,
            data=payload_json,
            headers=headers,
            timeout=30,
        )

        if response.status_code >= 200 and response.status_code < 300:
            delivery.mark_success(response.status_code, response.text)
            return True
        else:
            delivery.mark_failed(response.status_code, f"HTTP {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        delivery.mark_failed(error="Connection timeout")
        return False
    except requests.exceptions.ConnectionError as e:
        delivery.mark_failed(error=f"Connection error: {str(e)}")
        return False
    except Exception as e:
        logger.exception(f"Webhook delivery failed for client {client_account.pk}")
        delivery.mark_failed(error=str(e))
        return False


def trigger_session_webhook(session, event_type: str):
    """
    Trigger a webhook for an assessment session event.
    Fails silently if webhook infrastructure is not available.

    Args:
        session: Assessment session instance
        event_type: One of 'session.created', 'session.started', 'session.completed', 'session.expired'
    """
    try:
        client = getattr(session, "client", None)
        if not client:
            return

        # Check if webhooks are configured before building payload
        if not getattr(client, "webhook_enabled", False):
            return

        # Build session data payload
        data = {
            "session": {
                "uuid": str(session.uuid),
                "candidate_id": getattr(session, "candidate_id", None) or getattr(session, "candidate_email", ""),
                "status": session.status,
                "assessment_type": _get_assessment_type(session),
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "completed_at": getattr(session, "completed_at", None),
            },
            "client": {
                "company_name": client.company_name,
            },
        }

        # Add score if completed
        if event_type == "session.completed":
            score = _get_session_score(session)
            if score is not None:
                data["session"]["score"] = score

        # Add project info if available
        project = getattr(session, "project", None)
        if project:
            data["session"]["project"] = {
                "uuid": str(project.uuid),
                "title": project.title,
            }

        send_webhook(client, event_type, data)
    except Exception:
        logger.exception("Failed to trigger webhook for session %s event %s", getattr(session, "uuid", "?"), event_type)


def _get_assessment_type(session) -> str:
    """Determine assessment type from session model."""
    model_name = session.__class__.__name__.lower()
    if "marketing" in model_name:
        return "marketing"
    elif "product" in model_name or "pm" in model_name:
        return "product"
    elif "behavioral" in model_name:
        return "behavioral"
    elif "custom" in model_name:
        return "custom"
    return "unknown"


def _get_session_score(session):
    """Get the score from a session if available."""
    if hasattr(session, "overall_score") and session.overall_score is not None:
        return float(session.overall_score)
    if hasattr(session, "eligibility_score") and session.eligibility_score is not None:
        return float(session.eligibility_score)
    if hasattr(session, "score") and session.score is not None:
        return float(session.score)
    return None


def retry_failed_webhooks():
    """
    Retry failed webhook deliveries that are due for retry.
    Should be called periodically by a background task.
    """
    from .models import WebhookDelivery

    now = timezone.now()
    pending_retries = WebhookDelivery.objects.filter(
        status=WebhookDelivery.STATUS_RETRYING,
        next_retry_at__lte=now,
    ).select_related("client")

    for delivery in pending_retries:
        client = delivery.client
        if not client.has_webhook_configured:
            delivery.status = WebhookDelivery.STATUS_FAILED
            delivery.error_message = "Webhook configuration removed"
            delivery.save(update_fields=["status", "error_message", "updated_at"])
            continue

        payload_json = json.dumps(delivery.payload, default=str)
        signature = generate_webhook_signature(payload_json, client.webhook_secret)

        headers = {
            "Content-Type": "application/json",
            "X-Evalon-Signature": signature,
            "X-Evalon-Event": delivery.event_type,
            "X-Evalon-Delivery": str(delivery.pk),
            "X-Evalon-Retry": str(delivery.attempts),
            "User-Agent": "Evalon-Webhook/1.0",
        }

        try:
            response = requests.post(
                client.webhook_url,
                data=payload_json,
                headers=headers,
                timeout=30,
            )

            if response.status_code >= 200 and response.status_code < 300:
                delivery.mark_success(response.status_code, response.text)
            else:
                delivery.mark_failed(response.status_code, f"HTTP {response.status_code}")

        except Exception as e:
            delivery.mark_failed(error=str(e))
