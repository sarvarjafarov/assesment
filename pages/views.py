from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django import forms

from assessments.forms import AssessmentInviteForm
from assessments.services import send_invite_email
from cms.models import Article, Feature, MarketingCopy, Testimonial


def home(request):
    """Render the marketing landing page."""
    features = Feature.objects.all()
    articles = Article.objects.all()
    testimonials = Testimonial.objects.all()
    marketing = MarketingCopy.current()

    if request.method == "POST":
        form = AssessmentInviteForm(request.POST)
        if form.is_valid():
            try:
                result = form.save(invited_by="Site CTA")
                intro_link = request.build_absolute_uri(
                    reverse("candidate:session-entry", args=[result.session.uuid])
                )
                start_link = request.build_absolute_uri(
                    reverse("candidate:session-start", args=[result.session.uuid])
                )
                send_invite_email(
                    candidate=result.candidate,
                    assessment=result.assessment,
                    session=result.session,
                    intro_link=intro_link,
                    start_link=start_link,
                    invited_by="Site CTA",
                    notes=form.cleaned_data.get("notes", ""),
                )
                messages.success(
                    request,
                    f"Invite created for {result.candidate.first_name} "
                    f"({result.assessment.title}).",
                )
                return redirect(f"{reverse('pages:home')}#cta")
            except forms.ValidationError as exc:
                form.add_error(None, exc)
    else:
        form = AssessmentInviteForm()

    return render(
        request,
        "pages/home.html",
        {
            "features": features,
            "articles": articles,
            "testimonials": testimonials,
            "marketing": marketing,
            "invite_form": form,
        },
    )
