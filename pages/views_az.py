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
        "badge": "İşə Qəbul Qiymətləndirmə Platforması",
        "title": "Daha yaxşı namizədləri",
        "title_accent": "strukturlaşdırılmış qiymətləndirmələrlə işə götürün",
        "subtitle": "Hər bir vəzifə üçün hazır bacarıq testləri — avtomatik qiymətləndirmə, irəliləyiş izləmə və komandanızın etibar edə biləcəyi hesabatlarla.",
        "primary_label": "Pulsuz Başlayın",
        "primary_url": reverse("clients:signup"),
        "secondary_link_label": "Necə işləyir →",
        "secondary_link_url": "#necə-işləyir",
    }

    assessment_suite = [
        {"slug": "marketing", "label": "Marketinq IQ", "title": "Rəqəmsal Marketinq", "summary": "Ödənişli reklam, SEO, analitika və kontent yaradılması.", "duration": "32 dəq"},
        {"slug": "product", "label": "Məhsul Hissi", "title": "Məhsul İdarəetməsi", "summary": "Məntiqi düşüncə, prioritetləşdirmə və UX analizi.", "duration": "30 dəq"},
        {"slug": "behavioral", "label": "Davranış DNT", "title": "Liderlik və Mədəniyyət", "summary": "Komanda işi, risk tolerantlığı və kouçinq.", "duration": "15 dəq"},
        {"slug": "ux_design", "label": "Dizayn Gözü", "title": "UX/UI Dizayn", "summary": "İstifadəçi araşdırması, interaksiya dizaynı və əlçatanlıq.", "duration": "35 dəq"},
        {"slug": "hr", "label": "İnsan Resursları", "title": "HR və İnsan Strategiyası", "summary": "İşə qəbul, uyğunluq və insan strategiyası.", "duration": "35 dəq"},
        {"slug": "finance", "label": "Maliyyə IQ", "title": "Maliyyə İdarəetməsi", "summary": "Büdcələşdirmə, risk idarəetməsi və strateji maliyyə.", "duration": "35 dəq"},
    ]

    features = [
        {"slug": "create", "title": "Vəzifə yaradın", "description": "Rolu müəyyənləşdirin, qiymətləndirmə əlavə edin və bir neçə dəqiqə ərzində vakansiya səhifənizdə yayınlayın."},
        {"slug": "invite", "title": "Namizədləri dəvət edin", "description": "Namizədlər öz tempiylə başlamaq üçün link olan aydın bir email alırlar."},
        {"slug": "review", "title": "Avtomatik qiymətləndirmə", "description": "Strukturlaşdırılmış rubriklər hər cavabı qiymətləndirir ki, siz yan-yana müqayisə edə biləsiniz."},
        {"slug": "decide", "title": "Qərar verin", "description": "Təmiz hesabatları yükləyin və bütün işə qəbul qərarlarını bir yerdə izləyin."},
    ]

    case_studies = [
        {"slug": "atlas", "company": "Atlas CRM", "headline": "Məhsul işə götürmələri üçün 37% daha sürətli.", "result": "Müsahibəçilər üçün avtomatik qiymətləndirmə ilə PM testlərini mərkəzləşdirdilər.", "metric_label": "İşə götürmə sürəti", "metric_value": "-37%"},
        {"slug": "northwind", "company": "Northwind Commerce", "headline": "Marketinq tapşırıqlarından 2x daha çox siqnal.", "result": "Ssenari tapşırıqları uzaqdan namizədlərə ədalətli şans verdi.", "metric_label": "Siqnal dərinliyi", "metric_value": "2x"},
        {"slug": "aster", "company": "Aster Care", "headline": "Namizəd NPS 4.9 / 5-ə yüksəldi.", "result": "Davranış refleksiyaları və yönləndirilmiş portal klinik liderləri cəlb etdi.", "metric_label": "Namizəd CSAT", "metric_value": "4.9"},
    ]

    pricing_tiers = [
        {
            "slug": "starter", "badge": "Pulsuz", "name": "Başlanğıc",
            "price": "$0", "frequency": "Həmişəlik",
            "description": "İki aktiv vəzifə və kiçik namizəd hovuzu ilə Evalon-u sınayın.",
            "projects": "2 aktiv layihə", "invites": "Ayda 20 dəvət",
            "cta_label": "Pulsuz hesab yaradın", "cta_url": reverse("clients:signup"),
            "highlighted": False,
            "features": ["Bütün 6 qiymətləndirmə bankı daxildir", "Əsas hesabatlar və CSV ixracı", "Email dəstəyi"],
        },
        {
            "slug": "pro", "badge": "Ən populyar", "name": "Pro",
            "price": "$59", "frequency": "aylıq",
            "description": "Daha zəngin hesabatlar və sadə brendinqlə birdən çox axtarış aparın.",
            "projects": "10 aktiv layihə", "invites": "Ayda 250 dəvət",
            "cta_label": "Pro sınağına başlayın", "cta_url": reverse("clients:signup"),
            "highlighted": True,
            "features": ["AI işə götürmə boru xətləri", "Xüsusi qiymətləndirmələr", "Kanban və top namizəd vurğuları", "Xüsusi brendinq + paylaşıla bilən hesabatlar", "Webhook və API inteqrasiyalar", "Prioritet dəstək"],
        },
        {
            "slug": "enterprise", "badge": "Xüsusi", "name": "Müəssisə",
            "price": "Xüsusi", "frequency": "bizimlə əlaqə saxlayın",
            "description": "Limitsiz layihələr və dəvətlər, xüsusi dəstək.",
            "projects": "Limitsiz layihələr", "invites": "Limitsiz dəvətlər",
            "cta_label": "Qiymət soruşun", "cta_url": reverse("pages_az:contact"),
            "highlighted": False,
            "features": ["Xüsusi müştəri meneceri", "SLA zəmanəti", "Təkmil analitika", "Yerində təlim və dəstək"],
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
            "description": "Evalon-u iki aktiv vəzifə ilə sınayın.",
            "cta_label": "Pulsuz hesab yaradın", "cta_url": reverse("clients:signup"),
            "highlighted": False,
            "features": ["Bütün 6 qiymətləndirmə", "Əsas hesabatlar", "Email dəstəyi", "Ayda 20 dəvət", "2 aktiv layihə"],
        },
        {
            "slug": "pro", "badge": "Ən populyar", "name": "Pro",
            "price": "$59", "frequency": "aylıq",
            "description": "Zəngin hesabatlar və brendinqlə birdən çox axtarış.",
            "cta_label": "Pro sınağına başlayın", "cta_url": reverse("clients:signup"),
            "highlighted": True,
            "features": ["AI işə götürmə boru xətləri", "Xüsusi qiymətləndirmələr yaradın", "Kanban və top namizəd", "Xüsusi brendinq + hesabatlar", "Webhook və API", "Prioritet dəstək", "Ayda 250 dəvət", "10 aktiv layihə"],
        },
        {
            "slug": "enterprise", "badge": "Xüsusi", "name": "Müəssisə",
            "price": "Xüsusi", "frequency": "bizimlə əlaqə saxlayın",
            "description": "Limitsiz hər şey, xüsusi dəstək.",
            "cta_label": "Qiymət soruşun", "cta_url": reverse("pages_az:contact"),
            "highlighted": False,
            "features": ["Xüsusi müştəri meneceri", "SLA zəmanəti", "Təkmil analitika və audit", "Yerində təlim", "Limitsiz layihə və dəvət"],
        },
    ]

    comparison = [
        {"feature": "Qiymətləndirmə bankları", "starter": "Bütün 6", "pro": "Bütün 6 + xüsusi", "enterprise": "Bütün 6 + xüsusi"},
        {"feature": "Aktiv layihələr", "starter": "2", "pro": "10", "enterprise": "Limitsiz"},
        {"feature": "Aylıq dəvətlər", "starter": "20", "pro": "250", "enterprise": "Limitsiz"},
        {"feature": "AI işə götürmə", "starter": "—", "pro": "✓", "enterprise": "✓"},
        {"feature": "Xüsusi brendinq", "starter": "—", "pro": "✓", "enterprise": "✓"},
        {"feature": "API girişi", "starter": "—", "pro": "✓", "enterprise": "✓"},
        {"feature": "Xüsusi dəstək", "starter": "Email", "pro": "Prioritet", "enterprise": "Xüsusi menecer"},
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
        {"label": "Ümumi sorğular", "email": "hello@evalon.app", "sla": "24 saat ərzində cavab", "details": ["Məhsul sualları", "Qiymətləndirmə", "Tərəfdaşlıq"]},
        {"label": "Texniki dəstək", "email": "support@evalon.app", "sla": "12 saat ərzində cavab", "details": ["Hesab problemləri", "İnteqrasiya dəstəyi", "Xəta bildirişləri"]},
        {"label": "Tərəfdaşlıq", "email": "partners@evalon.app", "sla": "48 saat ərzində cavab", "details": ["Reseller proqramı", "API tərəfdaşlıq", "Birgə marketinq"]},
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
                error = "CV-nizin analizində xəta baş verdi. Zəhmət olmasa yenidən cəhd edin."

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
