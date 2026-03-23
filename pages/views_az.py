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

    suite_heading = {
        "title": "Hər vəzifə üçün testlər",
        "subtitle": "Qiymətləndirmə rubrikləri və real iş ssenariləri ilə altı hazır sual bankı.",
        "instructions": "İstənilən testə klikləyərək nümunə sualları görün.",
    }

    testimonials = [
        {
            "name": "Murad Əliyev",
            "role": "HR direktoru, Atlas CRM",
            "company": "Atlas CRM",
            "quote": "Evalon marketinq üzrə işə qəbul müddətimizi 3 həftədən 12 günə endirdi. Avtomatik qiymətləndirmə sayəsində yalnız ən yaxşı namizədlərə fokuslandıq.",
            "metric": "60% daha sürətli",
            "avatar": "img/avatar-lauren.svg",
        },
        {
            "name": "Aynur Həsənova",
            "role": "İşə qəbul rəhbəri, Aster Care",
            "company": "Aster Care",
            "quote": "İndi namizədlər prosesdən razı qalırlar. Aydın təlimatlar və irəliləyiş izləmə yarımçıq qalan testləri yarıya endirdi.",
            "metric": "50% daha yaxşı tamamlanma",
            "avatar": "img/avatar-savannah.svg",
        },
    ]

    pricing_helper = {
        "headline": "Sadə və aydın qiymətlər",
        "subline": "Pulsuz başlayın, daha çox vakansiya lazım olduqda yüksəldin. Bütün planlara 6 test növü daxildir.",
        "footnote": "Bütün planlara limitsiz komanda üzvləri daxildir. İllik ödənişdə Pro planda 20% qənaət.",
    }

    ai_pipeline_steps = [
        {"title": "CV-ləri yükləyin", "desc": "PDF və ya DOCX fayllarını yükləyin — AI hər birini oxuyub anlayır.", "icon": "upload"},
        {"title": "AI yoxlayır və qiymətləndirir", "desc": "Claude bacarıqları, təcrübəni və vəzifəyə uyğunluğu 0-100 şkalasında qiymətləndirir.", "icon": "brain"},
        {"title": "Avtomatik test göndərilir", "desc": "Seçilmiş namizədlər avtomatik olaraq uyğun bacarıq testini alırlar.", "icon": "send"},
        {"title": "AI qərar verir", "desc": "CV analizi + test nəticələri = ağıllı işə qəbul tövsiyələri.", "icon": "check"},
    ]

    from .forms import DemoRequestForm
    if request.method == "POST":
        form = DemoRequestForm(request.POST)
        if form.is_valid():
            demo_request = form.save()
            from django.contrib import messages as django_messages
            django_messages.success(
                request,
                f"Təşəkkürlər {demo_request.full_name.split()[0]}! Demo sorğunuzu aldıq, 1 iş günü ərzində əlaqə saxlayacağıq.",
            )
            return redirect(f"{reverse('pages_az:home')}#cta")
    else:
        form = DemoRequestForm()

    return render(request, "pages/az/home.html", {
        "hero_content": hero_content,
        "suite": assessment_suite,
        "suite_heading": suite_heading,
        "assessment_suite": assessment_suite,
        "features": features,
        "case_studies": case_studies,
        "testimonials": testimonials,
        "pricing_tiers": pricing_tiers,
        "pricing_helper": pricing_helper,
        "invite_form": form,
        "ai_pipeline_steps": ai_pipeline_steps,
        "lang": "az",
        "hreflang": _hreflang("/", "/az/"),
    })


# ── Pricing ───────────────────────────────────────────────────────────

def pricing(request):
    tiers = [
        {
            "slug": "starter", "name": "Başlanğıc",
            "price": "$0", "frequency": "həmişəlik",
            "desc": "2 aktiv vakansiya ilə Evalon-u sınayın.",
            "limits": "2 vakansiya · ayda 20 dəvət",
            "cta_label": "Pulsuz qeydiyyat", "cta_url": reverse("clients:signup"),
            "highlighted": False,
            "features": [
                "6 test bankının hamısı",
                "2 aktiv vakansiya",
                "Ayda 20 namizəd dəvəti",
                "Sadə bal hesabatları",
                "CSV ixracı",
                "E-poçt dəstəyi",
            ],
        },
        {
            "slug": "pro", "name": "Pro",
            "price": "$59", "frequency": "aylıq",
            "desc": "Ətraflı hesabatlar, brendinq və AI alətləri ilə bir neçə vakansiya idarə edin.",
            "limits": "10 vakansiya · ayda 250 dəvət",
            "cta_label": "14 günlük pulsuz sınaq", "cta_url": reverse("clients:signup"),
            "highlighted": True,
            "features": [
                "Başlanğıc planın hər şeyi, üstəgəl:",
                "10 aktiv vakansiya",
                "Ayda 250 namizəd dəvəti",
                "AI ilə avtomatik işə qəbul",
                "Öz testlərinizi yaradın",
                "Namizəd paneli və ən yaxşı namizəd seçimi",
                "Şirkət brendinqi və paylaşılan hesabatlar",
                "Webhook və API inteqrasiya",
                "Əlavə dəvət $0.40",
                "Prioritet dəstək",
            ],
        },
        {
            "slug": "enterprise", "name": "Korporativ",
            "price": "Fərdi", "frequency": "bizimlə əlaqə",
            "desc": "Limitsiz vakansiya və dəvət, fərdi dəstək və yerində təlim.",
            "limits": "Limitsiz vakansiya və dəvət",
            "cta_label": "Qiymət öyrənin", "cta_url": reverse("pages_az:contact"),
            "highlighted": False,
            "features": [
                "Pro planın hər şeyi, üstəgəl:",
                "Limitsiz vakansiya və dəvət",
                "Fərdi müştəri meneceri",
                "SLA zəmanəti",
                "Tam API girişi",
                "Yerində təlim və dəstək",
            ],
        },
    ]

    comparison = [
        {"feature": "Aktiv vakansiyalar", "starter": "2", "pro": "10", "enterprise": "Limitsiz"},
        {"feature": "Aylıq dəvətlər", "starter": "20", "pro": "250", "enterprise": "Limitsiz"},
        {"feature": "6 test bankı", "starter": True, "pro": True, "enterprise": True},
        {"feature": "Bal hesabatları", "starter": True, "pro": True, "enterprise": True},
        {"feature": "CSV ixracı", "starter": True, "pro": True, "enterprise": True},
        {"feature": "Namizəd paneli", "starter": False, "pro": True, "enterprise": True},
        {"feature": "Ən yaxşı namizəd seçimi", "starter": False, "pro": True, "enterprise": True},
        {"feature": "Şirkət brendinqi", "starter": False, "pro": True, "enterprise": True},
        {"feature": "Paylaşılan hesabatlar", "starter": False, "pro": True, "enterprise": True},
        {"feature": "Prioritet dəstək", "starter": False, "pro": True, "enterprise": True},
        {"feature": "AI ilə avtomatik işə qəbul", "starter": False, "pro": True, "enterprise": True, "highlight": True},
        {"feature": "Öz testlərinizi yaradın", "starter": False, "pro": True, "enterprise": True},
        {"feature": "Webhook və API", "starter": False, "pro": True, "enterprise": True},
        {"feature": "Fərdi menecer", "starter": False, "pro": False, "enterprise": True},
        {"feature": "SLA zəmanəti", "starter": False, "pro": False, "enterprise": True},
        {"feature": "Yerində təlim", "starter": False, "pro": False, "enterprise": True},
    ]

    assessments = [
        {"name": "Marketinq", "desc": "Reklam, SEO, analitika və kampaniya strategiyası."},
        {"name": "Məhsul idarəetməsi", "desc": "Strategiya, icra, yol xəritəsi və məhsul düşüncəsi."},
        {"name": "Davranış", "desc": "Mədəniyyət və vəzifəyə uyğunluq üçün psixometrik siqnallar."},
        {"name": "UX/UI Dizayn", "desc": "İstifadəçi araşdırması, interfeys dizaynı və prototipləmə."},
        {"name": "HR", "desc": "İşə qəbul, əmək münasibətləri və uyğunluq."},
        {"name": "Maliyyə", "desc": "Maliyyə planlaması, büdcə və analiz."},
    ]

    faqs = [
        {"q": "Planımı istənilən vaxt dəyişə bilərəm?", "a": "Bəli. İstədiyiniz vaxt yüksəldə və ya endirə bilərsiniz — dəyişikliklər növbəti ödəniş dövründə qüvvəyə minir."},
        {"q": "Dəvət limitini keçsəm nə olur?", "a": "Pro planda hər əlavə dəvət $0.40-dır. Başlanğıc planda növbəti ayı gözləyin və ya Pro-ya yüksəldin."},
        {"q": "Bütün planlara 6 test növü daxildirmi?", "a": "Bəli. Pulsuz Başlanğıc planı da daxil olmaqla bütün planlara altı test bankının hamısı daxildir."},
        {"q": "İllik ödənişdə endirim varmı?", "a": "Bəli. Pro planın illik ödənişi 20% qənaət edir — aylıq $47-ə düşür."},
        {"q": "Hansı ödəniş üsullarını qəbul edirsiniz?", "a": "Visa, Mastercard, Amex qəbul edirik. Korporativ müştərilər üçün faktura ilə ödəniş mümkündür."},
        {"q": "İstədiyim vaxt ləğv edə bilərəm?", "a": "Mütləq. Uzunmüddətli müqavilə yoxdur. İdarə panelindən ləğv edin — cari dövrün sonuna qədər giriş davam edir."},
        {"q": "Pulsuz sınaq necə işləyir?", "a": "Pro sınağı 14 gün tam Pro funksiyalarını verir. Kredit kartı lazım deyil. Sınaq bitdikdə abunə olun və ya Başlanğıc plana qayıdın."},
        {"q": "Məlumatlarım təhlükəsizdirmi?", "a": "Bəli. AES-256 şifrələmə, TLS 1.3 və müntəzəm üçüncü tərəf audit istifadə edirik. Korporativ müştərilər SOC 2 hesabatı tələb edə bilər."},
    ]

    return render(request, "pages/az/pricing.html", {
        "active": "pricing",
        "tiers": tiers,
        "comparison": comparison,
        "assessments": assessments,
        "faqs": faqs,
        "lang": "az",
        "hreflang": _hreflang("/pricing/", "/az/qiymet/"),
    })


# ── Contact ───────────────────────────────────────────────────────────

def contact(request):
    hero = {
        "eyebrow": "Əlaqə",
        "title": "Biz çox sürətli cavab veririk.",
        "lede": "Evalon-u yoxlayırsınız, komandanızı qoşursunuz və ya təhlükəsizlik yoxlaması istəyirsiniz — sizi doğru mütəxəssisə yönləndirəcəyik.",
    }
    sections = [
        {
            "badge": "Satış və demo",
            "title": "hello@evalon.app",
            "body": "1 iş günü ərzində cavab.",
            "list": ["Canlı məhsul nümayişi", "Qiymət və tətbiq köməyi", "Təhlükəsizlik sorğuları"],
        },
        {
            "badge": "Dəstək",
            "title": "support@evalon.app",
            "body": "4 iş saatı ərzində cavab.",
            "list": ["Test problemlərinin həlli", "Namizəd portalı köməyi", "Hesab və ödəniş dəyişiklikləri"],
        },
        {
            "badge": "Əməkdaşlıq",
            "title": "partners@evalon.app",
            "body": "2 iş günü ərzində cavab.",
            "list": ["ATS və HRIS inteqrasiyalar", "Araşdırma əməkdaşlığı", "Kontent və tədbir sorğuları"],
        },
    ]

    return render(request, "pages/az/contact.html", {
        "hero": hero,
        "sections": sections,
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
    """AZ version of role assessment detail page — mirrors English view exactly."""
    role = get_object_or_404(Role, slug=slug, is_active=True)

    recommended_assessments = role.assessment_types.filter(is_active=True).order_by('order')

    related_roles = (
        Role.objects.filter(is_active=True, department=role.department)
        .exclude(pk=role.pk)[:4]
    )

    has_interview_questions = role.interview_questions.filter(is_active=True).exists()

    # Aggregate rich content from all linked assessments
    all_focus_areas = []
    all_skills = []
    all_samples = []
    all_use_cases = []
    all_faqs = []
    total_duration = 0
    total_questions = 0
    seen_focus = set()
    seen_skill_names = set()

    for a in recommended_assessments:
        total_duration += a.duration_minutes
        total_questions += a.question_count
        for fa in (a.focus_areas or []):
            if fa not in seen_focus:
                seen_focus.add(fa)
                all_focus_areas.append(fa)
        for sk in (a.skills_tested or []):
            name = sk.get('name', '') if isinstance(sk, dict) else str(sk)
            if name not in seen_skill_names:
                seen_skill_names.add(name)
                all_skills.append(sk)
        all_samples.extend(a.sample_questions or [])
        all_use_cases.extend(a.use_cases or [])
        all_faqs.extend(a.faqs or [])

    from blog.models import BlogPost
    search_terms = [role.title, role.department]
    blog_posts = BlogPost.objects.published().none()
    for term in search_terms:
        blog_posts = blog_posts | BlogPost.objects.published().filter(
            Q(title__icontains=term) | Q(excerpt__icontains=term)
        )
    blog_posts = blog_posts.distinct()[:3]

    return render(request, 'pages/az/roles/detail.html', {
        'role': role,
        'recommended_assessments': recommended_assessments,
        'related_roles': related_roles,
        'has_interview_questions': has_interview_questions,
        'focus_areas': all_focus_areas,
        'skills_tested': all_skills,
        'sample_questions': all_samples[:6],
        'use_cases': all_use_cases,
        'faqs': all_faqs,
        'total_duration': total_duration,
        'total_questions': total_questions,
        'blog_posts': blog_posts,
        'lang': 'az',
        'hreflang': _hreflang(f'/assessments/for/{slug}/', f'/az/qiymetlendirmeler/ucun/{slug}/'),
    })
