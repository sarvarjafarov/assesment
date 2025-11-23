import mimetypes

from django.db import migrations


def migrate_logos(apps, schema_editor):
    ClientAccount = apps.get_model("clients", "ClientAccount")
    for account in ClientAccount.objects.exclude(logo="").iterator():
        field = account.logo
        if not field:
            continue
        try:
            with field.open("rb") as source:
                data = source.read()
        except FileNotFoundError:
            continue
        if not data:
            continue
        mime = mimetypes.guess_type(field.name)[0] or "image/png"
        account.logo_data = data
        account.logo_mime = mime
        field.delete(save=False)
        account.logo = None
        account.save(update_fields=["logo", "logo_data", "logo_mime"])


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0012_clientaccount_logo_data_clientaccount_logo_mime"),
    ]

    operations = [
        migrations.RunPython(migrate_logos, migrations.RunPython.noop),
    ]
