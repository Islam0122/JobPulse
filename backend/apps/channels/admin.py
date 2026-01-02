from django.contrib import admin
from .models import RequiredChannel


@admin.register(RequiredChannel)
class RequiredChannelAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "channel_id",
        "username",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active",)
    search_fields = ("title", "username", "channel_id")
