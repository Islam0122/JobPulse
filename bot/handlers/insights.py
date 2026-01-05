from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.api_client import api
import html

router = Router()


@router.callback_query(F.data == "menu:insights")
async def show_insights_menu(callback: CallbackQuery):
    """Меню аналитики и рекомендаций"""
    telegram_id = callback.from_user.id

    # Получаем данные о пользователе
    user = await api.get_user(telegram_id)

    if not user:
        await callback.answer("❌ Профиль не найден", show_alert=True)
        return

    text = "📊 <b>Твоя статистика</b>\n\n"
    text += "Выбери раздел:"

    builder = InlineKeyboardBuilder()
    builder.button(text="🎯 Анализ предпочтений", callback_data="insights:preferences")
    builder.button(text="📈 Статистика активности", callback_data="insights:stats")
    builder.button(text="💡 Рекомендации по профилю", callback_data="insights:recommendations")
    builder.button(text="⬅️ Назад", callback_data="menu:home")
    builder.adjust(1)

    await callback.message.edit_caption(
        caption=text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "insights:preferences")
async def show_preferences_analysis(callback: CallbackQuery):
    """Анализ предпочтений пользователя на основе лайков"""
    telegram_id = callback.from_user.id

    # Получаем инсайты через новый endpoint
    insights = await api.get_user_insights(telegram_id)

    if not insights:
        await callback.answer("❌ Ошибка загрузки данных", show_alert=True)
        return

    if insights.get("liked_count", 0) == 0:
        text = (
            "🤷‍♂️ <b>Недостаточно данных</b>\n\n"
            "Чтобы я мог проанализировать твои предпочтения, "
            "нужно отметить хотя бы несколько вакансий как интересные.\n\n"
            "💡 Перейди в раздел 'Вакансии' и начни просматривать предложения!"
        )
    else:
        text = "🎯 <b>Анализ твоих предпочтений</b>\n\n"
        text += f"📊 Проанализировано реакций: {insights['liked_count']}\n\n"

        # Топ навыки
        if insights.get('top_skills'):
            text += "<b>🛠 Технологии в понравившихся вакансиях:</b>\n"
            for skill in insights['top_skills'][:7]:
                text += f"  • {html.escape(skill)}\n"
            text += "\n"

        # Средняя зарплата
        if insights.get('avg_salary'):
            text += f"<b>💰 Средняя зарплата вакансий, которые тебе нравятся:</b>\n"
            text += f"  {insights['avg_salary']:,} USD\n\n"

        # Топ локации
        if insights.get('top_locations'):
            text += "<b>🌍 Популярные города:</b>\n"
            for loc in insights['top_locations']:
                text += f"  • {html.escape(loc)}\n"
            text += "\n"

        # Рекомендации
        if insights.get('recommendations'):
            text += "<b>💡 Рекомендации:</b>\n"
            for rec in insights['recommendations']:
                text += f"  • {html.escape(rec['message'])}\n"

    builder = InlineKeyboardBuilder()

    if insights.get('recommendations'):
        builder.button(
            text="✏️ Применить рекомендации",
            callback_data="insights:apply_recommendations"
        )

    builder.button(text="⬅️ Назад", callback_data="menu:insights")
    builder.adjust(1)

    await callback.message.edit_caption(
        caption=text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "insights:stats")
async def show_activity_stats(callback: CallbackQuery):
    """Статистика активности пользователя"""
    telegram_id = callback.from_user.id

    # Получаем статистику через API
    stats = await api.get_user_stats(telegram_id)

    if not stats:
        await callback.answer("❌ Ошибка загрузки статистики", show_alert=True)
        return

    text = "📈 <b>Твоя активность</b>\n\n"

    # Реакции
    likes = stats.get('likes_count', 0)
    dislikes = stats.get('dislikes_count', 0)
    total_reactions = likes + dislikes

    text += "<b>👍 Реакции на вакансии:</b>\n"
    text += f"  • Интересно: {likes}\n"
    text += f"  • Не подходит: {dislikes}\n"
    text += f"  • Всего: {total_reactions}\n\n"

    # Избранное
    favorites = stats.get('favorites_count', 0)
    text += f"<b>⭐️ Вакансий в избранном:</b> {favorites}\n\n"

    # Уведомления
    notifications = stats.get('notifications_count', 0)
    viewed = stats.get('viewed_count', 0)

    text += "<b>🔔 Уведомления:</b>\n"
    text += f"  • Получено: {notifications}\n"
    text += f"  • Просмотрено: {viewed}\n"

    if notifications > 0:
        view_rate = int((viewed / notifications) * 100)
        text += f"  • Процент просмотра: {view_rate}%\n"

    text += "\n"

    # Активность
    if total_reactions > 10:
        if likes > dislikes * 2:
            text += "🎯 <b>Ты активно ищешь работу!</b>\n"
            text += "Продолжай в том же духе.\n"
        elif likes < dislikes:
            text += "🤔 <b>Много вакансий не подходит?</b>\n"
            text += "Попробуй изменить настройки профиля.\n"
    else:
        text += "💡 <b>Совет:</b> Чем больше вакансий ты оценишь,\n"
        text += "тем лучше я смогу подбирать для тебя предложения!\n"

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="menu:insights")

    await callback.message.edit_caption(
        caption=text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "insights:recommendations")
async def show_profile_recommendations(callback: CallbackQuery):
    """Персонализированные рекомендации по улучшению профиля"""
    telegram_id = callback.from_user.id

    insights = await api.get_user_insights(telegram_id)
    user = await api.get_user(telegram_id)

    if not insights or not user:
        await callback.answer("❌ Ошибка загрузки данных", show_alert=True)
        return

    recommendations = insights.get('recommendations', [])

    if not recommendations:
        text = (
            "✅ <b>Твой профиль в порядке!</b>\n\n"
            "На данный момент у меня нет конкретных рекомендаций.\n\n"
            "💡 Продолжай оценивать вакансии, чтобы я мог "
            "лучше понимать твои предпочтения."
        )
    else:
        text = "💡 <b>Рекомендации по профилю</b>\n\n"
        text += "Вот что можно улучшить:\n\n"

        for i, rec in enumerate(recommendations, 1):
            rec_type = rec.get('type', 'general')
            message = rec.get('message', '')

            emoji = {
                'skills': '🛠',
                'salary': '💰',
                'location': '🌍',
                'general': '💡'
            }.get(rec_type, '💡')

            text += f"{emoji} <b>{i}. {rec_type.capitalize()}</b>\n"
            text += f"   {html.escape(message)}\n\n"

    builder = InlineKeyboardBuilder()

    if recommendations:
        builder.button(
            text="✏️ Редактировать профиль",
            callback_data="edit:profile_start"
        )

    builder.button(text="🔄 Обновить анализ", callback_data="insights:preferences")
    builder.button(text="⬅️ Назад", callback_data="menu:insights")
    builder.adjust(1)

    await callback.message.edit_caption(
        caption=text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

# ============= API ENDPOINTS (добавить в api_client.py) =============

# async def get_user_insights(self, telegram_id: int) -> Optional[Dict]:
#     """Получить инсайты и аналитику пользователя"""
#     params = {"telegram_id": telegram_id}
#     return await self._make_request("GET", "users/insights/", params=params)
#
# async def get_user_stats(self, telegram_id: int) -> Optional[Dict]:
#     """Получить статистику активности пользователя"""
#     params = {"telegram_id": telegram_id}
#     return await self._make_request("GET", "users/stats/", params=params)