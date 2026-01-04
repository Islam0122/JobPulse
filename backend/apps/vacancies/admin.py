from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from .models import Vacancy, VacancyNotification, ParsingLog
from .tasks import parse_hh_vacancies


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "company_name",
        "salary_display",
        "location",
        "published_at",
        "is_active",
        "notified_count",
        "hh_link"
    )

    list_filter = (
        "is_active",
        "currency",
        "location",
        "published_at",
        "created_at",
    )

    search_fields = (
        "title",
        "company_name",
        "hh_id",
        "description",
    )

    readonly_fields = (
        "hh_id",
        "created_at",
        "updated_at",
        "published_at",
        "notified_count",
    )

    fieldsets = (
        ("Основная информация", {
            "fields": (
                "hh_id",
                "title",
                "company_name",
                "company_url",
                "url",
            )
        }),
        ("Зарплата и условия", {
            "fields": (
                "salary_from",
                "salary_to",
                "currency",
                "location",
                "experience",
                "employment",
                "schedule",
            )
        }),
        ("Описание", {
            "fields": (
                "description",
                "skills",
            )
        }),
        ("Служебная информация", {
            "fields": (
                "is_active",
                "published_at",
                "created_at",
                "updated_at",
                "notified_count",
            )
        }),
    )

    date_hierarchy = "published_at"

    def salary_display(self, obj):
        return obj.salary_range

    salary_display.short_description = "Зарплата"

    def notified_count(self, obj):
        count = obj.notified_users.count()
        return format_html(
            '<span style="color: {};">{} чел.</span>',
            "green" if count > 0 else "gray",
            count
        )

    notified_count.short_description = "Уведомлено"

    def hh_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank">🔗 HH.ru</a>',
            obj.url
        )

    hh_link.short_description = "Ссылка"

    actions = ["activate_vacancies", "deactivate_vacancies"]

    def activate_vacancies(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Активировано вакансий: {updated}")

    activate_vacancies.short_description = "✅ Активировать выбранные"

    def deactivate_vacancies(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано вакансий: {updated}")

    deactivate_vacancies.short_description = "❌ Деактивировать выбранные"


@admin.register(VacancyNotification)
class VacancyNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "vacancy",
        "sent_at",
        "is_viewed",
    )

    list_filter = (
        "is_viewed",
        "sent_at",
    )

    search_fields = (
        "user__username",
        "user__telegram_id",
        "vacancy__title",
    )

    readonly_fields = (
        "user",
        "vacancy",
        "sent_at",
    )

    date_hierarchy = "sent_at"


@admin.register(ParsingLog)
class ParsingLogAdmin(admin.ModelAdmin):
    list_display = (
        "started_at",
        "status_display",
        "duration",
        "total_found",
        "new_vacancies",
        "updated_vacancies",
    )

    list_filter = (
        "status",
        "started_at",
    )

    readonly_fields = (
        "started_at",
        "finished_at",
        "total_found",
        "new_vacancies",
        "updated_vacancies",
        "errors",
        "status",
        "duration",
    )

    fieldsets = (
        ("Информация о парсинге", {
            "fields": (
                "started_at",
                "finished_at",
                "duration",
                "status",
            )
        }),
        ("Результаты", {
            "fields": (
                "total_found",
                "new_vacancies",
                "updated_vacancies",
            )
        }),
        ("Ошибки", {
            "fields": ("errors",)
        }),
    )

    date_hierarchy = "started_at"

    def status_display(self, obj):
        colors = {
            "running": "blue",
            "completed": "green",
            "failed": "red",
        }
        color = colors.get(obj.status, "gray")

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )

    status_display.short_description = "Статус"

    def duration(self, obj):
        if obj.finished_at and obj.started_at:
            delta = obj.finished_at - obj.started_at
            seconds = int(delta.total_seconds())
            if seconds < 60:
                return f"{seconds} сек"
            elif seconds < 3600:
                return f"{seconds // 60} мин {seconds % 60} сек"
            else:
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                return f"{hours} ч {minutes} мин"
        return "-"

    duration.short_description = "Длительность"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'run-parsing/',
                self.admin_site.admin_view(self.run_parsing),
                name='run-parsing',
            ),
        ]
        return custom_urls + urls

    def run_parsing(self, request):
        """Ручной запуск парсинга через админку"""
        parse_hh_vacancies.delay()
        self.message_user(request, "✅ Парсинг запущен в фоне")
        return redirect("..")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_run_button'] = True
        return super().changelist_view(request, extra_context=extra_context)