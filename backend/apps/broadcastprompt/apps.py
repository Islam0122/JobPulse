from django.apps import AppConfig


class BroadcastpromptConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.broadcastprompt'
    verbose_name = "📢 Сообщения пользователям"
    verbose_name_plural = verbose_name

    def ready(self):
        import apps.broadcastprompt.signals


