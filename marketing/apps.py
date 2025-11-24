from django.apps import AppConfig
from django.conf import settings


class MarketingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'marketing'

    def ready(self):
        from django.db import OperationalError, ProgrammingError
        from django.db.models.signals import post_save

        from .models import MarketingSettings

        def _apply(instance: MarketingSettings):
            has_creds = getattr(instance, "has_smtp_credentials", None)
            if not instance or not callable(has_creds) or not has_creds():
                return
            smtp_config = getattr(instance, "smtp_config", None)
            if not callable(smtp_config):
                return
            config = smtp_config()
            for key, value in config.items():
                setattr(settings, key, value)

        def _initialize():
            try:
                instance = MarketingSettings.objects.order_by("pk").first()
            except (OperationalError, ProgrammingError):
                return
            if instance:
                _apply(instance)

        def _handle_save(sender, instance, **kwargs):
            _apply(instance)

        _initialize()
        post_save.connect(_handle_save, sender=MarketingSettings, dispatch_uid="marketing_apply_email_settings")
