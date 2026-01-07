from rest_framework import serializers
from .models import Comment
from ..users.models import User


class CommentCreateSerializer(serializers.ModelSerializer):
    telegram_id = serializers.IntegerField(
        write_only=True,
        help_text="Telegram ID пользователя"
    )

    class Meta:
        model = Comment
        fields = ("telegram_id", "text")

    def create(self, validated_data):
        telegram_id = validated_data.pop("telegram_id")

        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "role": "unknown",
                "is_active": True,
            }
        )
        return Comment.objects.create(
            user=user,
            **validated_data
        )
