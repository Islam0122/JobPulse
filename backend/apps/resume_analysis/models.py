from django.db import models
from ..users.models import User


class ResumeAnalysis(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("done", "Done"),
        ("failed", "Failed"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="resume_analyses",
        verbose_name="User",
        help_text="Пользователь, запросивший AI-анализ резюме"
    )

    resume_text = models.TextField(
        verbose_name="Resume text",
        help_text="Извлечённый и нормализованный текст резюме, полученный от бота"
    )

    result = models.JSONField(
        null=True,
        blank=True,
        verbose_name="AI analysis result",
        help_text="Результат AI-анализа резюме: сильные стороны, слабые места и рекомендации"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="Analysis status",
        help_text="Текущий статус процесса AI-анализа"
    )

    error = models.TextField(
        blank=True,
        verbose_name="Error message",
        help_text="Текст ошибки, если анализ завершился неуспешно"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at",
        help_text="Дата и время создания запроса на анализ резюме"
    )

    class Meta:
        db_table = "resume_analysis"
        verbose_name = "Resume analysis"
        verbose_name_plural = "Resume analyses"
        ordering = ("-created_at",)

    def __str__(self):
        return f"ResumeAnalysis #{self.id} ({self.user_id}) — {self.status}"
