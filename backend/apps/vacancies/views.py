from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from .models import *
from .serializers import *
from .services import get_user_recommended_vacancies
from apps.users.models import User
from django.core.cache import cache


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
        """Отметить вакансию как просмотренную"""
        vacancy = self.get_object()
        telegram_id = request.data.get('telegram_id')

        if not telegram_id:
            return Response(
                {"error": "telegram_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(telegram_id=telegram_id)

            notification, created = VacancyNotification.objects.get_or_create(
                user=user,
                vacancy=vacancy,
                defaults={'is_viewed': False}
            )

            notification.is_viewed = True
            notification.viewed_at = timezone.now()
            notification.save()

            return Response({"status": "marked as viewed"})
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """
        Отреагировать на вакансию (like/dislike)

        Body:
        - telegram_id: ID пользователя
        - reaction: 'like' или 'dislike'
        """
        vacancy = self.get_object()
        telegram_id = request.data.get('telegram_id')
        reaction = request.data.get('reaction')

        if not telegram_id or reaction not in ['like', 'dislike']:
            return Response(
                {"error": "Invalid parameters"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        reaction_obj, created = VacancyReaction.objects.update_or_create(
            user=user,
            vacancy=vacancy,
            defaults={'reaction': reaction}
        )

        cache.delete(f"user_recommendations:{telegram_id}")

        return Response({
            "status": "success",
            "reaction": reaction,
            "created": created
        })

    @action(detail=True, methods=['post'])
    def add_to_favorites(self, request, pk=None):
        """
        Добавить вакансию в избранное

        Body:
        - telegram_id: ID пользователя
        - notes: (опционально) заметки
        """
        vacancy = self.get_object()
        telegram_id = request.data.get('telegram_id')
        notes = request.data.get('notes', '')

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

        favorite, created = FavoriteVacancy.objects.get_or_create(
            user=user,
            vacancy=vacancy,
            defaults={'notes': notes}
        )

        if not created:
            return Response(
                {"status": "already_exists"},
                status=status.HTTP_200_OK
            )

        return Response({
            "status": "added",
            "favorite_id": favorite.id
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'])
    def remove_from_favorites(self, request, pk=None):
        """Удалить из избранного"""
        vacancy = self.get_object()
        telegram_id = request.query_params.get('telegram_id')

        if not telegram_id:
            return Response(
                {"error": "telegram_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(telegram_id=telegram_id)
            favorite = FavoriteVacancy.objects.get(user=user, vacancy=vacancy)
            favorite.delete()

            return Response({"status": "removed"})
        except (User.DoesNotExist, FavoriteVacancy.DoesNotExist):
            return Response(
                {"error": "Not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def favorites(self, request):
        """
        Получить избранные вакансии пользователя

        Query params:
        - telegram_id: ID пользователя
        """
        telegram_id = request.query_params.get('telegram_id')

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

        favorites = FavoriteVacancy.objects.filter(user=user).select_related('vacancy')
        serializer = FavoriteVacancySerializer(favorites, many=True)

        return Response({
            "count": favorites.count(),
            "results": serializer.data
        })

    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        История просмотренных вакансий

        Query params:
        - telegram_id: ID пользователя
        """
        telegram_id = request.query_params.get('telegram_id')

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

        viewed_notifications = VacancyNotification.objects.filter(
            user=user,
            is_viewed=True
        ).select_related('vacancy').order_by('-sent_at')[:50]

        vacancies = [n.vacancy for n in viewed_notifications]
        serializer = VacancyListSerializer(vacancies, many=True)

        return Response({
            "count": len(vacancies),
            "results": serializer.data
        })


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