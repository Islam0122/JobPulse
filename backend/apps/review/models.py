from django.db import models
from ..users.models import User


class Comment(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Пользователь",
        help_text="Пользователь, оставивший комментарий в боте"
    )
    text = models.TextField(
        verbose_name="Текст комментария",
        help_text="Сообщение, отправленное пользователем через команду /comment"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
        help_text="Дата и время создания комментария"
    )
    def __str__(self):
        return f"{self.user} → {self.created_at.strftime('%d.%m.%Y %H:%M')}"

    class Meta:
        db_table = "comment"
        ordering = ["-created_at"]
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
