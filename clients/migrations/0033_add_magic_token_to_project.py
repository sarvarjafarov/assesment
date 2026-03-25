import secrets
from django.db import migrations, models


def populate_magic_tokens(apps, schema_editor):
    ClientProject = apps.get_model("clients", "ClientProject")
    for project in ClientProject.objects.all():
        if not project.magic_token:
            project.magic_token = secrets.token_urlsafe(16)
            project.save(update_fields=["magic_token"])


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0032_add_pipeline_candidate_to_positionapplication'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientproject',
            name='magic_token',
            field=models.CharField(
                blank=True, db_index=True, default='',
                help_text='Shareable invite link token', max_length=32,
            ),
        ),
        migrations.RunPython(populate_magic_tokens, migrations.RunPython.noop),
    ]
