from django.contrib import admin
from .models import User, Stack, WorkFormat, EmploymentType


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