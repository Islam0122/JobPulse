from django.db import models


class BroadcastMessage(models.Model):
    subject = models.CharField(
        max_length=255,
        verbose_name="Тема рассылки"
    )
    content = models.TextField(
        verbose_name="Текст сообщения"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано"
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Отправлено"
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name="Опубликовано"
    )

    class Meta:
        db_table = "broadcast_message"
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject
