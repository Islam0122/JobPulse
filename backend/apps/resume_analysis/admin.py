from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
import json
from .models import ResumeAnalysis


class StatusFilter(admin.SimpleListFilter):
    """Фильтр по статусу с подсчётом количества"""
    title = 'Статус анализа'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        counts = ResumeAnalysis.objects.values('status').annotate(
            count=Count('id')
        )
        status_dict = dict(ResumeAnalysis.STATUS_CHOICES)

        return [
            (status_data['status'], f"{status_dict.get(status_data['status'])} ({status_data['count']})")
            for status_data in counts
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class ScoreFilter(admin.SimpleListFilter):
    """Фильтр по оценке резюме"""
    title = 'Оценка резюме'
    parameter_name = 'score'

    def lookups(self, request, model_admin):
        return [
            ('high', '🔥 Высокая (8.0+)'),
            ('medium', '👍 Средняя (5.0-7.9)'),
            ('low', '⚠️ Низкая (<5.0)'),
            ('no_score', '❓ Без оценки'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'high':
            return queryset.filter(
                result__overall_score__gte=8.0
            )
        elif self.value() == 'medium':
            return queryset.filter(
                result__overall_score__gte=5.0,
                result__overall_score__lt=8.0
            )
        elif self.value() == 'low':
            return queryset.filter(
                result__overall_score__lt=5.0
            )
        elif self.value() == 'no_score':
            return queryset.filter(
                Q(result__isnull=True) | Q(result__overall_score__isnull=True)
            )
        return queryset


class DomainFilter(admin.SimpleListFilter):
    title = 'Сфера деятельности'
    parameter_name = 'domain'

    def lookups(self, request, model_admin):
        domains = ResumeAnalysis.objects.exclude(
            result__isnull=True
        ).values_list('result__detected_domain', flat=True).distinct()

        domain_icons = {
            'IT': '💻',
            'design': '🎨',
            'marketing': '📈',
            'finance': '💰',
            'sales': '🤝',
            'management': '👔',
            'other': '📋',
            'unknown': '❓',
        }

        return [
            (domain, f"{domain_icons.get(domain, '📌')} {domain.capitalize()}")
            for domain in domains if domain
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(result__detected_domain=self.value())
        return queryset


@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "id_with_link",
        "user_info",
        "status_badge",
        "score_badge",
        "domain_badge",
        "level_badge",
        "created_at_formatted",
        "quick_actions",
    )

    list_filter = (
        StatusFilter,
        ScoreFilter,
        DomainFilter,
        "created_at",
    )

    search_fields = (
        "id",
        "user__telegram_id",
        "user__first_name",
        "user__last_name",
        "resume_text",
        "result__detected_domain",
    )

    readonly_fields = (
        "id",
        "created_at",
        "result_preview",
        "error_display",
        "resume_preview",
        "analysis_metadata",
    )

    ordering = ("-created_at",)

    list_per_page = 25

    date_hierarchy = "created_at"

    fieldsets = (
        (
            "🔍 Основная информация",
            {
                "fields": (
                    "id",
                    "user",
                    "status",
                    "created_at",
                )
            },
        ),
        (
            "📄 Резюме",
            {
                "fields": (
                    "resume_preview",
                    "resume_text",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "🤖 AI Анализ",
            {
                "fields": (
                    "result_preview",
                    "result",
                ),
            },
        ),
        (
            "📊 Метаданные",
            {
                "fields": (
                    "analysis_metadata",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "❌ Ошибки",
            {
                "fields": (
                    "error_display",
                    "error",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    actions = [
        "mark_as_pending",
        "mark_as_failed",
        "export_results_json",
    ]

    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status="pending")
        self.message_user(request, f"Обновлено записей: {updated}")

    mark_as_pending.short_description = "🔄 Пометить как ожидающие"

    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status="failed", error="Отменено администратором")
        self.message_user(request, f"Отменено записей: {updated}")

    mark_as_failed.short_description = "❌ Пометить как неудачные"

    def export_results_json(self, request, queryset):
        """Экспорт результатов в JSON"""
        # Здесь можно добавить экспорт в файл
        count = queryset.filter(status="done").count()
        self.message_user(request, f"Готово к экспорту: {count} анализов")

    export_results_json.short_description = "📥 Экспортировать результаты"


    def id_with_link(self, obj):
        url = reverse("admin:resume_analysis_resumeanalysis_change", args=[obj.pk])
        return format_html('<a href="{}" style="font-weight: bold;">#{}</a>', url, obj.id)

    id_with_link.short_description = "ID"
    id_with_link.admin_order_field = "id"

    def user_info(self, obj):
        user = obj.user
        url = reverse("admin:users_user_change", args=[user.pk])

        name_parts = []
        if hasattr(user, 'first_name') and user.first_name:
            name_parts.append(user.first_name)
        if hasattr(user, 'last_name') and user.last_name:
            name_parts.append(user.last_name)

        name = " ".join(name_parts) if name_parts else f"User #{user.pk}"
        telegram_id = user.telegram_id

        role_html = ""
        if hasattr(user, 'role') and user.role:
            role_html = user.role

        return format_html(
            '<a href="{}" style="text-decoration: none;">'
            '<strong>{}</strong><br>'
            '<span style="color: #666; font-size: 11px;">TG: {}</span>'
            '<br><span style="color: #999; font-size: 10px;">Role: {}</span>'
            '</a>',
            url, name, telegram_id, role_html
        )

    user_info.short_description = "👤 Пользователь"

    def status_badge(self, obj):
        status_styles = {
            "pending": ("⏳", "#FFA500", "Ожидает"),
            "processing": ("⚙️", "#2196F3", "Обработка"),
            "done": ("✅", "#4CAF50", "Готово"),
            "failed": ("❌", "#F44336", "Ошибка"),
        }

        emoji, color, label = status_styles.get(
            obj.status,
            ("❓", "#999", obj.status)
        )

        return format_html(
            '<span style="'
            'background: {}; '
            'color: white; '
            'padding: 4px 10px; '
            'border-radius: 12px; '
            'font-size: 11px; '
            'font-weight: bold; '
            'white-space: nowrap;'
            '">{} {}</span>',
            color, emoji, label
        )

    status_badge.short_description = "Статус"
    status_badge.admin_order_field = "status"

    def score_badge(self, obj):
        if not obj.result or "overall_score" not in obj.result:
            return format_html(
                '<span style="color: #999; font-size: 11px;">—</span>'
            )

        score = obj.result.get("overall_score", 0)

        if score >= 8.0:
            color = "#4CAF50"
            emoji = "🔥"
        elif score >= 5.0:
            color = "#FFA500"
            emoji = "👍"
        else:
            color = "#F44336"
            emoji = "⚠️"

        return format_html(
            '<span style="'
            'background: {}; '
            'color: white; '
            'padding: 4px 10px; '
            'border-radius: 12px; '
            'font-size: 12px; '
            'font-weight: bold;'
            '">{} {}/10</span>',
            color, emoji, score
        )

    score_badge.short_description = "Оценка"

    def domain_badge(self, obj):
        if not obj.result or "detected_domain" not in obj.result:
            return "—"

        domain = obj.result.get("detected_domain", "unknown")

        domain_icons = {
            "IT": "💻",
            "design": "🎨",
            "marketing": "📈",
            "finance": "💰",
            "sales": "🤝",
            "management": "👔",
            "other": "📋",
            "unknown": "❓",
        }

        emoji = domain_icons.get(domain, "📌")

        return format_html(
            '<span style="font-size: 12px;">{} {}</span>',
            emoji, domain.capitalize()
        )

    domain_badge.short_description = "Сфера"

    def level_badge(self, obj):
        if not obj.result or "detected_level" not in obj.result:
            return "—"

        level = obj.result.get("detected_level", "unknown")

        level_colors = {
            "junior": "#9C27B0",
            "middle": "#2196F3",
            "senior": "#FF9800",
            "lead": "#F44336",
            "unknown": "#999",
        }

        color = level_colors.get(level, "#999")

        return format_html(
            '<span style="'
            'color: {}; '
            'font-weight: bold; '
            'font-size: 11px;'
            '">{}</span>',
            color, level.upper()
        )

    level_badge.short_description = "Уровень"

    def created_at_formatted(self, obj):
        delta = timezone.now() - obj.created_at

        if delta.days == 0:
            if delta.seconds < 3600:
                minutes = delta.seconds // 60
                relative = f"{minutes} мин назад"
            else:
                hours = delta.seconds // 3600
                relative = f"{hours} ч назад"
        elif delta.days == 1:
            relative = "Вчера"
        else:
            relative = f"{delta.days} дн назад"

        return format_html(
            '<span title="{}">{}<br>'
            '<small style="color: #666;">{}</small></span>',
            obj.created_at.strftime("%d.%m.%Y %H:%M:%S"),
            obj.created_at.strftime("%d.%m.%Y"),
            relative
        )

    created_at_formatted.short_description = "📅 Создано"
    created_at_formatted.admin_order_field = "created_at"

    def quick_actions(self, obj):
        url = reverse("admin:resume_analysis_resumeanalysis_change", args=[obj.pk])

        return format_html(
            '<a href="{}" style="'
            'background: #2196F3; '
            'color: white; '
            'padding: 4px 8px; '
            'border-radius: 4px; '
            'text-decoration: none; '
            'font-size: 11px;'
            '">Открыть</a>',
            url
        )

    quick_actions.short_description = "Действия"

    def resume_preview(self, obj):
        if not obj.resume_text:
            return format_html('<em style="color: #999;">Нет текста</em>')

        preview = obj.resume_text[:300]
        if len(obj.resume_text) > 300:
            preview += "..."

        return format_html(
            '<div style="'
            'background: #f5f5f5; '
            'padding: 15px; '
            'border-left: 4px solid #2196F3; '
            'border-radius: 4px; '
            'font-family: monospace; '
            'white-space: pre-wrap;'
            '">{}</div>'
            '<p style="margin-top: 10px; color: #666; font-size: 12px;">'
            'Длина: {} символов'
            '</p>',
            preview,
            len(obj.resume_text)
        )

    resume_preview.short_description = "📄 Превью резюме"

    def result_preview(self, obj):
        if not obj.result:
            return format_html('<em style="color: #999;">Анализ не завершён</em>')

        result = obj.result

        html = '<div style="background: #f5f5f5; padding: 20px; border-radius: 8px;">'

        summary = result.get("summary", "—")
        html += f'<p style="margin: 0 0 15px 0; font-size: 14px;"><strong>Резюме:</strong> {summary}</p>'

        score = result.get("overall_score", 0)
        html += f'<p style="margin: 0 0 15px 0;"><strong>Оценка:</strong> <span style="font-size: 18px; font-weight: bold; color: #2196F3;">{score}/10</span></p>'

        strengths = result.get("strengths", [])
        if strengths:
            html += '<p style="margin: 0; font-weight: bold;">✅ Сильные стороны:</p><ul style="margin: 5px 0 15px 20px;">'
            for strength in strengths[:3]:
                html += f'<li>{strength}</li>'
            html += '</ul>'

        weaknesses = result.get("weaknesses", [])
        if weaknesses:
            html += '<p style="margin: 0; font-weight: bold;">⚠️ Слабые стороны:</p><ul style="margin: 5px 0 15px 20px;">'
            for weakness in weaknesses[:3]:
                html += f'<li>{weakness}</li>'
            html += '</ul>'

        recommendations = result.get("recommendations", [])
        if recommendations:
            html += '<p style="margin: 0; font-weight: bold;">💡 Рекомендации:</p><ul style="margin: 5px 0 0 20px;">'
            for rec in recommendations[:3]:
                html += f'<li>{rec}</li>'
            html += '</ul>'

        html += '</div>'

        return format_html(html)

    result_preview.short_description = "🤖 Результат AI анализа"

    def error_display(self, obj):
        if not obj.error:
            return format_html('<em style="color: #4CAF50;">✅ Ошибок нет</em>')

        return format_html(
            '<div style="'
            'background: #FFEBEE; '
            'color: #C62828; '
            'padding: 15px; '
            'border-left: 4px solid #F44336; '
            'border-radius: 4px;'
            '">{}</div>',
            obj.error
        )

    error_display.short_description = "❌ Ошибка"

    def analysis_metadata(self, obj):
        if not obj.result:
            return format_html('<em style="color: #999;">Нет данных</em>')

        result = obj.result

        metadata = {
            "Сфера": result.get("detected_domain", "—"),
            "Уровень": result.get("detected_level", "—"),
            "Конкурентоспособность": result.get("market_competitiveness", "—"),
            "Год анализа": result.get("market_year", "—"),
        }

        html = '<table style="width: 100%; border-collapse: collapse;">'
        for key, value in metadata.items():
            html += f'''
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 8px; font-weight: bold; width: 200px;">{key}</td>
                    <td style="padding: 8px;">{value}</td>
                </tr>
            '''
        html += '</table>'

        return format_html(html)

    analysis_metadata.short_description = "📊 Метаданные"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')

    def has_add_permission(self, request):
        return False

    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
