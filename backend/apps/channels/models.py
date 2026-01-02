from django.db import models


class RequiredChannel(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name="Название канала"
    )
    channel_id = models.BigIntegerField(
        unique=True,
        verbose_name="ID канала"
    )
    username = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Username канала"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Обязательный канал"
        verbose_name_plural = "Обязательные каналы"

    def __str__(self):
        return self.title
