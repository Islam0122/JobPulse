import requests
import logging
from django.conf import settings
from apps.users.models import User
from .models import Vacancy

logger = logging.getLogger(__name__)


def match_vacancy_to_users(vacancy: Vacancy):
    """
    Подбор пользователей для вакансии на основе их профиля

    Критерии подбора:
    - Совпадение роли/должности
    - Соответствие уровня (junior/middle/senior)
    - Наличие нужных технологий в стеке
    - Подходящая зарплата
    - Нужный формат работы
    - Совпадение локации
    """
    matched_users = []

    # Базовый фильтр: активные пользователи с заполненным профилем
    users = User.objects.filter(
        is_active=True,
        is_profile_completed=True
    ).prefetch_related('stack', 'work_formats', 'employment_types')

    for user in users:
        score = calculate_match_score(user, vacancy)

        # Отправляем только если совпадение >= 10%
        if score >= 10:
            matched_users.append(user)
            logger.info(
                f"✅ Вакансия '{vacancy.title}' подходит "
                f"{user.username} (score: {score}%)"
            )

    return matched_users


def calculate_match_score(user: User, vacancy: Vacancy) -> int:
    """
    Расчет процента совпадения вакансии с профилем пользователя

    Returns:
        int: Процент совпадения (0-100)
    """
    score = 0
    max_score = 100

    # 1. Совпадение роли (40 баллов)
    if user.role.lower() in vacancy.title.lower():
        score += 40
    elif any(word in vacancy.title.lower() for word in user.role.lower().split()):
        score += 20

    # 2. Уровень опыта (20 баллов)
    level_map = {
        "junior": ["junior", "стажер", "intern", "начинающий"],
        "middle": ["middle", "миддл"],
        "senior": ["senior", "сеньор", "lead", "principal"],
        "lead": ["lead", "head", "chief", "principal"]
    }

    if user.level:
        user_keywords = level_map.get(user.level, [])
        vacancy_text = f"{vacancy.title} {vacancy.description}".lower()

        if any(keyword in vacancy_text for keyword in user_keywords):
            score += 20

    # 3. Технологии/навыки (25 баллов)
    user_stack = {s.name.lower() for s in user.stack.all()}
    vacancy_skills = {skill.lower() for skill in vacancy.skills}
    vacancy_text = vacancy.description.lower()

    # Проверяем навыки как из ключевых, так и из описания
    all_vacancy_keywords = vacancy_skills | {
        word for word in vacancy_text.split() if len(word) > 3
    }

    matching_skills = user_stack & all_vacancy_keywords

    if user_stack and matching_skills:
        skill_match_percent = len(matching_skills) / len(user_stack)
        score += int(25 * skill_match_percent)

    # 4. Зарплата (10 баллов)
    if user.salary_from and vacancy.salary_from:
        # Приводим к одной валюте для сравнения (упрощенно)
        if vacancy.salary_from >= user.salary_from * 0.8:
            score += 10
        elif vacancy.salary_from >= user.salary_from * 0.5:
            score += 5

    # 5. Локация (5 баллов)
    if user.location and vacancy.location:
        if user.location.lower() in vacancy.location.lower() or \
                "remote" in vacancy.location.lower() or \
                "удаленно" in vacancy.location.lower():
            score += 5

    return min(score, max_score)


def send_vacancy_notification(user: User, vacancy: Vacancy) -> bool:
    if not user.telegram_id:
        logger.warning(f"У пользователя {user.id} нет telegram_id")
        return False

    bot_token = settings.BOT_TOKEN
    if not bot_token:
        logger.error("BOT_TOKEN не найден")
        return False

    message = format_vacancy_message(vacancy)

    # Telegram лимит 4096 символов
    message = message[:4000]

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": user.telegram_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True

    except requests.RequestException as e:
        logger.error(
            f"❌ Ошибка отправки уведомления {user.telegram_id}: {e}"
        )
        return False


def format_vacancy_message(vacancy: Vacancy) -> str:
    """
    Форматирование сообщения о вакансии для Telegram
    """
    message = f"🔥 <b>Новая вакансия!</b>\n\n"
    message += f"<b>{vacancy.title}</b>\n"
    message += f"🏢 {vacancy.company_name}\n\n"

    if vacancy.salary_from or vacancy.salary_to:
        message += f"💰 <b>Зарплата:</b> {vacancy.salary_range}\n"

    if vacancy.location:
        message += f"📍 <b>Локация:</b> {vacancy.location}\n"

    if vacancy.experience:
        message += f"⏳ <b>Опыт:</b> {vacancy.experience}\n"

    if vacancy.employment:
        message += f"📋 <b>Занятость:</b> {vacancy.employment}\n"

    if vacancy.schedule:
        message += f"🕐 <b>График:</b> {vacancy.schedule}\n"

    if vacancy.skills:
        skills_text = ", ".join(vacancy.skills[:5])
        if len(vacancy.skills) > 5:
            skills_text += f" и еще {len(vacancy.skills) - 5}"
        message += f"\n🛠 <b>Навыки:</b> {skills_text}\n"

    message += f"\n<a href='{vacancy.url}'>📎 Посмотреть на HH.ru</a>"

    return message


def get_user_recommended_vacancies(user: User, limit: int = 10):
    """
    Получение рекомендованных вакансий для пользователя

    Args:
        user: Пользователь
        limit: Максимальное количество вакансий

    Returns:
        QuerySet: Подходящие вакансии отсортированные по релевантности
    """
    vacancies = Vacancy.objects.filter(is_active=True)

    if user.role:
        vacancies = vacancies.filter(
            title__icontains=user.role
        )

    notified_ids = user.notified_vacancies.values_list('id', flat=True)
    vacancies = vacancies.exclude(id__in=notified_ids)

    vacancies = vacancies.order_by('-published_at')[:limit * 2]

    recommended = []
    for vacancy in vacancies:
        score = calculate_match_score(user, vacancy)
        if score >= 60:
            recommended.append((vacancy, score))

    recommended.sort(key=lambda x: x[1], reverse=True)

    return [v for v, _ in recommended[:limit]]