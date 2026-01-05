from django.apps import AppConfig


class ChannelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.channels'
    verbose_name = "📺 Каналы"
    verbose_name_plural = verbose_name

    def ready(self):
        import apps.channels.signals