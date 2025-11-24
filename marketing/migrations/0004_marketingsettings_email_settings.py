from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketing", "0003_auto_populate_asset_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="marketingsettings",
            name="default_from_email",
            field=models.CharField(
                blank=True,
                help_text="Default From header for transactional messages.",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="marketingsettings",
            name="email_host",
            field=models.CharField(
                blank=True,
                help_text="SMTP host provided by your email provider (e.g., smtp-relay.brevo.com).",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="marketingsettings",
            name="email_password",
            field=models.CharField(
                blank=True,
                help_text="SMTP password or API key.",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="marketingsettings",
            name="email_port",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="SMTP port, usually 587 for TLS.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="marketingsettings",
            name="email_use_tls",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="marketingsettings",
            name="email_username",
            field=models.CharField(
                blank=True,
                help_text="SMTP login/username.",
                max_length=255,
            ),
        ),
    ]
