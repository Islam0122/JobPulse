from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.utils.html import format_html
from django.utils import timezone

from .models import BroadcastMessage
from .services import send_broadcast_message


@admin.register(BroadcastMessage)
class BroadcastMessageAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "created_at",
        "send_button",
    )

    readonly_fields = ("created_at", "published_at")

    fieldsets = (
        ("📨 Сообщение", {
            "fields": ("subject", "content"),
        }),
        ("🕒 Служебная информация", {
            "fields": ("created_at", "published_at"),
        }),
    )

    # 🔘 КНОПКА / СТАТУС
    def send_button(self, obj):
        if obj.is_published:
            return format_html(
                "<span style='color: green; font-weight: bold;'>✔ Отправлено<br>{}</span>",
                obj.published_at.strftime("%d.%m.%Y %H:%M")
            )

        return format_html(
            "<a class='button' href='send/{}/'>📤 Отправить</a>",
            obj.id
        )

    send_button.short_description = "Рассылка"
    send_button.allow_tags = True

    # 🌐 URL для кнопки
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "send/<int:pk>/",
                self.admin_site.admin_view(self.send_broadcast),
                name="broadcast-send",
            ),
        ]
        return custom_urls + urls

    def send_broadcast(self, request, pk):
        broadcast = BroadcastMessage.objects.get(pk=pk)

        if not broadcast.is_published:
            send_broadcast_message(broadcast)
            broadcast.is_published = True
            broadcast.published_at = timezone.now()
            broadcast.save(update_fields=["is_published", "published_at"])

        return redirect(request.META.get("HTTP_REFERER"))
