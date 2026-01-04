from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VacancyViewSet, VacancyNotificationViewSet

router = DefaultRouter()
router.register('vacancies', VacancyViewSet, basename='vacancy')
router.register('vacancy-notifications', VacancyNotificationViewSet, basename='vacancy-notification')

urlpatterns = [
    path('', include(router.urls)),
]