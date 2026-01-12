from typing import Literal
from django.db.models import QuerySet, Count, Q
from .models import Vacancy


def get_vacancy_source(vacancy: Vacancy) -> Literal['hh', 'devkg']:
    """
    Определить источник вакансии по hh_id

    Args:
        vacancy: Объект вакансии

    Returns:
        'hh' или 'devkg'
    """
    if vacancy.hh_id.startswith('devkg_'):
        return 'devkg'
    return 'hh'


def filter_by_source(queryset: QuerySet, source: Literal['hh', 'devkg', 'all'] = 'all') -> QuerySet:
    """
    Фильтровать вакансии по источнику

    Args:
        queryset: QuerySet вакансий
        source: 'hh', 'devkg' или 'all'

    Returns:
        Отфильтрованный QuerySet
    """
    if source == 'hh':
        return queryset.filter(hh_id__regex=r'^\d+$')
    elif source == 'devkg':
        return queryset.filter(hh_id__startswith='devkg_')
    return queryset


def get_vacancies_stats(source: Literal['hh', 'devkg', 'all'] = 'all') -> dict:
    """
    Получить статистику по вакансиям

    Args:
        source: Источник для статистики

    Returns:
        Словарь со статистикой
    """
    queryset = Vacancy.objects.all()

    if source == 'hh':
        queryset = queryset.filter(hh_id__regex=r'^\d+$')
    elif source == 'devkg':
        queryset = queryset.filter(hh_id__startswith='devkg_')

    stats = queryset.aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(is_active=True)),
        inactive=Count('id', filter=Q(is_active=False)),
        with_salary=Count('id', filter=Q(salary_from__isnull=False))
    )

    return {
        'source': source,
        'total_vacancies': stats['total'],
        'active_vacancies': stats['active'],
        'inactive_vacancies': stats['inactive'],
        'vacancies_with_salary': stats['with_salary'],
    }


def get_all_sources_stats() -> dict:
    """
    Получить статистику по всем источникам

    Returns:
        Словарь со статистикой по каждому источнику
    """
    all_vacancies = Vacancy.objects.aggregate(
        total=Count('id'),
        hh_count=Count('id', filter=Q(hh_id__regex=r'^\d+$')),
        devkg_count=Count('id', filter=Q(hh_id__startswith='devkg_')),
        active=Count('id', filter=Q(is_active=True)),
    )

    return {
        'total': all_vacancies['total'],
        'active': all_vacancies['active'],
        'sources': {
            'hh': all_vacancies['hh_count'],
            'devkg': all_vacancies['devkg_count'],
        }
    }


def get_recent_vacancies(source: Literal['hh', 'devkg', 'all'] = 'all', limit: int = 10) -> QuerySet:
    """
    Получить последние вакансии

    Args:
        source: Источник вакансий
        limit: Количество вакансий

    Returns:
        QuerySet последних вакансий
    """
    queryset = Vacancy.objects.filter(is_active=True)
    queryset = filter_by_source(queryset, source)
    return queryset.order_by('-published_at')[:limit]


def format_vacancy_source_display(vacancy: Vacancy) -> str:
    """
    Форматировать отображение источника вакансии

    Args:
        vacancy: Объект вакансии

    Returns:
        Строка с названием источника
    """
    source = get_vacancy_source(vacancy)

    source_names = {
        'hh': '🔵 HH.ru',
        'devkg': '🟢 Dev.kg'
    }

    return source_names.get(source, '❓ Неизвестно')


"""
from apps.vacancies.utils import *

# Статистика
stats = get_all_sources_stats()
print(stats)
# {'total': 195, 'active': 180, 'sources': {'hh': 150, 'devkg': 45}}

# Последние вакансии с HH.ru
hh_vacancies = get_recent_vacancies(source='hh', limit=5)
for v in hh_vacancies:
    print(f"{v.title} - {format_vacancy_source_display(v)}")

# Фильтрация
from apps.vacancies.models import Vacancy
devkg_only = filter_by_source(Vacancy.objects.all(), 'devkg')
print(devkg_only.count())
"""