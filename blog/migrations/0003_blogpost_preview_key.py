from __future__ import annotations

from django.db import migrations, models
import uuid


def populate_preview_keys(apps, schema_editor):
    BlogPost = apps.get_model("blog", "BlogPost")
    for post in BlogPost.objects.filter(preview_key__isnull=True):
        post.preview_key = uuid.uuid4()
        post.save(update_fields=["preview_key"])


def dedupe_preview_keys(apps, schema_editor):
    BlogPost = apps.get_model("blog", "BlogPost")
    seen = set()
    duplicates = []

    for post in BlogPost.objects.exclude(preview_key__isnull=True).order_by("id"):
        key = str(post.preview_key)
        if key in seen:
            duplicates.append(post)
        else:
            seen.add(key)

    for post in duplicates:
        post.preview_key = uuid.uuid4()
        post.save(update_fields=["preview_key"])


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0002_seed_initial_posts"),
    ]

    operations = [
        migrations.AddField(
            model_name="blogpost",
            name="preview_key",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.RunPython(populate_preview_keys, migrations.RunPython.noop),
        migrations.RunPython(dedupe_preview_keys, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="blogpost",
            name="preview_key",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
