"""
Azerbaijani language views for evalon.tech/az/
Mirrors pages/views.py but with Azerbaijani content and templates.
"""
import json
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q

from .forms import ResumeCheckerForm, ResumeDownloadForm
from .models import (
    ResumeTemplate, ResumeBuilderLead, ResumeCheckerLead,
    NewsletterSubscriber, Role,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://www.evalon.tech"


def _hreflang(en_path, az_path):
    return [
        {"lang": "en", "url": f"{BASE_URL}{en_path}"},
        {"lang": "az", "url": f"{BASE_URL}{az_path}"},
    ]


# ── Home ──────────────────────────────────────────────────────────────

def home(request):
    hero_content = {
        "badge": "İşə qəbul platforması",
        "title": "Ən yaxşı namizədləri",
        "title_accent": "testlərlə seçin",
        "subtitle": "Hər vəzifə üçün hazır bacarıq testləri — avtomatik nəticələr, prosesin izlənməsi və etibarlı hesabatlar.",
        "primary_label": "Pulsuz başlayın",
        "primary_url": reverse("clients:signup"),
        "secondary_link_label": "Necə işləyir →",
        "secondary_link_url": "#necə-işləyir",
    }

    assessment_suite = [
        {"slug": "marketing", "label": "Marketinq", "title": "Rəqəmsal marketinq", "summary": "Reklam, SEO, analitika və kontent bilikləri yoxlanılır.", "duration": "32 dəq"},
        {"slug": "product", "label": "Məhsul", "title": "Məhsul idarəetməsi", "summary": "Analitik düşüncə, prioritetlərin müəyyənləşdirilməsi və UX.", "duration": "30 dəq"},
        {"slug": "behavioral", "label": "Davranış", "title": "Liderlik və mədəniyyət", "summary": "Komanda işi, riskə münasibət və mentorluq bacarıqları.", "duration": "15 dəq"},
        {"slug": "ux_design", "label": "Dizayn", "title": "UX/UI dizayn", "summary": "İstifadəçi araşdırması, interfeys dizaynı və əlçatanlıq.", "duration": "35 dəq"},
        {"slug": "hr", "label": "HR", "title": "İnsan resursları", "summary": "İşə qəbul, əmək qanunvericiliyi və HR strategiyası.", "duration": "35 dəq"},
        {"slug": "finance", "label": "Maliyyə", "title": "Maliyyə idarəetməsi", "summary": "Büdcə planlaması, risk analizi və strateji maliyyə.", "duration": "35 dəq"},
    ]

    features = [
        {"slug": "create", "title": "Vakansiya yaradın", "description": "Vəzifəni təyin edin, test əlavə edin və vakansiya səhifənizdə dərc edin."},
        {"slug": "invite", "title": "Namizədləri dəvət edin", "description": "Namizədlər öz vaxtlarında testi keçmək üçün link olan e-poçt alırlar."},
        {"slug": "review", "title": "Avtomatik nəticələr", "description": "Hər cavab avtomatik qiymətləndirilir — namizədləri asanlıqla müqayisə edin."},
        {"slug": "decide", "title": "Qərar qəbul edin", "description": "Hesabatları yükləyin və bütün işə qəbul prosesini bir yerdən idarə edin."},
    ]

    case_studies = [
        {"slug": "atlas", "company": "Atlas CRM", "headline": "Məhsul mütəxəssislərinin işə qəbulu 37% sürətləndi.", "result": "Testlərin avtomatik qiymətləndirilməsi müsahibəçilərin vaxtına qənaət etdi.", "metric_label": "İşə qəbul sürəti", "metric_value": "-37%"},
        {"slug": "northwind", "company": "Northwind Commerce", "headline": "Marketinq testlərindən 2 dəfə çox faydalı nəticə.", "result": "Real ssenari tapşırıqları distant namizədlərə bərabər imkan yaratdı.", "metric_label": "Nəticə keyfiyyəti", "metric_value": "2x"},
        {"slug": "aster", "company": "Aster Care", "headline": "Namizəd məmnuniyyəti 4.9/5-ə çatdı.", "result": "Rahat interfeys və aydın təlimatlar namizədlərin iştirakını artırdı.", "metric_label": "Namizəd reytinqi", "metric_value": "4.9"},
    ]

    pricing_tiers = [
        {
            "slug": "starter", "badge": "Pulsuz", "name": "Başlanğıc",
            "price": "$0", "frequency": "Həmişəlik",
            "description": "2 aktiv vakansiya ilə Evalon-u sınayın.",
            "projects": "2 aktiv vakansiya", "invites": "Ayda 20 dəvət",
            "cta_label": "Pulsuz qeydiyyat", "cta_url": reverse("clients:signup"),
            "highlighted": False,
            "features": ["6 test bankının hamısı daxildir", "Sadə hesabatlar və CSV", "E-poçt dəstəyi"],
        },
        {
            "slug": "pro", "badge": "Ən çox seçilən", "name": "Pro",
            "price": "$59", "frequency": "aylıq",
            "description": "Ətraflı hesabatlar və şirkət brendinqi ilə bir neçə vakansiya idarə edin.",
            "projects": "10 aktiv vakansiya", "invites": "Ayda 250 dəvət",
            "cta_label": "Pro-nu sınayın", "cta_url": reverse("clients:signup"),
            "highlighted": True,
            "features": ["AI ilə avtomatik işə qəbul", "Öz testlərinizi yaradın", "Namizəd paneli və ən yaxşı namizədlər", "Şirkət brendinqi + paylaşılan hesabatlar", "Webhook və API inteqrasiya", "Prioritet dəstək"],
        },
        {
            "slug": "enterprise", "badge": "Fərdi", "name": "Korporativ",
            "price": "Fərdi", "frequency": "bizimlə əlaqə saxlayın",
            "description": "Limitsiz vakansiya, dəvət və fərdi dəstək.",
            "projects": "Limitsiz vakansiya", "invites": "Limitsiz dəvət",
            "cta_label": "Qiymət öyrənin", "cta_url": reverse("pages_az:contact"),
            "highlighted": False,
            "features": ["Fərdi müştəri meneceri", "SLA zəmanəti", "Təkmil analitika", "Yerində təlim və dəstək"],
        },
    ]

    return render(request, "pages/az/home.html", {
        "hero_content": hero_content,
        "assessment_suite": assessment_suite,
        "features": features,
        "case_studies": case_studies,
        "pricing_tiers": pricing_tiers,
        "lang": "az",
        "hreflang": _hreflang("/", "/az/"),
    })


# ── Pricing ───────────────────────────────────────────────────────────

def pricing(request):
    from .views import pricing as en_pricing_view
    # Reuse the English pricing data structure but with AZ labels
    pricing_tiers = [
        {
            "slug": "starter", "badge": "Pulsuz", "name": "Başlanğıc",
            "price": "$0", "frequency": "Həmişəlik",
            "description": "2 aktiv vakansiya ilə Evalon-u sınayın.",
            "cta_label": "Pulsuz qeydiyyat", "cta_url": reverse("clients:signup"),
            "highlighted": False,
            "features": ["6 test bankının hamısı", "Sadə hesabatlar", "E-poçt dəstəyi", "Ayda 20 dəvət", "2 aktiv vakansiya"],
        },
        {
            "slug": "pro", "badge": "Ən çox seçilən", "name": "Pro",
            "price": "$59", "frequency": "aylıq",
            "description": "Ətraflı hesabatlar və brendinq ilə bir neçə vakansiya idarə edin.",
            "cta_label": "Pro-nu sınayın", "cta_url": reverse("clients:signup"),
            "highlighted": True,
            "features": ["AI ilə avtomatik işə qəbul", "Öz testlərinizi yaradın", "Namizəd paneli", "Şirkət brendinqi + hesabatlar", "Webhook və API", "Prioritet dəstək", "Ayda 250 dəvət", "10 aktiv vakansiya"],
        },
        {
            "slug": "enterprise", "badge": "Fərdi", "name": "Korporativ",
            "price": "Fərdi", "frequency": "bizimlə əlaqə saxlayın",
            "description": "Limitsiz vakansiya, dəvət və fərdi dəstək.",
            "cta_label": "Qiymət öyrənin", "cta_url": reverse("pages_az:contact"),
            "highlighted": False,
            "features": ["Fərdi müştəri meneceri", "SLA zəmanəti", "Təkmil analitika və audit", "Yerində təlim", "Limitsiz vakansiya və dəvət"],
        },
    ]

    comparison = [
        {"feature": "Test bankları", "starter": "6-sı da", "pro": "6 + öz testləriniz", "enterprise": "6 + öz testləriniz"},
        {"feature": "Aktiv vakansiyalar", "starter": "2", "pro": "10", "enterprise": "Limitsiz"},
        {"feature": "Aylıq dəvət", "starter": "20", "pro": "250", "enterprise": "Limitsiz"},
        {"feature": "AI işə qəbul", "starter": "—", "pro": "✓", "enterprise": "✓"},
        {"feature": "Şirkət brendinqi", "starter": "—", "pro": "✓", "enterprise": "✓"},
        {"feature": "API", "starter": "—", "pro": "✓", "enterprise": "✓"},
        {"feature": "Dəstək", "starter": "E-poçt", "pro": "Prioritet", "enterprise": "Fərdi menecer"},
    ]

    return render(request, "pages/az/pricing.html", {
        "pricing_tiers": pricing_tiers,
        "comparison": comparison,
        "lang": "az",
        "hreflang": _hreflang("/pricing/", "/az/qiymet/"),
    })


# ── Contact ───────────────────────────────────────────────────────────

def contact(request):
    channels = [
        {"label": "Ümumi suallar", "email": "hello@evalon.app", "sla": "24 saat ərzində cavab", "details": ["Məhsul haqqında suallar", "Qiymət təklifləri", "Əməkdaşlıq"]},
        {"label": "Texniki dəstək", "email": "support@evalon.app", "sla": "12 saat ərzində cavab", "details": ["Hesab problemləri", "İnteqrasiya köməyi", "Xəta bildirişi"]},
        {"label": "Əməkdaşlıq", "email": "partners@evalon.app", "sla": "48 saat ərzində cavab", "details": ["Distribütor proqramı", "API əməkdaşlıq", "Birgə marketinq"]},
    ]

    return render(request, "pages/az/contact.html", {
        "channels": channels,
        "lang": "az",
        "hreflang": _hreflang("/contact/", "/az/elaqe/"),
    })


# ── Privacy & Terms (simple pages) ────────────────────────────────────

def privacy(request):
    return render(request, "pages/az/privacy.html", {
        "lang": "az",
        "hreflang": _hreflang("/privacy/", "/az/mexfilik/"),
    })


def terms(request):
    return render(request, "pages/az/terms.html", {
        "lang": "az",
        "hreflang": _hreflang("/terms/", "/az/sertler/"),
    })


# ── Resume Checker ────────────────────────────────────────────────────

def resume_checker(request):
    from .views import _analyze_resume, _send_resume_checker_email

    form = ResumeCheckerForm()
    result = None
    error = None

    if request.method == "POST":
        form = ResumeCheckerForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                result = _analyze_resume(
                    form.cleaned_data["resume"],
                    form.cleaned_data["job_description"],
                )
                lead = ResumeCheckerLead.objects.create(
                    email=form.cleaned_data["email"],
                    full_name=form.cleaned_data["full_name"],
                    ats_score=result.get("ats_score"),
                    verdict=result.get("verdict", ""),
                    result_json=result,
                )
                NewsletterSubscriber.objects.get_or_create(
                    email=form.cleaned_data["email"],
                    defaults={"source": "resume_checker_az"},
                )
                _send_resume_checker_email(lead, result)
            except Exception as exc:
                logger.exception("Resume checker AZ error: %s", exc)
                error = "CV analizi zamanı xəta baş verdi. Zəhmət olmasa yenidən yoxlayın."

    return render(request, "pages/az/resume_checker.html", {
        "form": form,
        "result": result,
        "error": error,
        "lang": "az",
        "hreflang": _hreflang("/resume-checker/", "/az/cv-yoxla/"),
    })


# ── Resume Builder ────────────────────────────────────────────────────

def resume_builder_list(request):
    from django.db.models import Sum

    roles = Role.objects.filter(
        is_active=True, resume_template__is_active=True,
    ).select_related('resume_template').distinct()

    department = request.GET.get('department', '').strip()
    if department:
        roles = roles.filter(department__iexact=department)

    query = request.GET.get('q', '').strip()
    if query:
        roles = roles.filter(
            Q(title__icontains=query) | Q(department__icontains=query)
        )

    departments = (
        Role.objects.filter(is_active=True, resume_template__is_active=True)
        .values_list('department', flat=True).distinct().order_by('department')
    )

    total_templates = Role.objects.filter(
        is_active=True, resume_template__is_active=True,
    ).distinct().count()
    total_downloads = ResumeTemplate.objects.filter(is_active=True).aggregate(
        total=Sum('downloads_count')
    )['total'] or 0

    paginator = Paginator(roles, 24)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Use AZ template if it exists, fall back to English
    import os
    from django.conf import settings
    az_tpl = 'pages/az/resume_builder/list.html'
    en_tpl = 'pages/resume_builder/list.html'
    tpl = az_tpl if os.path.exists(os.path.join(settings.BASE_DIR, 'templates', az_tpl)) else en_tpl
    return render(request, tpl, {
        'roles': page_obj,
        'page_obj': page_obj,
        'query': query,
        'department': department,
        'departments': departments,
        'total_templates': total_templates,
        'total_downloads': total_downloads,
        'total_departments': departments.count(),
        'lang': 'az',
        'hreflang': _hreflang('/resume/', '/az/cv/'),
    })


def resume_builder_department(request, dept_slug):
    from .views import DEPARTMENT_META
    from django.http import Http404

    dept_info = DEPARTMENT_META.get(dept_slug)
    if not dept_info:
        raise Http404

    roles = Role.objects.filter(
        is_active=True, department__iexact=dept_info['name'],
        resume_template__is_active=True,
    ).select_related('resume_template').distinct()

    import os
    from django.conf import settings
    az_tpl = 'pages/az/resume_builder/department.html'
    en_tpl = 'pages/resume_builder/department.html'
    tpl = az_tpl if os.path.exists(os.path.join(settings.BASE_DIR, 'templates', az_tpl)) else en_tpl
    return render(request, tpl, {
        'dept_slug': dept_slug,
        'dept_info': dept_info,
        'roles': roles,
        'lang': 'az',
    })


def resume_builder_detail(request, slug):
    template = get_object_or_404(
        ResumeTemplate.objects.select_related('role'),
        role__slug=slug, is_active=True,
    )
    role = template.role

    related = ResumeTemplate.objects.filter(
        is_active=True, role__department=role.department, role__is_active=True,
    ).select_related('role').exclude(pk=template.pk)[:4]

    import os
    from django.conf import settings
    az_tpl = 'pages/az/resume_builder/detail.html'
    en_tpl = 'pages/resume_builder/detail.html'
    tpl = az_tpl if os.path.exists(os.path.join(settings.BASE_DIR, 'templates', az_tpl)) else en_tpl
    return render(request, tpl, {
        'template': template,
        'role': role,
        'related': related,
        'lang': 'az',
        'hreflang': _hreflang(f'/resume/{slug}/', f'/az/cv/{slug}/'),
    })


@require_POST
def resume_download_pdf(request, slug):
    """PDF download — reuses English download logic."""
    from .views import resume_download_pdf as en_download
    return en_download(request, slug)


# ── Assessments ───────────────────────────────────────────────────────

from .models import PublicAssessment


def assessment_list(request):
    """AZ version of assessment library list."""
    from .views import _get_assessment_theme, ASSESSMENT_THEMES

    assessments = PublicAssessment.objects.filter(is_active=True)

    query = request.GET.get('q', '').strip()
    if query:
        assessments = assessments.filter(
            Q(title__icontains=query) | Q(label__icontains=query) |
            Q(summary__icontains=query) | Q(description__icontains=query)
        ).distinct()

    paginator = Paginator(assessments, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    for a in page_obj:
        theme = _get_assessment_theme(a.slug)
        a.theme_color = theme['color']
        a.theme_rgb = theme['rgb']

    return render(request, 'pages/az/assessments/list.html', {
        'assessments': page_obj,
        'page_obj': page_obj,
        'query': query,
        'is_paginated': page_obj.has_other_pages(),
        'themes': ASSESSMENT_THEMES,
        'lang': 'az',
        'hreflang': _hreflang('/assessments/', '/az/qiymetlendirmeler/'),
    })


def assessment_detail(request, slug):
    """AZ version of assessment detail page."""
    from .views import _get_assessment_theme

    assessment = get_object_or_404(PublicAssessment, slug=slug, is_active=True)
    theme = _get_assessment_theme(assessment.slug)

    related = PublicAssessment.objects.filter(
        is_active=True
    ).exclude(pk=assessment.pk).order_by('order')[:4]
    for r in related:
        t = _get_assessment_theme(r.slug)
        r.theme_color = t['color']
        r.theme_rgb = t['rgb']

    return render(request, 'pages/az/assessments/detail.html', {
        'assessment': assessment,
        'related_assessments': related,
        'theme_color': theme['color'],
        'theme_rgb': theme['rgb'],
        'lang': 'az',
        'hreflang': _hreflang(f'/assessments/{slug}/', f'/az/qiymetlendirmeler/{slug}/'),
    })


# ── AI Hiring ─────────────────────────────────────────────────────────

def ai_hiring(request):
    """AZ version of AI hiring marketing page."""
    import os
    from django.conf import settings
    az_tpl = "pages/az/ai_hiring.html"
    en_tpl = "pages/ai_hiring.html"
    tpl = az_tpl if os.path.exists(os.path.join(settings.BASE_DIR, 'templates', az_tpl)) else en_tpl
    return render(request, tpl, {
        "active": "ai_hiring",
        "lang": "az",
        "hreflang": _hreflang("/ai-hiring/", "/az/ai-isegotürme/"),
    })


# ── Role Assessments (SEO) ───────────────────────────────────────────

def role_assessment_list(request):
    """AZ version of role assessment list."""
    from .views import role_assessment_list as en_view
    # Reuse English logic, just swap template
    from django.db.models import Count, Prefetch

    roles = Role.objects.filter(
        is_active=True, assessment_types__is_active=True,
    ).annotate(
        assessment_count=Count('assessment_types', filter=Q(assessment_types__is_active=True))
    ).filter(assessment_count__gt=0).distinct().prefetch_related(
        Prefetch('assessment_types', queryset=PublicAssessment.objects.filter(is_active=True).order_by('order')[:3], to_attr='preview_assessments')
    )

    department = request.GET.get('department', '').strip()
    if department:
        roles = roles.filter(department__iexact=department)

    query = request.GET.get('q', '').strip()
    if query:
        roles = roles.filter(Q(title__icontains=query) | Q(department__icontains=query))

    departments = Role.objects.filter(is_active=True).values_list('department', flat=True).distinct().order_by('department')

    paginator = Paginator(roles, 24)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'pages/az/roles/list.html', {
        'roles': page_obj,
        'page_obj': page_obj,
        'query': query,
        'department': department,
        'departments': departments,
        'total_roles': roles.count(),
        'total_assessments': PublicAssessment.objects.filter(is_active=True).count(),
        'total_departments': departments.count(),
        'lang': 'az',
        'hreflang': _hreflang('/assessments/roles/', '/az/qiymetlendirmeler/vezifeler/'),
    })


def role_assessment_department(request, dept_slug):
    """AZ version of role assessment department page."""
    from .views import DEPARTMENT_META, role_assessment_department as en_view
    from django.http import Http404

    dept_info = DEPARTMENT_META.get(dept_slug)
    if not dept_info:
        raise Http404

    roles = Role.objects.filter(
        is_active=True, department__iexact=dept_info['name'],
        assessment_types__is_active=True,
    ).distinct().prefetch_related('assessment_types')

    return render(request, 'pages/az/roles/department.html', {
        'dept_slug': dept_slug,
        'dept_info': dept_info,
        'roles': roles,
        'lang': 'az',
    })


def role_assessment_detail(request, slug):
    """AZ version of role assessment detail page."""
    from .views import _get_assessment_theme

    role = get_object_or_404(Role, slug=slug, is_active=True)

    recommended = role.assessment_types.filter(is_active=True).order_by('order')
    for a in recommended:
        theme = _get_assessment_theme(a.slug)
        a.theme_color = theme['color']
        a.theme_rgb = theme['rgb']

    related = Role.objects.filter(
        is_active=True, department=role.department,
        assessment_types__is_active=True,
    ).exclude(pk=role.pk).distinct()[:4]

    return render(request, 'pages/az/roles/detail.html', {
        'role': role,
        'recommended_assessments': recommended,
        'related_roles': related,
        'lang': 'az',
        'hreflang': _hreflang(f'/assessments/for/{slug}/', f'/az/qiymetlendirmeler/ucun/{slug}/'),
    })
