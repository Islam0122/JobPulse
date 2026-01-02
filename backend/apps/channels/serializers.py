from rest_framework import serializers
from .models import RequiredChannel


class RequiredChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequiredChannel
        fields = (
            "id",
            "title",
            "channel_id",
            "username",
            "is_active",
        )
