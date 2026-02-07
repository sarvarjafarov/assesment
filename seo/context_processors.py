from .models import SeoPage, marketing_meta_defaults


def seo_metadata(request):
    defaults = marketing_meta_defaults(request)
    page = SeoPage.for_path(request.path_info)
    metadata = page.metadata(defaults, request) if page else defaults
    if not metadata.get('canonical_url'):
        metadata['canonical_url'] = request.build_absolute_uri()
    return {'seo_metadata': metadata}
