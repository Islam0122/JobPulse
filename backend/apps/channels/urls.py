from django.urls import path
from .views import RequiredChannelListAPIView

urlpatterns = [
    path(
        "required-channels/",
        RequiredChannelListAPIView.as_view(),
        name="required-channels"
    ),
]
