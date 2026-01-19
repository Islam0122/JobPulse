from rest_framework import serializers
from .models import ResumeAnalysis
from ..users.models import User


class ResumeAnalysisSerializer(serializers.ModelSerializer):
    telegram_id = serializers.IntegerField(
        write_only=True,
        help_text="Telegram ID пользователя, отправившего резюме"
    )

    class Meta:
        model = ResumeAnalysis
        fields = (
            "telegram_id",     # приходит от бота
            "resume_text",     # приходит от бота
            "id",              # возвращаем клиенту
            "status",          # возвращаем клиенту
            "result",          # опционально (когда done)
            "error",           # если failed
            "created_at",      # для отображения
        )
        read_only_fields = (
            "id",
            "status",
            "result",
            "error",
            "created_at",
        )

    def create(self, validated_data):
        telegram_id = validated_data.pop("telegram_id")

        user, _ = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "role": "unknown",
                "is_active": True,
            }
        )

        return ResumeAnalysis.objects.create(
            user=user,
            **validated_data
        )
