from django.contrib import admin
from .models import User, Stack, WorkFormat, EmploymentType
from django.urls import path
from django.shortcuts import render
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta


@admin.register(Stack)
class StackAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(WorkFormat)
class WorkFormatAdmin(admin.ModelAdmin):
    list_display = ['code', 'title']
    search_fields = ['code', 'title']
    ordering = ['code']


@admin.register(EmploymentType)
class EmploymentTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'title']
    search_fields = ['code', 'title']
    ordering = ['code']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'telegram_id',
        'username',
        'role',
        'level',
        'is_active',
        'is_profile_completed',
        'created_at'
    ]

    list_filter = [
        'is_active',
        'is_profile_completed',
        'level',
        'notify_mode',
        'created_at'
    ]

    search_fields = [
        'telegram_id',
        'username',
        'role',
        'location'
    ]

    filter_horizontal = [
        'stack',
        'work_formats',
        'employment_types'
    ]

    readonly_fields = [
        'created_at',
        'updated_at'
    ]

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'telegram_id',
                'username',
                'role',
                'level'
            )
        }),
        ('Предпочтения', {
            'fields': (
                'stack',
                'work_formats',
                'employment_types',
                'location',
                'salary_from',
                'currency'
            )
        }),
        ('Настройки', {
            'fields': (
                'notify_mode',
                'is_active',
                'is_profile_completed',
                'onboarding_step'
            )
        }),
        ('Временные метки', {
            'fields': (
                'created_at',
                'updated_at'
            )
        }),
    )

    ordering = ['-created_at']


def analytics_view(request):
    now = timezone.now()
    days = int(request.GET.get("days", 7))

    total_users = User.objects.count()
    users_period = User.objects.filter(
        created_at__gte=now - timedelta(days=days)
    ).count()

    prev_period = User.objects.filter(
        created_at__gte=now - timedelta(days=days * 2),
        created_at__lt=now - timedelta(days=days)
    ).count()

    growth = users_period - prev_period

    by_level = User.objects.values("level").annotate(total=Count("id"))
    by_role = User.objects.values("role").annotate(total=Count("id")).order_by("-total")[:5]

    context = {
        **admin.site.each_context(request),
        "total_users": total_users,
        "users_period": users_period,
        "growth": growth,
        "by_level": by_level,
        "by_role": by_role,
        "days": days,
    }

    return render(request, "admin/analytics.html", context)


def get_admin_urls(original_urls):
    def get_urls():
        urls = original_urls()
        custom = [
            path(
                "analytics/",
                admin.site.admin_view(analytics_view),
                name="analytics",
            )
        ]
        return custom + urls

    return get_urls


admin.site.get_urls = get_admin_urls(admin.site.get_urls)
from django.contrib.auth.models import Group
admin.site.unregister(Group)