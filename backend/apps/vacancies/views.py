from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Vacancy, VacancyNotification
from .serializers import (
    VacancySerializer,
    VacancyListSerializer,
    VacancyNotificationSerializer
)
from .services import get_user_recommended_vacancies
from apps.users.models import User


class VacancyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра вакансий

    Endpoints:
    - GET /api/vacancies/ - список всех активных вакансий
    - GET /api/vacancies/{id}/ - детали вакансии
    - GET /api/vacancies/recommended/?telegram_id=123 - рекомендованные вакансии
    """
    queryset = Vacancy.objects.filter(is_active=True)
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = ['location', 'currency', 'employment']
    search_fields = ['title', 'company_name', 'description']
    ordering_fields = ['published_at', 'salary_from', 'created_at']
    ordering = ['-published_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return VacancyListSerializer
        return VacancySerializer

    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """
        Получить рекомендованные вакансии для пользователя

        Query params:
        - telegram_id: ID пользователя в Telegram
        - limit: Количество вакансий (по умолчанию 10)
        """
        telegram_id = request.query_params.get('telegram_id')
        limit = int(request.query_params.get('limit', 10))

        if not telegram_id:
            return Response(
                {"error": "telegram_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        vacancies = get_user_recommended_vacancies(user, limit=limit)
        serializer = VacancyListSerializer(vacancies, many=True)

        return Response({
            "count": len(vacancies),
            "results": serializer.data
        })

    @action(detail=True, methods=['post'])
    def mark_viewed(self, request, pk=None):
        """
        Отметить вакансию как просмотренную

        Body:
        - telegram_id: ID пользователя
        """
        vacancy = self.get_object()
        telegram_id = request.data.get('telegram_id')

        if not telegram_id:
            return Response(
                {"error": "telegram_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(telegram_id=telegram_id)
            notification = VacancyNotification.objects.get(
                user=user,
                vacancy=vacancy
            )
            notification.is_viewed = True
            notification.save()

            return Response({"status": "marked as viewed"})
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except VacancyNotification.DoesNotExist:
            return Response(
                {"error": "Notification not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class VacancyNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра уведомлений о вакансиях

    Endpoints:
    - GET /api/vacancy-notifications/?telegram_id=123 - все уведомления пользователя
    """
    serializer_class = VacancyNotificationSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['is_viewed']
    ordering = ['-sent_at']

    def get_queryset(self):
        telegram_id = self.request.query_params.get('telegram_id')

        if not telegram_id:
            return VacancyNotification.objects.none()

        try:
            user = User.objects.get(telegram_id=telegram_id)
            return VacancyNotification.objects.filter(user=user)
        except User.DoesNotExist:
            return VacancyNotification.objects.none()