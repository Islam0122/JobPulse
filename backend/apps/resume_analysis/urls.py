from django.urls import path
from .views import (
    ResumeAnalysisCreateView,
    ResumeAnalysisDetailView,
    ResumeAnalysisListView
)

urlpatterns = [
    path(
        "resume-analysis/",
        ResumeAnalysisCreateView.as_view(),
        name="resume-analysis-create"
    ),

    path(
        "resume-analysis/<int:pk>/",
        ResumeAnalysisDetailView.as_view(),
        name="resume-analysis-detail"
    ),

    path(
        "resume-analyses/",
        ResumeAnalysisListView.as_view(),
        name="resume-analysis-list"
    ),
]