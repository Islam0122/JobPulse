import requests
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple, Any
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch
from .models import Vacancy, ParsingLog, VacancyNotification
from apps.users.models import User
from .services import send_vacancy_notification, match_vacancy_to_users_v2
import asyncio
from .services_.telethon_parser import (
    TelegramVacancyParser,
    TELEGRAM_JOB_CHANNELS
)

logger = logging.getLogger(__name__)

# ============= HH.ru Configuration =============
HH_API_URL = "https://api.hh.ru/vacancies"
HH_HEADERS = {
    "User-Agent": "JobPulseBot/1.0 (duishobaevislam01@gmail.com)",
    "HH-User-Agent": "JobPulseBot/1.0 (duishobaevislam01@gmail.com)"
}

# ============= Dev.kg Configuration =============
DEVKG_API_URL = "https://devkg.com/api/pages/jobs"
DEVKG_HEADERS = {
    "User-Agent": "JobPulseBot/1.0 (duishobaevislam01@gmail.com)",
    "Accept": "application/json"
}


class HHRateLimiter:
    def __init__(self):
        self.last_request_time = 0
        self.min_interval = 0.5
        self.request_count = 0
        self.period_start = time.time()
        self.max_requests_per_minute = 150
        self.consecutive_errors = 0

    def wait_if_needed(self):
        now = time.time()

        if now - self.period_start > 60:
            self.request_count = 0
            self.period_start = now
            self.consecutive_errors = max(0, self.consecutive_errors - 1)

        if self.request_count >= self.max_requests_per_minute:
            wait_time = 60 - (now - self.period_start) + 1
            if wait_time > 0:
                logger.info(f"⏸️ HH: Достигнут лимит. Ожидание {wait_time:.1f}с")
                time.sleep(wait_time)
                self.request_count = 0
                self.period_start = time.time()

        delay = self.min_interval * (1.5 ** self.consecutive_errors)

        time_since_last = now - self.last_request_time
        if time_since_last < delay:
            time.sleep(delay - time_since_last)

        self.last_request_time = time.time()
        self.request_count += 1

    def register_error(self):
        self.consecutive_errors = min(self.consecutive_errors + 1, 5)

    def register_success(self):
        self.consecutive_errors = max(0, self.consecutive_errors - 1)


class DevKGRateLimiter:
    """Rate limiter для Dev.kg API"""

    def __init__(self):
        self.last_request_time = 0
        self.min_interval = 1.0
        self.consecutive_errors = 0

    def wait_if_needed(self):
        now = time.time()
        delay = self.min_interval * (1.5 ** self.consecutive_errors)

        time_since_last = now - self.last_request_time
        if time_since_last < delay:
            time.sleep(delay - time_since_last)

        self.last_request_time = time.time()

    def register_error(self):
        self.consecutive_errors = min(self.consecutive_errors + 1, 5)

    def register_success(self):
        self.consecutive_errors = max(0, self.consecutive_errors - 1)


hh_rate_limiter = HHRateLimiter()
devkg_rate_limiter = DevKGRateLimiter()


def safe_str(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        return value.strip()
    return default


# ============= HH.ru Functions =============

def fetch_vacancies_from_hh(
        text: str,
        per_page: int = 20,
        page: int = 0,
        max_retries: int = 3
) -> Optional[Dict]:
    params = {
        "text": text,
        "area": 1,
        "per_page": min(per_page, 50),
        "page": page,
        "period": 1,
        "order_by": "publication_time",
    }

    for attempt in range(max_retries):
        try:
            hh_rate_limiter.wait_if_needed()

            response = requests.get(
                HH_API_URL,
                params=params,
                headers=HH_HEADERS,
                timeout=15
            )

            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"⚠️ HH: 429 Too Many Requests. Ожидание {retry_after}с")
                hh_rate_limiter.register_error()
                time.sleep(retry_after)
                continue

            if response.status_code == 403:
                logger.error("❌ HH: 403 Forbidden - возможна блокировка IP")
                hh_rate_limiter.register_error()
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
                return None

            response.raise_for_status()
            hh_rate_limiter.register_success()
            return response.json()

        except requests.RequestException as e:
            logger.error(f"HH: Ошибка запроса (попытка {attempt + 1}/{max_retries}): {e}")
            hh_rate_limiter.register_error()
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return None

    return None


def fetch_vacancy_details(vacancy_id: str) -> Optional[Dict]:
    try:
        hh_rate_limiter.wait_if_needed()

        response = requests.get(
            f"{HH_API_URL}/{vacancy_id}",
            headers=HH_HEADERS,
            timeout=10
        )

        if response.status_code == 200:
            hh_rate_limiter.register_success()
            return response.json()
        elif response.status_code == 404:
            logger.warning(f"HH: Вакансия {vacancy_id} не найдена")
            return None
        else:
            logger.error(f"HH: Ошибка {response.status_code} при получении {vacancy_id}")
            hh_rate_limiter.register_error()
            return None

    except Exception as e:
        logger.error(f"HH: Ошибка получения деталей {vacancy_id}: {e}")
        hh_rate_limiter.register_error()
        return None


# ============= Dev.kg Functions =============

def fetch_vacancies_from_devkg(page: int = 1, max_retries: int = 3) -> Optional[Dict]:
    """Получение вакансий с Dev.kg API"""
    params = {"page": page}

    for attempt in range(max_retries):
        try:
            devkg_rate_limiter.wait_if_needed()

            response = requests.get(
                DEVKG_API_URL,
                params=params,
                headers=DEVKG_HEADERS,
                timeout=15
            )

            if response.status_code == 429:
                logger.warning(f"⚠️ Dev.kg: 429 Too Many Requests. Ожидание 60с")
                devkg_rate_limiter.register_error()
                time.sleep(60)
                continue

            if response.status_code == 403:
                logger.error("❌ Dev.kg: 403 Forbidden")
                devkg_rate_limiter.register_error()
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
                return None

            response.raise_for_status()
            devkg_rate_limiter.register_success()

            data = response.json()
            if data.get('success'):
                return data.get('result')
            else:
                logger.warning(f"Dev.kg: API вернул success=false")
                return None

        except requests.RequestException as e:
            logger.error(f"Dev.kg: Ошибка запроса (попытка {attempt + 1}/{max_retries}): {e}")
            devkg_rate_limiter.register_error()
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return None

    return None


# ============= Common Functions =============

def parse_hh_date(date_string: str) -> datetime:
    try:
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        logger.warning(f"Не удалось распарсить дату: {date_string}")
        return timezone.now()


def extract_skills_from_description(description: str) -> List[str]:
    common_skills = [
        'python', 'django', 'fastapi', 'flask', 'react', 'vue', 'angular',
        'javascript', 'typescript', 'node.js', 'postgresql', 'mongodb',
        'redis', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'git',
        'java', 'kotlin', 'swift', 'go', 'rust', 'c++', 'c#', '.net',
        'unity', 'unreal', 'figma', 'photoshop', 'illustrator', 'php',
        'laravel', 'symfony', 'ruby', 'rails', 'android', 'ios'
    ]

    description_lower = description.lower() if description else ''
    found_skills = []

    for skill in common_skills:
        if skill in description_lower:
            found_skills.append(skill.capitalize())

    return list(set(found_skills))[:10]


def normalize_devkg_vacancy(item: Dict) -> Dict:
    """Преобразование вакансии Dev.kg в формат модели"""

    vacancy_type = safe_str(item.get("type"), "office")
    employment_map = {
        "office": "Полная занятость",
        "remote": "Удаленная работа",
        "internship": "Стажировка",
    }

    price_from = item.get("price_from") or 0
    price_to = item.get("price_to") or 0
    currency = safe_str(item.get("currency"), "KGS").upper()
    salary_type = safe_str(item.get("salary"), "monthly")

    position = safe_str(item.get("position"), "Без названия")
    company = safe_str(item.get("organization_name"), "Не указано")
    city = safe_str(item.get("city"), "Бишкек")
    slug = safe_str(item.get("slug"))

    description_parts = []
    if position:
        description_parts.append(f"Позиция: {position}")
    if company:
        description_parts.append(f"Компания: {company}")
    if city:
        description_parts.append(f"Город: {city}")

    description = "\n".join(description_parts) if description_parts else "Описание не указано"
    skills = extract_skills_from_description(position)

    return {
        "hh_id": f"devkg_{slug or position.lower().replace(' ', '_')}",
        "title": position[:255]+" (DEV KG)",
        "company_name": company[:255],
        "company_url": f"https://devkg.com/ru/jobs/{slug}" if slug else None,
        "description": description,
        "salary_from": price_from if price_from > 0 else None,
        "salary_to": price_to if price_to > 0 else None,
        "currency": currency,
        "location": city[:255],
        "experience": "",
        "employment": employment_map.get(vacancy_type, "Не указано")[:50],
        "schedule": salary_type[:50],
        "url": f"https://devkg.com/ru/jobs/{slug}"[:200] if slug else None,
        "skills": skills,
        "published_at": parse_hh_date(item.get("created_at")),
        "is_active": not item.get("is_archived", False),
    }


def normalize_hh_vacancy(item: Dict) -> Dict:
    """Преобразование вакансии HH.ru в формат модели"""
    employer = item.get('employer') or {}
    salary = item.get('salary')
    area = item.get('area') or {}
    snippet = item.get('snippet') or {}
    experience = item.get('experience') or {}
    employment = item.get('employment') or {}
    schedule = item.get('schedule') or {}

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

    skills = extract_skills_from_description(description)

    return {
        "hh_id": str(item.get('id')),  # Оставляем как есть для HH
        "title": item.get('name', 'Без названия')[:255]+" (HH)",
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


def normalize_telegram_vacancy(item: Dict) -> Dict:
    return {
        "hh_id": item.get("hh_id"),
        "title": item.get("title", "Без названия")[:255],
        "company_name": item.get("company_name", "Не указано")[:255],
        "company_url": item.get("company_url"),
        "description": item.get("description", "Описание отсутствует"),
        "salary_from": item.get("salary_from"),
        "salary_to": item.get("salary_to"),
        "currency": item.get("currency", "RUB"),
        "location": item.get("location", "Удаленно")[:255],
        "experience": item.get("experience", "")[:250],
        "employment": item.get("employment", {}).get("name", "")[:250],
        "schedule": item.get("schedule", {}).get("name", "")[:250],
        "url": item.get("url", "")[:200],
        "skills": item.get("skills", []),
        "published_at": parse_hh_date(item.get("published_at")) if isinstance(item.get("published_at"), str) else item.get("published_at"),
        "is_active": item.get("is_active", True),
    }


def save_vacancies_batch(vacancies: List[Dict], source: str = "hh") -> Tuple[int, int]:
    """Сохранение пакета вакансий"""
    new_count = 0
    updated_count = 0

    if not vacancies:
        return 0, 0

    # Нормализация вакансий
    normalized_vacancies = []
    for item in vacancies:
        if source == "devkg":
            normalized_vacancies.append(normalize_devkg_vacancy(item))
        elif source == "telegram":
            normalized_vacancies.append(normalize_telegram_vacancy(item))  # ← ДОБАВИТЬ ЭТУ СТРОКУ
        else:
            normalized_vacancies.append(normalize_hh_vacancy(item))

    existing_ids = set(
        Vacancy.objects.filter(
            hh_id__in=[v['hh_id'] for v in normalized_vacancies]
        ).values_list('hh_id', flat=True)
    )

    vacancies_to_create = []
    vacancies_to_update = []

    for vacancy_data in normalized_vacancies:
        hh_id = vacancy_data['hh_id']

        if hh_id in existing_ids:
            vacancies_to_update.append((hh_id, vacancy_data))
        else:
            vacancies_to_create.append(Vacancy(**vacancy_data))

    if vacancies_to_create:
        try:
            with transaction.atomic():
                Vacancy.objects.bulk_create(
                    vacancies_to_create,
                    batch_size=50,
                    ignore_conflicts=True
                )
            new_count = len(vacancies_to_create)
            logger.info(f"➕ [{source.upper()}] Создано {new_count} новых вакансий")
        except Exception as e:
            logger.error(f"[{source.upper()}] Ошибка при создании вакансий: {e}")

    if vacancies_to_update:
        try:
            for hh_id, data in vacancies_to_update:
                Vacancy.objects.filter(hh_id=hh_id).update(**data)
            updated_count = len(vacancies_to_update)
            logger.info(f"🔄 [{source.upper()}] Обновлено {updated_count} вакансий")
        except Exception as e:
            logger.error(f"[{source.upper()}] Ошибка при обновлении вакансий: {e}")

    return new_count, updated_count


# ============= Celery Tasks =============

@shared_task(bind=True, max_retries=3)
def parse_hh_vacancies(self):
    """Парсинг вакансий с HH.ru"""
    log = ParsingLog.objects.create(status="running")

    try:
        logger.info("🚀 [HH] Начинаем парсинг HH.ru...")
        search_queries = User.objects.filter(
            is_active=True,
            is_profile_completed=True
        ).values_list('role', flat=True).distinct()[:5]

        if not search_queries:
            logger.warning("[HH] Нет активных пользователей для парсинга")
            log.status = "completed"
            log.finished_at = timezone.now()
            log.save()
            return {"status": "no_users", "message": "Нет пользователей"}

        total_found = 0
        new_vacancies = 0
        updated_vacancies = 0

        for query in search_queries:
            logger.info(f"🔍 [HH] Поиск вакансий: {query}")
            result = fetch_vacancies_from_hh(query, per_page=20, page=0)

            if not result or not result.get('items'):
                logger.warning(f"[HH] Нет результатов для '{query}'")
                continue

            total_found += result.get('found', 0)
            new, updated = save_vacancies_batch(result['items'], source="hh")
            new_vacancies += new
            updated_vacancies += updated
            time.sleep(2)

        log.total_found = total_found
        log.new_vacancies = new_vacancies
        log.updated_vacancies = updated_vacancies
        log.finished_at = timezone.now()
        log.status = "completed"
        log.save()

        logger.info(
            f"✅ [HH] Парсинг завершен: найдено {total_found}, "
            f"новых {new_vacancies}, обновлено {updated_vacancies}"
        )

        if new_vacancies > 0:
            notify_users_about_new_vacancies.apply_async(countdown=10)

        return {
            "status": "success",
            "source": "hh",
            "total": total_found,
            "new": new_vacancies,
            "updated": updated_vacancies
        }

    except Exception as e:
        logger.error(f"❌ [HH] Критическая ошибка парсинга: {e}", exc_info=True)
        log.status = "failed"
        log.errors = str(e)
        log.finished_at = timezone.now()
        log.save()
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def parse_devkg_vacancies(self, max_pages: int = 3):
    """Парсинг вакансий с Dev.kg"""
    log = ParsingLog.objects.create(status="running")

    try:
        logger.info("🚀 [Dev.kg] Начинаем парсинг Dev.kg...")

        total_found = 0
        new_vacancies = 0
        updated_vacancies = 0

        for page in range(1, max_pages + 1):
            logger.info(f"📄 [Dev.kg] Обработка страницы {page}/{max_pages}")

            result = fetch_vacancies_from_devkg(page=page)

            if not result or not result.get('list'):
                logger.warning(f"[Dev.kg] Нет результатов на странице {page}")
                break

            vacancies_list = result['list']
            total_found += len(vacancies_list)

            new, updated = save_vacancies_batch(vacancies_list, source="devkg")
            new_vacancies += new
            updated_vacancies += updated

            time.sleep(2)

        log.total_found = total_found
        log.new_vacancies = new_vacancies
        log.updated_vacancies = updated_vacancies
        log.finished_at = timezone.now()
        log.status = "completed"
        log.save()

        logger.info(
            f"✅ [Dev.kg] Парсинг завершен: найдено {total_found}, "
            f"новых {new_vacancies}, обновлено {updated_vacancies}"
        )

        if new_vacancies > 0:
            notify_users_about_new_vacancies.apply_async(countdown=10)

        return {
            "status": "success",
            "source": "devkg",
            "total": total_found,
            "new": new_vacancies,
            "updated": updated_vacancies
        }

    except Exception as e:
        logger.error(f"❌ [Dev.kg] Критическая ошибка парсинга: {e}", exc_info=True)
        log.status = "failed"
        log.errors = str(e)
        log.finished_at = timezone.now()
        log.save()
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True)
def parse_all_sources(self):
    """Парсинг всех источников вакансий"""
    logger.info("🌐 Запуск парсинга всех источников...")

    results = {}

    # Парсинг HH.ru
    try:
        hh_result = parse_hh_vacancies.apply()
        results['hh'] = hh_result.get()
    except Exception as e:
        logger.error(f"Ошибка при парсинге HH: {e}")
        results['hh'] = {"status": "error", "error": str(e)}

    time.sleep(5)

    # Парсинг Dev.kg
    try:
        devkg_result = parse_devkg_vacancies.apply()
        results['devkg'] = devkg_result.get()
    except Exception as e:
        logger.error(f"Ошибка при парсинге Dev.kg: {e}")
        results['devkg'] = {"status": "error", "error": str(e)}

    time.sleep(5)

    # Telegram
    try:
        telegram_result = parse_telegram_vacancies.apply()
        results['telegram'] = telegram_result.get()
    except Exception as e:
        logger.error(f"Ошибка при парсинге Telegram: {e}")
        results['telegram'] = {"status": "error", "error": str(e)}

    # Запуск уведомлений
    total_new = results.get('hh', {}).get('new', 0) + results.get('devkg', {}).get('new', 0)
    if total_new > 0:
        notify_users_about_new_vacancies.apply_async(countdown=10)

    logger.info(f"✅ Парсинг всех источников завершен")
    return results


@shared_task(bind=True)
def notify_users_about_new_vacancies(self):
    logger.info("📨 Начинаем рассылку уведомлений...")

    try:
        recent_vacancies = Vacancy.objects.filter(
            is_active=True,
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).select_related().prefetch_related('notified_users')[:20]

        if not recent_vacancies:
            logger.info("Нет новых вакансий для рассылки")
            return {"notified": 0}

        active_users = User.objects.filter(
            is_active=True,
            is_profile_completed=True,
            telegram_id__isnull=False
        ).prefetch_related('stack', 'work_formats', 'employment_types')

        notified_count = 0

        for vacancy in recent_vacancies:
            already_notified = set(
                vacancy.notified_users.values_list('telegram_id', flat=True)
            )

            matched_users = match_vacancy_to_users_v2(vacancy)
            matched_users = [
                                u for u in matched_users
                                if u.telegram_id not in already_notified
                            ][:5]

            notifications_to_create = []

            for user in matched_users:
                success = send_vacancy_notification(user, vacancy)

                if success:
                    notifications_to_create.append(
                        VacancyNotification(user=user, vacancy=vacancy)
                    )
                    notified_count += 1

                time.sleep(0.5)

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
    threshold_date = timezone.now() - timedelta(days=30)

    updated = Vacancy.objects.filter(
        is_active=True,
        published_at__lt=threshold_date
    ).update(is_active=False, updated_at=timezone.now())

    logger.info(f"🗑 Деактивировано вакансий: {updated}")
    return {"deactivated": updated}


@shared_task
def cleanup_old_logs():
    threshold_date = timezone.now() - timedelta(days=90)

    deleted_count, _ = ParsingLog.objects.filter(
        started_at__lt=threshold_date
    ).delete()

    logger.info(f"🧹 Удалено логов: {deleted_count}")
    return {"deleted": deleted_count}


# ============= Telegram Parsing Task =============

@shared_task(bind=True, max_retries=3)
def parse_telegram_vacancies(self, category: str = None):
    log = ParsingLog.objects.create(status="running")

    try:
        logger.info("🚀 [TELEGRAM] Начинаем парсинг Telegram-каналов...")
        parser = TelegramVacancyParser()
        vacancies = asyncio.run(
            parser.parse_channels(
                category=category,
                limit_per_channel=settings.TELETHON_MESSAGES_LIMIT,
                days_ago=settings.TELETHON_DAYS_AGO
            )
        )
        if not vacancies:
            logger.warning("[TELEGRAM] Вакансий не найдено")
            log.status = "completed"
            log.finished_at = timezone.now()
            log.save()
            return {"status": "no_vacancies", "message": "Вакансий не найдено"}

        new_count, updated_count = save_vacancies_batch(vacancies, source="telegram")

        log.total_found = len(vacancies)
        log.new_vacancies = new_count
        log.updated_vacancies = updated_count
        log.finished_at = timezone.now()
        log.status = "completed"
        log.save()

        logger.info(
            f"✅ [TELEGRAM] Парсинг завершен: найдено {len(vacancies)}, "
            f"новых {new_count}, обновлено {updated_count}"
        )

        # Запускаем уведомления
        if new_count > 0:
            notify_users_about_new_vacancies.apply_async(countdown=10)

        return {
            "status": "success",
            "source": "telegram",
            "total": len(vacancies),
            "new": new_count,
            "updated": updated_count
        }

    except Exception as e:
        logger.error(f"❌ [TELEGRAM] Критическая ошибка парсинга: {e}", exc_info=True)
        log.status = "failed"
        log.errors = str(e)
        log.finished_at = timezone.now()
        log.save()
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

