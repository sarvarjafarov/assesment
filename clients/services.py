"""
Email services for client account management.
Handles verification emails, approval notifications, and welcome emails.
"""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags


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
