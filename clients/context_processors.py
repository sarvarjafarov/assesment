"""
Context processors for client portal navigation.
Provides sidebar badge counts and navigation data to all templates.
"""


def portal_navigation(request):
    """
    Add portal navigation context to all client portal pages.

    Provides:
    - assessment_badge_count: Number of pending assessments requiring review
    - project_badge_count: Number of active projects
    - is_manager: Boolean indicating if user has manager role
    - can_manage_branding: Boolean for branding permissions
    - account: The client account object for sidebar display
    - role_label: Human-readable role name
    """
    context = {
        'assessment_badge_count': None,
        'project_badge_count': None,
        'is_manager': False,
        'can_manage_branding': False,
        'has_custom_assessments': False,
        'has_ai_hiring': False,
        'account': None,
        'role_label': None,
        'sidebar_plan': None,
    }

    # Only add navigation data for authenticated client users
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return context

    # Check if user has a client account
    if not hasattr(request.user, 'client_account'):
        return context

    try:
        from clients.models import ClientAccount, ClientProject
        from marketing_assessments.models import DigitalMarketingAssessmentSession
        from pm_assessments.models import ProductAssessmentSession
        from behavioral_assessments.models import BehavioralAssessmentSession

        account = request.user.client_account

        # Add account and role to context for sidebar footer
        context['account'] = account
        context['role_label'] = dict(ClientAccount.ROLE_CHOICES).get(account.role, account.role.title())

        # Get role information
        context['is_manager'] = account.role == 'manager'
        context['can_manage_branding'] = account.role in ('manager', 'branding_manager')

        # Check if user has access to custom assessments (pro/enterprise only)
        context['has_custom_assessments'] = account.plan_slug in ('pro', 'enterprise')

        # Check if user has access to AI hiring pipelines (enterprise only)
        context['has_ai_hiring'] = account.plan_slug == 'enterprise'

        # Count assessments requiring review (completed sessions not yet reviewed)
        assessment_count = 0

        # Count marketing assessments
        marketing_count = DigitalMarketingAssessmentSession.objects.filter(
            client=account,
            status='completed'
        ).count()

        # Count product assessments
        product_count = ProductAssessmentSession.objects.filter(
            client=account,
            status='completed'
        ).count()

        # Count behavioral assessments
        behavioral_count = BehavioralAssessmentSession.objects.filter(
            client=account,
            status='completed'
        ).count()

        assessment_count = marketing_count + product_count + behavioral_count

        # Only show badge if there are items to review
        if assessment_count > 0:
            context['assessment_badge_count'] = assessment_count

        # Count active positions
        project_count = ClientProject.objects.filter(
            client=account,
            status=ClientProject.STATUS_ACTIVE
        ).count()

        if project_count > 0:
            context['project_badge_count'] = project_count

        # Unread notification count for badge
        context['notification_unread_count'] = account.notifications.filter(is_read=False).count()

        # Sidebar plan usage (lightweight)
        invite_limit = account.invite_limit()
        invites_used = account.invites_used() if invite_limit else 0
        invite_pct = min(100, round((invites_used / invite_limit) * 100)) if invite_limit else None
        context['sidebar_plan'] = {
            'name': dict(ClientAccount.PLAN_CHOICES).get(account.plan_slug, 'Starter'),
            'slug': account.plan_slug,
            'invites_used': invites_used,
            'invite_limit': invite_limit,
            'invite_pct': invite_pct,
        }

    except Exception:
        # Silently fail if there are any issues
        # This prevents the entire page from breaking
        pass

    return context
