from django.contrib import admin
from .models import ResumeAnalysis


@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "user__id",
        "resume_text",
    )

    readonly_fields = (
        "created_at",
        "result",
        "error",
    )

    ordering = ("-created_at",)

    fieldsets = (
        (
            "General",
            {
                "fields": (
                    "user",
                    "status",
                    "created_at",
                )
            },
        ),
        (
            "Resume",
            {
                "fields": (
                    "resume_text",
                )
            },
        ),
        (
            "AI Analysis",
            {
                "fields": (
                    "result",
                    "error",
                )
            },
        ),
    )
