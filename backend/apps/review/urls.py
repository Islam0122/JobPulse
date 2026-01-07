from django.urls import path
from .views import CommentCreateView

urlpatterns = [
    path("comments/", CommentCreateView.as_view()),
]
