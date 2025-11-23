import mimetypes

from django.db import migrations


def populate_asset_blobs(apps, schema_editor):
    Settings = apps.get_model("marketing", "MarketingSettings")
    for settings in Settings.objects.all():
        updated = False
        for field in ("favicon", "meta_image"):
            file_field = getattr(settings, field)
            if file_field and file_field.storage.exists(file_field.name):
                with file_field.open("rb") as source:
                    data = source.read()
                mime = mimetypes.guess_type(file_field.name)[0] or "image/png"
                setattr(settings, f"{field}_data", data)
                setattr(settings, f"{field}_mime", mime)
                file_field.delete(save=False)
                setattr(settings, field, None)
                updated = True
        if updated:
            settings.save(update_fields=[
                "favicon_data",
                "favicon_mime",
                "meta_image_data",
                "meta_image_mime",
            ])


class Migration(migrations.Migration):

    dependencies = [
        ("marketing", "0002_marketingsettings_favicon_data_and_more"),
    ]

    operations = [
        migrations.RunPython(populate_asset_blobs, migrations.RunPython.noop),
    ]
