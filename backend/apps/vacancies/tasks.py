import requests
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch

from .models import Vacancy, ParsingLog, VacancyNotification
from apps.users.models import User
from .services import match_vacancy_to_users, send_vacancy_notification

logger = logging.getLogger(__name__)

HH_API_URL = "https://api.hh.ru/vacancies"
HH_HEADERS = {
    "User-Agent": "JobPulseBot/1.0 (duishobaevislam01@gmail.com)",
    "HH-User-Agent": "JobPulseBot/1.0 (duishobaevislam01@gmail.com)"
}


class HHRateLimiter:
    def __init__(self):
        self.last_request_time = 0
        self.min_interval = 0.5  # 500ms между запросами (безопаснее)
        self.request_count = 0
        self.period_start = time.time()
        self.max_requests_per_minute = 150  # Снижено с 200 для безопасности
        self.consecutive_errors = 0

    def wait_if_needed(self):
        """Ожидание с учетом лимитов и ошибок"""
        now = time.time()

        # Сброс счетчика каждую минуту
        if now - self.period_start > 60:
            self.request_count = 0
            self.period_start = now
            self.consecutive_errors = max(0, self.consecutive_errors - 1)

        # Проверка лимита
        if self.request_count >= self.max_requests_per_minute:
            wait_time = 60 - (now - self.period_start) + 1
            if wait_time > 0:
                logger.info(f"⏸️ Достигнут лимит. Ожидание {wait_time:.1f}с")
                time.sleep(wait_time)
                self.request_count = 0
                self.period_start = time.time()

        # Адаптивная задержка при ошибках
        delay = self.min_interval * (1.5 ** self.consecutive_errors)

        time_since_last = now - self.last_request_time
        if time_since_last < delay:
            time.sleep(delay - time_since_last)

        self.last_request_time = time.time()
        self.request_count += 1

    def register_error(self):
        """Регистрация ошибки для увеличения задержки"""
        self.consecutive_errors = min(self.consecutive_errors + 1, 5)

    def register_success(self):
        """Регистрация успешного запроса"""
        self.consecutive_errors = max(0, self.consecutive_errors - 1)


# Глобальный rate limiter
rate_limiter = HHRateLimiter()


def fetch_vacancies_from_hh(
        text: str,
        per_page: int = 20,
        page: int = 0,
        max_retries: int = 3
) -> Optional[Dict]:
    """
    Улучшенное получение вакансий с retry логикой
    """
    params = {
        "text": text,
        "area": 1,  # Москва
        "per_page": min(per_page, 50),  # Максимум 50 за раз
        "page": page,
        "period": 1,  # За последний день
        "order_by": "publication_time",
    }

    for attempt in range(max_retries):
        try:
            rate_limiter.wait_if_needed()

            response = requests.get(
                HH_API_URL,
                params=params,
                headers=HH_HEADERS,
                timeout=15
            )

            # Обработка rate limit
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"⚠️ 429 Too Many Requests. Ожидание {retry_after}с")
                rate_limiter.register_error()
                time.sleep(retry_after)
                continue

            # Обработка 403
            if response.status_code == 403:
                logger.error("❌ 403 Forbidden - возможна блокировка IP")
                rate_limiter.register_error()
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
                return None

            response.raise_for_status()
            rate_limiter.register_success()
            return response.json()

        except requests.RequestException as e:
            logger.error(f"Ошибка запроса (попытка {attempt + 1}/{max_retries}): {e}")
            rate_limiter.register_error()
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                return None

    return None


def fetch_vacancy_details(vacancy_id: str) -> Optional[Dict]:
    """
    Получение детальной информации о вакансии
    """
    try:
        rate_limiter.wait_if_needed()

        response = requests.get(
            f"{HH_API_URL}/{vacancy_id}",
            headers=HH_HEADERS,
            timeout=10
        )

        if response.status_code == 200:
            rate_limiter.register_success()
            return response.json()
        elif response.status_code == 404:
            logger.warning(f"Вакансия {vacancy_id} не найдена")
            return None
        else:
            logger.error(f"Ошибка {response.status_code} при получении {vacancy_id}")
            rate_limiter.register_error()
            return None

    except Exception as e:
        logger.error(f"Ошибка получения деталей {vacancy_id}: {e}")
        rate_limiter.register_error()
        return None


def parse_hh_date(date_string: str) -> datetime:
    """Улучшенный парсинг даты"""
    try:
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        logger.warning(f"Не удалось распарсить дату: {date_string}")
        return timezone.now()


def extract_skills_from_description(description: str) -> List[str]:
    """
    Извлечение навыков из описания вакансии
    """
    # Простая эвристика для извлечения технологий
    common_skills = [
        'python', 'django', 'fastapi', 'flask', 'react', 'vue', 'angular',
        'javascript', 'typescript', 'node.js', 'postgresql', 'mongodb',
        'redis', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'git'
    ]

    description_lower = description.lower()
    found_skills = []

    for skill in common_skills:
        if skill in description_lower:
            found_skills.append(skill.capitalize())

    return found_skills[:10]  # Максимум 10 навыков


def save_vacancies_batch(vacancies: List[Dict]) -> Tuple[int, int]:
    """
    Батчевое сохранение вакансий с оптимизацией
    """
    new_count = 0
    updated_count = 0

    # Получаем существующие hh_id для проверки
    existing_ids = set(
        Vacancy.objects.filter(
            hh_id__in=[v.get('id') for v in vacancies if v.get('id')]
        ).values_list('hh_id', flat=True)
    )

    vacancies_to_create = []
    vacancies_to_update = []

    for item in vacancies:
        hh_id = item.get('id')
        if not hh_id:
            continue

        # Безопасное извлечение данных
        employer = item.get('employer') or {}
        salary = item.get('salary')
        area = item.get('area') or {}
        snippet = item.get('snippet') or {}
        experience = item.get('experience') or {}
        employment = item.get('employment') or {}
        schedule = item.get('schedule') or {}

        # Формирование описания
        requirement = snippet.get('requirement', '').strip()
        responsibility = snippet.get('responsibility', '').strip()

        if requirement and responsibility:
            description = f"{requirement}\n\n{responsibility}"
        elif requirement:
            description = requirement
        elif responsibility:
            description = responsibility
        else:
            description = "Описание не указано"

        # Извлечение навыков
        skills = extract_skills_from_description(description)

        vacancy_data = {
            "hh_id": hh_id,
            "title": item.get('name', 'Без названия')[:255],
            "company_name": employer.get('name', 'Не указано')[:255],
            "company_url": employer.get('alternate_url'),
            "description": description,
            "salary_from": salary.get('from') if salary else None,
            "salary_to": salary.get('to') if salary else None,
            "currency": salary.get('currency', 'RUR') if salary else 'RUR',
            "location": area.get('name', '')[:255],
            "experience": experience.get('name', '')[:50],
            "employment": employment.get('name', '')[:50],
            "schedule": schedule.get('name', '')[:50],
            "url": item.get('alternate_url', '')[:200],
            "skills": skills,
            "published_at": parse_hh_date(item.get('published_at')),
            "is_active": True
        }

        if hh_id in existing_ids:
            vacancies_to_update.append((hh_id, vacancy_data))
        else:
            vacancies_to_create.append(Vacancy(**vacancy_data))

    # Батчевое создание
    if vacancies_to_create:
        try:
            with transaction.atomic():
                Vacancy.objects.bulk_create(
                    vacancies_to_create,
                    batch_size=50,
                    ignore_conflicts=True
                )
            new_count = len(vacancies_to_create)
            logger.info(f"➕ Создано {new_count} новых вакансий")
        except Exception as e:
            logger.error(f"Ошибка при создании вакансий: {e}")

    # Батчевое обновление
    if vacancies_to_update:
        try:
            for hh_id, data in vacancies_to_update:
                Vacancy.objects.filter(hh_id=hh_id).update(**data)
            updated_count = len(vacancies_to_update)
            logger.info(f"🔄 Обновлено {updated_count} вакансий")
        except Exception as e:
            logger.error(f"Ошибка при обновлении вакансий: {e}")

    return new_count, updated_count


@shared_task(bind=True, max_retries=3)
def parse_hh_vacancies(self):
    """
    Оптимизированный парсинг вакансий с HH.ru
    """
    log = ParsingLog.objects.create(status="running")

    try:
        logger.info("🚀 Начинаем парсинг HH.ru...")

        # Получаем топ-5 ролей пользователей
        search_queries = User.objects.filter(
            is_active=True,
            is_profile_completed=True
        ).values_list('role', flat=True).distinct()[:5]

        if not search_queries:
            logger.warning("Нет активных пользователей для парсинга")
            log.status = "completed"
            log.finished_at = timezone.now()
            log.save()
            return {"status": "no_users", "message": "Нет пользователей"}

        total_found = 0
        new_vacancies = 0
        updated_vacancies = 0

        for query in search_queries:
            logger.info(f"🔍 Поиск вакансий: {query}")

            # Получаем первую страницу
            result = fetch_vacancies_from_hh(query, per_page=20, page=0)

            if not result or not result.get('items'):
                logger.warning(f"Нет результатов для '{query}'")
                continue

            total_found += result.get('found', 0)

            # Сохраняем батчем
            new, updated = save_vacancies_batch(result['items'])
            new_vacancies += new
            updated_vacancies += updated

            # Задержка между разными запросами
            time.sleep(2)

        # Обновляем лог
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

        # Запускаем рассылку только если есть новые
        if new_vacancies > 0:
            notify_users_about_new_vacancies.apply_async(countdown=10)

        return {
            "status": "success",
            "total": total_found,
            "new": new_vacancies,
            "updated": updated_vacancies
        }

    except Exception as e:
        logger.error(f"❌ Критическая ошибка парсинга: {e}", exc_info=True)
        log.status = "failed"
        log.errors = str(e)
        log.finished_at = timezone.now()
        log.save()

        # Retry с экспоненциальной задержкой
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True)
def notify_users_about_new_vacancies(self):
    """
    Оптимизированная рассылка уведомлений
    """
    logger.info("📨 Начинаем рассылку уведомлений...")

    try:
        # Получаем новые вакансии за последний час
        recent_vacancies = Vacancy.objects.filter(
            is_active=True,
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).select_related().prefetch_related('notified_users')[:20]

        if not recent_vacancies:
            logger.info("Нет новых вакансий для рассылки")
            return {"notified": 0}

        # Получаем активных пользователей с предзагрузкой связей
        active_users = User.objects.filter(
            is_active=True,
            is_profile_completed=True,
            telegram_id__isnull=False
        ).prefetch_related('stack', 'work_formats', 'employment_types')

        notified_count = 0

        for vacancy in recent_vacancies:
            # Получаем уже уведомленных пользователей
            already_notified = set(
                vacancy.notified_users.values_list('telegram_id', flat=True)
            )

            # Фильтруем пользователей
            matched_users = [
                user for user in active_users
                if user.telegram_id not in already_notified
            ]

            # Подбор по релевантности
            matched_users = match_vacancy_to_users(vacancy)
            matched_users = [
                                u for u in matched_users
                                if u.telegram_id not in already_notified
                            ][:5]

            # Батчевое создание уведомлений
            notifications_to_create = []

            for user in matched_users:
                success = send_vacancy_notification(user, vacancy)

                if success:
                    notifications_to_create.append(
                        VacancyNotification(user=user, vacancy=vacancy)
                    )
                    notified_count += 1

                time.sleep(0.5)  # Задержка между отправками

            # Батчевое сохранение
            if notifications_to_create:
                VacancyNotification.objects.bulk_create(
                    notifications_to_create,
                    ignore_conflicts=True
                )

        logger.info(f"✅ Отправлено уведомлений: {notified_count}")
        return {"notified": notified_count}

    except Exception as e:
        logger.error(f"❌ Ошибка при рассылке: {e}", exc_info=True)
        return {"error": str(e)}


@shared_task
def deactivate_old_vacancies():
    """Деактивация старых вакансий"""
    threshold_date = timezone.now() - timedelta(days=30)

    updated = Vacancy.objects.filter(
        is_active=True,
        published_at__lt=threshold_date
    ).update(is_active=False, updated_at=timezone.now())

    logger.info(f"🗑 Деактивировано вакансий: {updated}")
    return {"deactivated": updated}


@shared_task
def cleanup_old_logs():
    """Очистка старых логов"""
    threshold_date = timezone.now() - timedelta(days=90)

    deleted_count, _ = ParsingLog.objects.filter(
        started_at__lt=threshold_date
    ).delete()

    logger.info(f"🧹 Удалено логов: {deleted_count}")
    return {"deleted": deleted_count}