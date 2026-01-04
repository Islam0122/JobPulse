import requests
import logging
from datetime import datetime, timedelta
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import Vacancy, ParsingLog, VacancyNotification
from apps.users.models import User
from .services import match_vacancy_to_users, send_vacancy_notification

logger = logging.getLogger(__name__)

HH_API_URL = "https://api.hh.ru/vacancies"
HH_HEADERS = {
    "User-Agent": "JobPulseBot/1.0 (duishobaevislam01@gmail.com)"
}


@shared_task
def parse_hh_vacancies():
    """
    Основная задача парсинга вакансий с HH.ru
    Запускается каждые 10 минут через Celery Beat
    """
    log = ParsingLog.objects.create(status="running")

    try:
        logger.info("🚀 Начинаем парсинг HH.ru...")

        # Получаем уникальные роли пользователей для поиска
        search_queries = User.objects.filter(
            is_active=True,
            is_profile_completed=True
        ).values_list('role', flat=True).distinct()

        total_found = 0
        new_vacancies = 0
        updated_vacancies = 0

        for query in search_queries:
            result = fetch_vacancies_from_hh(query)
            if result:
                total_found += result['found']
                new, updated = save_vacancies_to_db(result['items'])
                new_vacancies += new
                updated_vacancies += updated

        log.total_found = total_found
        log.new_vacancies = new_vacancies
        log.updated_vacancies = updated_vacancies
        log.finished_at = timezone.now()
        log.status = "completed"
        log.save()

        logger.info(
            f"✅ Парсинг завершен: найдено {total_found}, "
            f"новых {new_vacancies}, обновлено {updated_vacancies}"
        )

        # Запускаем рассылку новых вакансий
        if new_vacancies > 0:
            notify_users_about_new_vacancies.delay()

        return {
            "status": "success",
            "total": total_found,
            "new": new_vacancies,
            "updated": updated_vacancies
        }

    except Exception as e:
        logger.error(f"❌ Ошибка парсинга: {e}")
        log.status = "failed"
        log.errors = str(e)
        log.finished_at = timezone.now()
        log.save()

        return {"status": "error", "message": str(e)}


def fetch_vacancies_from_hh(text: str, per_page: int = 50, page: int = 0):
    """
    Получение вакансий с HH.ru API

    Args:
        text: Поисковый запрос (название должности)
        per_page: Количество результатов на странице
        page: Номер страницы
    """
    params = {
        "text": text,
        "area": 1,
        "per_page": per_page,
        "page": page,
        "period": 1,
        "sort": "publication_time",
    }

    try:
        response = requests.get(
            HH_API_URL,
            params=params,
            headers=HH_HEADERS,
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        logger.error(f"Ошибка запроса к HH API: {e}")
        return None


def save_vacancies_to_db(vacancies: list):
    """
    Сохранение вакансий в базу данных

    Returns:
        tuple: (количество новых, количество обновленных)
    """
    new_count = 0
    updated_count = 0

    for item in vacancies:
        hh_id = item.get('id')

        if not hh_id:
            continue

        # Получаем детальную информацию о вакансии
        details = get_vacancy_details(hh_id)
        if not details:
            continue

        vacancy_data = {
            "title": item.get("name"),
            "company_name": item.get("employer", {}).get("name"),
            "salary_from": item.get("salary", {}).get("from") if item.get("salary") else None,
            "salary_to": item.get("salary", {}).get("to") if item.get("salary") else None,
            "currency": item.get("salary", {}).get("currency") if item.get("salary") else None,
            "location": item.get("area", {}).get("name"),
            "experience": item.get("experience", {}).get("name"),
            "employment": item.get("employment", {}).get("name"),
            "schedule": item.get("schedule", {}).get("name"),
            "url": item.get("alternate_url"),
            "published_at": parse_hh_date(item.get("published_at")),
        }

        vacancy, created = Vacancy.objects.update_or_create(
            hh_id=hh_id,
            defaults=vacancy_data
        )

        if created:
            new_count += 1
            logger.info(f"➕ Новая вакансия: {vacancy.title}")
        else:
            updated_count += 1
            logger.info(f"♻️ Обновлена: {vacancy.title}")

    return new_count, updated_count


def get_vacancy_details(hh_id: str):
    """Получение детальной информации о вакансии"""
    url = f"https://api.hh.ru/vacancies/{hh_id}"

    try:
        response = requests.get(url, headers=HH_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Ошибка получения деталей вакансии {hh_id}: {e}")
        return None


def parse_hh_date(date_string: str):
    """Парсинг даты из формата HH.ru"""
    try:
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except Exception:
        return timezone.now()


@shared_task
def notify_users_about_new_vacancies():
    """
    Рассылка новых вакансий пользователям
    """
    logger.info("📨 Начинаем рассылку новых вакансий...")

    # Получаем вакансии за последний час
    recent_vacancies = Vacancy.objects.filter(
        is_active=True,
        created_at__gte=timezone.now() - timedelta(hours=1)
    )

    notified_count = 0

    for vacancy in recent_vacancies:
        # Находим подходящих пользователей
        matched_users = match_vacancy_to_users(vacancy)

        for user in matched_users:
            # Проверяем, не отправляли ли уже
            if VacancyNotification.objects.filter(
                    user=user,
                    vacancy=vacancy
            ).exists():
                continue

            # Отправляем уведомление
            if send_vacancy_notification(user, vacancy):
                VacancyNotification.objects.create(
                    user=user,
                    vacancy=vacancy
                )
                notified_count += 1

    logger.info(f"✅ Отправлено уведомлений: {notified_count}")
    return notified_count


@shared_task
def deactivate_old_vacancies():
    """
    Деактивация старых вакансий (старше 30 дней)
    """
    threshold_date = timezone.now() - timedelta(days=30)

    updated = Vacancy.objects.filter(
        is_active=True,
        published_at__lt=threshold_date
    ).update(is_active=False)

    logger.info(f"🗑 Деактивировано старых вакансий: {updated}")
    return updated


@shared_task
def cleanup_old_logs():
    threshold_date = timezone.now() - timedelta(days=90)

    deleted_count, _ = ParsingLog.objects.filter(
        started_at__lt=threshold_date
    ).delete()

    logger.info(f"🧹 Удалено старых логов: {deleted_count}")
    return deleted_count