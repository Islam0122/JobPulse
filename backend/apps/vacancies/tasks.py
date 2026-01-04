import requests
import logging
import time
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


# Rate Limiter
class HHRateLimiter:
    def __init__(self):
        self.last_request_time = 0
        self.min_interval = 0.3  # 300ms между запросами
        self.request_count = 0
        self.period_start = time.time()

    def wait_if_needed(self):
        """Подождать если нужно"""
        now = time.time()

        # Сброс счётчика каждую минуту
        if now - self.period_start > 60:
            self.request_count = 0
            self.period_start = now

        # Проверка лимита (макс 200 запросов в минуту)
        if self.request_count >= 200:
            wait_time = 60 - (now - self.period_start)
            if wait_time > 0:
                logger.info(f"⏸️ Достигнут лимит запросов. Ожидание {wait_time:.1f}с")
                time.sleep(wait_time)
                self.request_count = 0
                self.period_start = time.time()

        # Задержка между запросами
        time_since_last = now - self.last_request_time
        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)

        self.last_request_time = time.time()
        self.request_count += 1


rate_limiter = HHRateLimiter()


@shared_task
def parse_hh_vacancies():
    """
    Оптимизированный парсинг вакансий с HH.ru
    """
    log = ParsingLog.objects.create(status="running")

    try:
        logger.info("🚀 Начинаем парсинг HH.ru...")

        # Получаем роли пользователей
        search_queries = User.objects.filter(
            is_active=True,
            is_profile_completed=True
        ).values_list('role', flat=True).distinct()[:5]  # Лимит на 5 ролей

        total_found = 0
        new_vacancies = 0
        updated_vacancies = 0

        for query in search_queries:
            logger.info(f"🔍 Поиск вакансий: {query}")

            rate_limiter.wait_if_needed()
            result = fetch_vacancies_from_hh(query, per_page=20)  # Уменьшил до 20

            if result and result.get('items'):
                total_found += result.get('found', 0)
                new, updated = save_vacancies_to_db(result['items'])
                new_vacancies += new
                updated_vacancies += updated

            # Задержка между разными запросами
            time.sleep(1)

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

        # Уведомления только если есть новые
        if new_vacancies > 0:
            notify_users_about_new_vacancies.delay()

        return {
            "status": "success",
            "total": total_found,
            "new": new_vacancies,
            "updated": updated_vacancies
        }

    except Exception as e:
        logger.error(f"❌ Ошибка парсинга: {e}", exc_info=True)
        log.status = "failed"
        log.errors = str(e)
        log.finished_at = timezone.now()
        log.save()

        return {"status": "error", "message": str(e)}


def fetch_vacancies_from_hh(text: str, per_page: int = 20, page: int = 0):
    """Получение вакансий с rate limiting"""
    params = {
        "text": text,
        "area": 1,
        "per_page": min(per_page, 100),
        "page": page,
        "period": 1,
        "order_by": "publication_time",
    }

    try:
        response = requests.get(
            HH_API_URL,
            params=params,
            headers=HH_HEADERS,
            timeout=10
        )

        if response.status_code == 403:
            logger.error("❌ 403 Forbidden - превышен лимит или заблокирован IP")
            return None

        if response.status_code == 429:
            logger.warning("⚠️ 429 Too Many Requests - слишком много запросов")
            time.sleep(5)
            return None

        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        logger.error(f"Ошибка HH API: {e}")
        return None


def save_vacancies_to_db(vacancies: list):
    """
    Сохранение без детальных запросов для каждой вакансии
    """
    new_count = 0
    updated_count = 0

    for item in vacancies[:20]:  # Лимит на 20 вакансий за раз
        hh_id = item.get('id')

        if not hh_id:
            continue

        # Используем только базовые данные из списка
        employer = item.get('employer', {}) or {}
        salary = item.get('salary')
        area = item.get('area', {}) or {}
        snippet = item.get('snippet', {}) or {}

        # Безопасная конкатенация строк
        requirement = snippet.get('requirement') or ''
        responsibility = snippet.get('responsibility') or ''
        description = f"{requirement} {responsibility}".strip() or 'Описание не указано'

        vacancy_data = {
            "title": item.get('name', 'Без названия'),
            "company_name": employer.get('name', 'Не указано'),
            "company_url": employer.get('alternate_url'),
            "description": description,
            "salary_from": salary.get('from') if salary else None,
            "salary_to": salary.get('to') if salary else None,
            "currency": salary.get('currency', 'RUR') if salary else 'RUR',
            "location": area.get('name'),
            "experience": item.get('experience', {}).get('name'),
            "employment": item.get('employment', {}).get('name'),
            "schedule": item.get('schedule', {}).get('name'),
            "url": item.get('alternate_url', ''),
            "skills": [],  # Детали не запрашиваем
            "published_at": parse_hh_date(item.get('published_at')),
        }

        try:
            vacancy, created = Vacancy.objects.update_or_create(
                hh_id=hh_id,
                defaults=vacancy_data
            )

            if created:
                new_count += 1
                logger.info(f"➕ {vacancy.title}")
            else:
                updated_count += 1

        except Exception as e:
            logger.error(f"Ошибка сохранения {hh_id}: {e}")
            continue

    return new_count, updated_count


def parse_hh_date(date_string: str):
    """Парсинг даты"""
    try:
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except Exception:
        return timezone.now()


@shared_task
def notify_users_about_new_vacancies():
    """Рассылка новых вакансий"""
    logger.info("📨 Начинаем рассылку...")

    recent_vacancies = Vacancy.objects.filter(
        is_active=True,
        created_at__gte=timezone.now() - timedelta(hours=1)
    )[:10]  # Максимум 10 вакансий за раз

    notified_count = 0

    for vacancy in recent_vacancies:
        matched_users = match_vacancy_to_users(vacancy)

        for user in matched_users[:5]:  # Максимум 5 пользователей на вакансию
            if VacancyNotification.objects.filter(
                    user=user,
                    vacancy=vacancy
            ).exists():
                continue

            if send_vacancy_notification(user, vacancy):
                VacancyNotification.objects.create(
                    user=user,
                    vacancy=vacancy
                )
                notified_count += 1
                time.sleep(0.5)  # Задержка между отправками

    logger.info(f"✅ Отправлено: {notified_count}")
    return notified_count


@shared_task
def deactivate_old_vacancies():
    """Деактивация старых вакансий"""
    threshold_date = timezone.now() - timedelta(days=30)

    updated = Vacancy.objects.filter(
        is_active=True,
        published_at__lt=threshold_date
    ).update(is_active=False)

    logger.info(f"🗑 Деактивировано: {updated}")
    return updated


@shared_task
def cleanup_old_logs():
    """Очистка логов"""
    threshold_date = timezone.now() - timedelta(days=90)

    deleted_count, _ = ParsingLog.objects.filter(
        started_at__lt=threshold_date
    ).delete()

    logger.info(f"🧹 Удалено логов: {deleted_count}")
    return deleted_count