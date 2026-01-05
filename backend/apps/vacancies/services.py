import requests
import logging
from typing import List,Dict
from django.conf import settings
from apps.users.models import User
from .models import *
from django.core.cache import cache
from django.db.models import Q, Count, Avg
from django.utils import timezone

logger = logging.getLogger(__name__)


def match_vacancy_to_users(vacancy: Vacancy, min_score: int = 30) -> List[User]:
    """
    Оптимизированный подбор пользователей для вакансии

    Args:
        vacancy: Вакансия
        min_score: Минимальный порог совпадения (%)

    Returns:
        List[User]: Отсортированный список подходящих пользователей
    """
    # Кеш для результатов подбора (5 минут)
    cache_key = f"vacancy_matches:{vacancy.hh_id}"
    cached_result = cache.get(cache_key)

    if cached_result:
        return cached_result

    # Оптимизированный запрос с prefetch
    users = User.objects.filter(
        is_active=True,
        is_profile_completed=True,
        telegram_id__isnull=False
    ).prefetch_related('stack', 'work_formats', 'employment_types')

    # Предварительная фильтрация по роли
    vacancy_title_lower = vacancy.title.lower()

    matched_users = []

    for user in users:
        score = calculate_match_score(user, vacancy)

        if score >= min_score:
            matched_users.append((user, score))

    # Сортировка по релевантности
    matched_users.sort(key=lambda x: x[1], reverse=True)
    result = [user for user, _ in matched_users]

    # Кешируем результат
    cache.set(cache_key, result, 300)

    return result


def calculate_match_score(user: User, vacancy: Vacancy) -> int:
    """
    Улучшенный расчет совпадения с весами

    Веса критериев:
    - Роль: 35%
    - Уровень: 20%
    - Технологии: 25%
    - Зарплата: 10%
    - Локация: 10%
    """
    score = 0
    weights = {
        'role': 35,
        'level': 20,
        'stack': 25,
        'salary': 10,
        'location': 10
    }

    # 1. Роль (35 баллов)
    role_score = calculate_role_match(user.role, vacancy.title, vacancy.description)
    score += int(role_score * weights['role'] / 100)

    # 2. Уровень (20 баллов)
    level_score = calculate_level_match(user.level, vacancy)
    score += int(level_score * weights['level'] / 100)

    # 3. Технологии (25 баллов)
    stack_score = calculate_stack_match(user, vacancy)
    score += int(stack_score * weights['stack'] / 100)

    # 4. Зарплата (10 баллов)
    salary_score = calculate_salary_match(user, vacancy)
    score += int(salary_score * weights['salary'] / 100)

    # 5. Локация (10 баллов)
    location_score = calculate_location_match(user, vacancy)
    score += int(location_score * weights['location'] / 100)

    return min(score, 100)


def calculate_role_match(user_role: str, vacancy_title: str, vacancy_desc: str) -> int:
    """Расчет совпадения роли"""
    if not user_role:
        return 0

    user_role_lower = user_role.lower()
    vacancy_title_lower = vacancy_title.lower()
    vacancy_desc_lower = vacancy_desc.lower()

    # Полное совпадение
    if user_role_lower in vacancy_title_lower:
        return 100

    # Частичное совпадение по словам
    user_words = set(user_role_lower.split())
    title_words = set(vacancy_title_lower.split())

    common_words = user_words & title_words

    if common_words:
        match_ratio = len(common_words) / len(user_words)
        return int(match_ratio * 70)

    # Проверка в описании
    if user_role_lower in vacancy_desc_lower:
        return 40

    return 0


def calculate_level_match(user_level: str, vacancy: Vacancy) -> int:
    """Расчет совпадения уровня"""
    if not user_level:
        return 50  # Нейтральный скор если уровень не указан

    level_keywords = {
        'junior': ['junior', 'джуниор', 'стажер', 'intern', 'начинающий'],
        'middle': ['middle', 'миддл', 'средний'],
        'senior': ['senior', 'сеньор', 'старший', 'ведущий'],
        'lead': ['lead', 'лид', 'head', 'chief', 'principal', 'руководитель']
    }

    keywords = level_keywords.get(user_level, [])
    vacancy_text = f"{vacancy.title} {vacancy.description} {vacancy.experience}".lower()

    for keyword in keywords:
        if keyword in vacancy_text:
            return 100

    # Проверка соседних уровней
    level_order = ['junior', 'middle', 'senior', 'lead']

    if user_level in level_order:
        user_idx = level_order.index(user_level)

        # Проверка соседних уровней
        for offset in [-1, 1]:
            check_idx = user_idx + offset
            if 0 <= check_idx < len(level_order):
                check_level = level_order[check_idx]
                for keyword in level_keywords.get(check_level, []):
                    if keyword in vacancy_text:
                        return 60  # Частичное совпадение

    return 30  # Базовый скор


def calculate_stack_match(user: User, vacancy: Vacancy) -> int:
    """Расчет совпадения технологий"""
    user_stack = set(s.name.lower() for s in user.stack.all())

    if not user_stack:
        return 0

    # Навыки из вакансии
    vacancy_skills = set(s.lower() for s in vacancy.skills)

    # Извлечение из описания
    vacancy_text = f"{vacancy.title} {vacancy.description}".lower()

    all_vacancy_keywords = vacancy_skills.copy()

    # Добавляем технологии найденные в тексте
    for tech in user_stack:
        if tech in vacancy_text:
            all_vacancy_keywords.add(tech)

    # Расчет пересечения
    matching_skills = user_stack & all_vacancy_keywords

    if not matching_skills:
        return 0

    # Процент совпадения
    match_ratio = len(matching_skills) / len(user_stack)

    # Бонус за количество совпадений
    bonus = min(len(matching_skills) * 5, 20)

    return min(int(match_ratio * 80) + bonus, 100)


def calculate_salary_match(user: User, vacancy: Vacancy) -> int:
    """Расчет совпадения зарплаты"""
    if not user.salary_from or not vacancy.salary_from:
        return 50  # Нейтральный скор

    # Простое сравнение (игнорируем валюту для упрощения)
    if vacancy.salary_from >= user.salary_from:
        # Полное соответствие
        if vacancy.salary_from >= user.salary_from * 1.2:
            return 100  # Значительно выше ожиданий
        return 80
    elif vacancy.salary_from >= user.salary_from * 0.8:
        return 60  # Близко к ожиданиям
    elif vacancy.salary_from >= user.salary_from * 0.6:
        return 30  # Ниже ожиданий
    else:
        return 0  # Значительно ниже


def calculate_location_match(user: User, vacancy: Vacancy) -> int:
    """Расчет совпадения локации"""
    if not user.location or not vacancy.location:
        return 50  # Нейтральный скор

    user_loc = user.location.lower()
    vac_loc = vacancy.location.lower()

    # Удаленка всегда подходит
    if 'remote' in vac_loc or 'удален' in vac_loc:
        return 100

    # Полное совпадение
    if user_loc in vac_loc or vac_loc in user_loc:
        return 100

    # Проверка по словам
    user_words = set(user_loc.split())
    vac_words = set(vac_loc.split())

    if user_words & vac_words:
        return 70

    return 0


def send_vacancy_notification(user: User, vacancy: Vacancy) -> bool:
    """
    Отправка уведомления с обработкой ошибок
    """
    if not user.telegram_id:
        logger.warning(f"У пользователя {user.id} нет telegram_id")
        return False

    bot_token = settings.BOT_TOKEN
    if not bot_token:
        logger.error("BOT_TOKEN не настроен")
        return False

    message = format_vacancy_message(vacancy)
    message = message[:4000]  # Telegram лимит

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": user.telegram_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)

        # Обработка блокировки бота
        if response.status_code == 403:
            logger.warning(
                f"❌ Бот заблокирован пользователем {user.telegram_id}"
            )
            # Можно деактивировать пользователя
            user.is_active = False
            user.save(update_fields=['is_active'])
            return False

        # Обработка несуществующего чата
        if response.status_code == 400:
            error_data = response.json()
            if 'chat not found' in str(error_data).lower():
                logger.warning(
                    f"❌ Чат не найден для {user.telegram_id}"
                )
                return False

        response.raise_for_status()
        logger.info(f"✅ Уведомление отправлено {user.telegram_id}")
        return True

    except requests.RequestException as e:
        logger.error(
            f"❌ Ошибка отправки {user.telegram_id}: {e}"
        )
        return False


def format_vacancy_message(vacancy: Vacancy) -> str:
    """
    Улучшенное форматирование сообщения
    """
    lines = []

    lines.append("🔥 <b>Новая вакансия!</b>\n")
    lines.append(f"<b>{vacancy.title}</b>")
    lines.append(f"🏢 {vacancy.company_name}\n")

    if vacancy.salary_from or vacancy.salary_to:
        lines.append(f"💰 <b>Зарплата:</b> {vacancy.salary_range}")

    if vacancy.location:
        lines.append(f"📍 <b>Локация:</b> {vacancy.location}")

    if vacancy.experience:
        lines.append(f"⏳ <b>Опыт:</b> {vacancy.experience}")

    if vacancy.employment:
        lines.append(f"📋 <b>Занятость:</b> {vacancy.employment}")

    if vacancy.schedule:
        lines.append(f"🕐 <b>График:</b> {vacancy.schedule}")

    if vacancy.skills:
        skills_text = ", ".join(vacancy.skills[:7])
        if len(vacancy.skills) > 7:
            skills_text += f" и еще {len(vacancy.skills) - 7}"
        lines.append(f"\n🛠 <b>Навыки:</b> {skills_text}")

    lines.append(f"\n<a href='{vacancy.url}'>📎 Посмотреть на HH.ru</a>")

    return "\n".join(lines)


def get_user_recommended_vacancies(user: User, limit: int = 10) -> List[Vacancy]:
    """
    Получение рекомендованных вакансий с кешированием
    """
    cache_key = f"user_recommendations:{user.telegram_id}"
    cached = cache.get(cache_key)

    if cached:
        return cached

    # Базовый запрос
    vacancies = Vacancy.objects.filter(is_active=True)

    # Фильтр по роли
    if user.role:
        vacancies = vacancies.filter(title__icontains=user.role)

    # Исключаем уже уведомленные
    notified_ids = user.notified_vacancies.values_list('id', flat=True)
    vacancies = vacancies.exclude(id__in=notified_ids)

    # Берем последние
    vacancies = vacancies.order_by('-published_at')[:limit * 3]

    # Расчет релевантности
    scored_vacancies = []
    for vacancy in vacancies:
        score = calculate_match_score(user, vacancy)
        if score >= 40:  # Минимальный порог
            scored_vacancies.append((vacancy, score))

    # Сортировка по score
    scored_vacancies.sort(key=lambda x: x[1], reverse=True)
    result = [v for v, _ in scored_vacancies[:limit]]

    # Кешируем на 10 минут
    cache.set(cache_key, result, 600)

    return result


def match_vacancy_to_users_v2(vacancy: Vacancy, min_score: int = 30) -> List[User]:
    """
    Улучшенный подбор с учетом поведения пользователя
    """
    cache_key = f"vacancy_matches_v2:{vacancy.hh_id}"
    cached_result = cache.get(cache_key)

    if cached_result:
        return cached_result

    users = User.objects.filter(
        is_active=True,
        is_profile_completed=True,
        telegram_id__isnull=False
    ).prefetch_related(
        'stack',
        'work_formats',
        'employment_types',
        'vacancy_reactions',  # Новое
        'favorite_vacancies'  # Новое
    )

    matched_users = []

    for user in users:
        # Базовый скор
        base_score = calculate_match_score(user, vacancy)

        # Бонус за поведенческие факторы
        behavior_bonus = calculate_behavior_bonus(user, vacancy)

        final_score = base_score + behavior_bonus

        if final_score >= min_score:
            matched_users.append((user, final_score))

    # Сортировка по релевантности
    matched_users.sort(key=lambda x: x[1], reverse=True)
    result = [user for user, _ in matched_users]

    cache.set(cache_key, result, 300)
    return result


def calculate_behavior_bonus(user: User, vacancy: Vacancy) -> int:
    """
    Рассчитать бонус на основе поведения пользователя

    Факторы:
    1. Реакции на похожие вакансии (+15 баллов)
    2. Избранные похожие вакансии (+20 баллов)
    3. Частота просмотра определенных компаний (+10 баллов)
    4. Предпочтения по зарплате (+10 баллов)
    """
    bonus = 0

    # 1. Анализ реакций на похожие вакансии
    similar_liked = VacancyReaction.objects.filter(
        user=user,
        reaction='like',
        vacancy__title__icontains=user.role
    ).count()

    if similar_liked > 0:
        bonus += min(similar_liked * 3, 15)  # Максимум 15 баллов

    # Штраф за dislike похожих вакансий
    similar_disliked = VacancyReaction.objects.filter(
        user=user,
        reaction='dislike',
        vacancy__title__icontains=vacancy.title.split()[0]  # Первое слово
    ).count()

    if similar_disliked > 2:
        bonus -= 20  # Существенный штраф

    # 2. Избранные вакансии
    has_similar_favorites = FavoriteVacancy.objects.filter(
        user=user,
        vacancy__title__icontains=user.role
    ).exists()

    if has_similar_favorites:
        bonus += 20

    # 3. Предпочтения по компаниям
    if user.vacancy_reactions.filter(
            reaction='like',
            vacancy__company_name=vacancy.company_name
    ).exists():
        bonus += 10

    # 4. Анализ зарплатных предпочтений на основе лайков
    if user.salary_from and vacancy.salary_from:
        liked_vacancies = VacancyReaction.objects.filter(
            user=user,
            reaction='like',
            vacancy__salary_from__isnull=False
        ).values_list('vacancy__salary_from', flat=True)

        if liked_vacancies:
            avg_liked_salary = sum(liked_vacancies) / len(liked_vacancies)

            # Если текущая вакансия близка к среднему лайкнутому
            if abs(vacancy.salary_from - avg_liked_salary) / avg_liked_salary < 0.2:
                bonus += 10

    return bonus


def get_personalized_vacancies(user: User, limit: int = 20) -> List[Vacancy]:
    """
    Персонализированная лента вакансий с учетом истории
    """
    cache_key = f"personalized_feed:{user.telegram_id}"
    cached = cache.get(cache_key)

    if cached:
        return cached

    # Исключаем вакансии, которые пользователь дизлайкнул
    disliked_ids = VacancyReaction.objects.filter(
        user=user,
        reaction='dislike'
    ).values_list('vacancy_id', flat=True)

    # Исключаем уже уведомленные
    notified_ids = user.notified_vacancies.values_list('id', flat=True)

    # Базовый запрос
    vacancies = Vacancy.objects.filter(
        is_active=True
    ).exclude(
        id__in=list(disliked_ids) + list(notified_ids)
    )

    # Фильтр по роли (мягкий)
    if user.role:
        role_words = user.role.lower().split()
        q_objects = Q()
        for word in role_words:
            if len(word) > 3:  # Игнорируем короткие слова
                q_objects |= Q(title__icontains=word)

        vacancies = vacancies.filter(q_objects)

    # Получаем больше вакансий для скоринга
    vacancies = vacancies.order_by('-published_at')[:limit * 3]

    # Рассчитываем персонализированный скор
    scored_vacancies = []
    for vacancy in vacancies:
        base_score = calculate_match_score(user, vacancy)
        behavior_bonus = calculate_behavior_bonus(user, vacancy)

        # Бонус за свежесть
        hours_old = (timezone.now() - vacancy.published_at).total_seconds() / 3600
        freshness_bonus = max(0, 10 - int(hours_old / 24))

        total_score = base_score + behavior_bonus + freshness_bonus

        if total_score >= 40:
            scored_vacancies.append((vacancy, total_score))

    # Сортировка по итоговому скору
    scored_vacancies.sort(key=lambda x: x[1], reverse=True)
    result = [v for v, _ in scored_vacancies[:limit]]

    cache.set(cache_key, result, 600)  # 10 минут
    return result


def analyze_user_preferences(user: User) -> Dict:
    """
    Анализ предпочтений пользователя на основе поведения

    Возвращает инсайты для улучшения профиля
    """
    liked_vacancies = VacancyReaction.objects.filter(
        user=user,
        reaction='like'
    ).select_related('vacancy')

    if not liked_vacancies.exists():
        return {
            "message": "Пока недостаточно данных для анализа",
            "recommendations": []
        }

    # Анализируем лайкнутые вакансии
    liked_list = list(liked_vacancies.values(
        'vacancy__title',
        'vacancy__company_name',
        'vacancy__location',
        'vacancy__salary_from',
        'vacancy__skills'
    ))

    all_skills = []
    for item in liked_list:
        all_skills.extend(item['vacancy__skills'] or [])

    from collections import Counter
    skill_freq = Counter(all_skills)
    top_skills = [skill for skill, _ in skill_freq.most_common(10)]

    # 2. Средняя зарплата
    salaries = [
        item['vacancy__salary_from']
        for item in liked_list
        if item['vacancy__salary_from']
    ]
    avg_salary = sum(salaries) / len(salaries) if salaries else None

    locations = [
        item['vacancy__location']
        for item in liked_list
        if item['vacancy__location']
    ]
    location_freq = Counter(locations)
    top_locations = [loc for loc, _ in location_freq.most_common(3)]
    recommendations = []
    user_stack_names = set(s.name.lower() for s in user.stack.all())
    missing_skills = [s for s in top_skills if s.lower() not in user_stack_names]

    if missing_skills[:3]:
        recommendations.append({
            "type": "skills",
            "message": f"Добавь в профиль: {', '.join(missing_skills[:3])}",
            "action": "update_stack"
        })

    if avg_salary and user.salary_from:
        if user.salary_from < avg_salary * 0.8:
            recommendations.append({
                "type": "salary",
                "message": f"Вакансии, которые тебе нравятся, обычно предлагают ~{int(avg_salary)}. "
                           f"Возможно, стоит повысить зарплатные ожидания.",
                "suggested_salary": int(avg_salary)
            })

    if top_locations and user.location:
        if user.location not in top_locations:
            recommendations.append({
                "type": "location",
                "message": f"Тебе часто нравятся вакансии из: {', '.join(top_locations)}. "
                           f"Рассмотри изменение локации.",
                "suggested_locations": top_locations
            })

    return {
        "liked_count": liked_vacancies.count(),
        "top_skills": top_skills[:10],
        "avg_salary": int(avg_salary) if avg_salary else None,
        "top_locations": top_locations,
        "recommendations": recommendations
    }