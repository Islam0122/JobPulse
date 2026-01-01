from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from .models import User, Stack, WorkFormat, EmploymentType
from .serializers import (
    UserReadSerializer,
    UserWriteSerializer,
    StackSerializer,
    WorkFormatSerializer,
    EmploymentTypeSerializer
)
from .cache import UserCache, ReferenceCache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .cache import UserCache, ReferenceCache


class WorkFormatViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkFormat.objects.all()
    serializer_class = WorkFormatSerializer
    permission_classes = [AllowAny]


class EmploymentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EmploymentType.objects.all()
    serializer_class = EmploymentTypeSerializer
    permission_classes = [AllowAny]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    lookup_field = 'telegram_id'

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return UserWriteSerializer
        return UserReadSerializer

    def retrieve(self, request, telegram_id=None):
        """Получить пользователя с кэшированием"""
        # Пытаемся получить из кэша
        cached_user = UserCache.get_user(telegram_id)
        if cached_user:
            return Response(cached_user)

        # Если нет в кэше, получаем из БД
        user = get_object_or_404(User, telegram_id=telegram_id)
        serializer = self.get_serializer(user)

        # Сохраняем в кэш
        UserCache.set_user(telegram_id, serializer.data)

        return Response(serializer.data)

    def update(self, request, telegram_id=None):
        """Обновление с очисткой кэша"""
        response = super().update(request, telegram_id)
        UserCache.delete_user(telegram_id)
        return response

    def destroy(self, request, telegram_id=None):
        """Удаление с очисткой кэша"""
        response = super().destroy(request, telegram_id)
        UserCache.delete_user(telegram_id)
        return response

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        read_serializer = UserReadSerializer(user)
        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED
        )


    def partial_update(self, request, telegram_id=None):
        user = get_object_or_404(User, telegram_id=telegram_id)
        serializer = self.get_serializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        read_serializer = UserReadSerializer(user)
        return Response(read_serializer.data)



    @action(detail=True, methods=['post'])
    def complete_onboarding(self, request, telegram_id=None):
        user = get_object_or_404(User, telegram_id=telegram_id)
        user.is_profile_completed = True
        user.onboarding_step = None
        user.save()

        serializer = UserReadSerializer(user)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def update_notification_mode(self, request, telegram_id=None):
        user = get_object_or_404(User, telegram_id=telegram_id)
        notify_mode = request.data.get('notify_mode')

        if notify_mode not in ['instant', 'daily', 'weekly']:
            return Response(
                {'error': 'Invalid notification mode'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.notify_mode = notify_mode
        user.save()

        serializer = UserReadSerializer(user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, telegram_id=None):
        user = get_object_or_404(User, telegram_id=telegram_id)
        user.is_active = not user.is_active
        user.save()

        serializer = UserReadSerializer(user)
        return Response(serializer.data)


class StackViewSet(viewsets.ReadOnlyModelViewSet):
    @method_decorator(cache_page(3600))
    def list(self, request):
        return super().list(request)