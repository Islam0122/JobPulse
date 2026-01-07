from django.contrib import admin
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "short_text",
        "created_at",
    )
    list_filter = (
        "created_at",
    )
    search_fields = (
        "text",
        "user__username",
        "user__email",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Основная информация", {
            "fields": ("user", "text")
        }),
        ("Служебные поля", {
            "fields": ("created_at",)
        }),
    )

    def short_text(self, obj):
        return obj.text[:50] + "…" if len(obj.text) > 50 else obj.text

    short_text.short_description = "Комментарий"
