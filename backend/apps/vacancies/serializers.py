from rest_framework import serializers
from .models import *


class VacancySerializer(serializers.ModelSerializer):
    salary_range = serializers.CharField(read_only=True)
    notified_count = serializers.IntegerField(
        source='notified_users.count',
        read_only=True
    )

    class Meta:
        model = Vacancy
        fields = [
            'id',
            'hh_id',
            'title',
            'company_name',
            'company_url',
            'description',
            'salary_from',
            'salary_to',
            'salary_range',
            'currency',
            'location',
            'experience',
            'employment',
            'schedule',
            'url',
            'skills',
            'published_at',
            'is_active',
            'notified_count',
            'created_at',
        ]


class VacancyListSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для списка вакансий"""
    salary_range = serializers.CharField(read_only=True)

    class Meta:
        model = Vacancy
        fields = [
            'id',
            'title',
            'company_name',
            'salary_range',
            'location',
            'url',
            'published_at',
        ]


class VacancyNotificationSerializer(serializers.ModelSerializer):
    vacancy = VacancyListSerializer(read_only=True)

    class Meta:
        model = VacancyNotification
        fields = [
            'id',
            'vacancy',
            'sent_at',
            'is_viewed',
        ]

class VacancyReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VacancyReaction
        fields = ['id', 'vacancy', 'reaction', 'created_at']
        read_only_fields = ['created_at']


class FavoriteVacancySerializer(serializers.ModelSerializer):
    vacancy = VacancyListSerializer(read_only=True)

    class Meta:
        model = FavoriteVacancy
        fields = ['id', 'vacancy', 'added_at', 'notes']
        read_only_fields = ['added_at']