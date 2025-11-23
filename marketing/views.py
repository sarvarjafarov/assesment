from django.http import Http404, HttpResponse

from .models import MarketingSettings


def meta_image(request):
    settings = MarketingSettings.objects.order_by("pk").first()
    if not settings or not settings.has_meta_image:
        raise Http404("Meta image not configured.")
    data, mime = settings.meta_image_response()
    if not data:
        raise Http404("Meta image data missing.")
    response = HttpResponse(data, content_type=mime or "image/png")
    response["Cache-Control"] = "public, max-age=3600"
    return response
