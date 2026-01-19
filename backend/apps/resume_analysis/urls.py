from django.urls import path
from .views import ResumeAnalysisCreateView

urlpatterns = [
    path(
        "resume-analysis/",
        ResumeAnalysisCreateView.as_view(),
        name="resume-analysis-create"
    ),
]
