from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from services.api_client import api
from states.user_states import OnboardingStates
import html

router = Router()


@router.callback_query(F.data == "menu:insights")
async def show_insights_menu(callback: CallbackQuery):
    """Меню аналитики и рекомендаций"""
    telegram_id = callback.from_user.id

    user = await api.get_user(telegram_id)

    if not user:
        await callback.answer("❌ Профиль не найден", show_alert=True)
        return

    text = "📊 <b>Твоя статистика</b>\n\n"
    text += "Выбери раздел:"

    builder = InlineKeyboardBuilder()
    builder.button(text="🎯 Анализ предпочтений", callback_data="insights:preferences")
    builder.button(text="📈 Статистика активности", callback_data="insights:stats")
    builder.button(text="💡 Рекомендации", callback_data="insights:recommendations")
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
    """Анализ предпочтений на основе лайков"""
    telegram_id = callback.from_user.id

    await callback.message.edit_caption(
        caption="⏳ Анализирую твои предпочтения...",
        parse_mode="HTML"
    )

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
            text += f"<b>💰 Средняя зарплата:</b>\n"
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
            for rec in insights['recommendations'][:3]:
                text += f"  • {html.escape(rec['message'][:100])}\n"

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
    """Статистика активности"""
    telegram_id = callback.from_user.id

    await callback.message.edit_caption(
        caption="⏳ Загружаю статистику...",
        parse_mode="HTML"
    )

    stats = await api.get_user_stats(telegram_id)

    if not stats:
        await callback.answer("❌ Ошибка загрузки", show_alert=True)
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
    text += f"<b>⭐️ В избранном:</b> {favorites}\n\n"

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

    # Советы
    if total_reactions > 10:
        if likes > dislikes * 2:
            text += "🎯 <b>Отлично!</b> Ты активно ищешь работу.\n"
        elif likes < dislikes:
            text += "🤔 <b>Совет:</b> Много вакансий не подходит?\n"
            text += "Попробуй изменить настройки профиля.\n"
    else:
        text += "💡 <b>Совет:</b> Чем больше вакансий ты оценишь,\n"
        text += "тем лучше я смогу подбирать предложения!\n"

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
    """Персональные рекомендации"""
    telegram_id = callback.from_user.id

    await callback.message.edit_caption(
        caption="⏳ Генерирую рекомендации...",
        parse_mode="HTML"
    )

    insights = await api.get_user_insights(telegram_id)
    user = await api.get_user(telegram_id)

    if not insights or not user:
        await callback.answer("❌ Ошибка загрузки", show_alert=True)
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
            text="✏️ Применить рекомендации",
            callback_data="insights:apply_recommendations"
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


@router.callback_query(F.data == "insights:apply_recommendations")
async def apply_recommendations(callback: CallbackQuery, state: FSMContext):
    """Применить рекомендации - переход к редактированию профиля"""
    telegram_id = callback.from_user.id

    insights = await api.get_user_insights(telegram_id)

    if not insights or not insights.get('recommendations'):
        await callback.answer(
            "Нет доступных рекомендаций",
            show_alert=True
        )
        return

    recommendations = insights['recommendations']

    text = "✏️ <b>Применяем рекомендации</b>\n\n"
    text += "Я помогу тебе обновить профиль на основе анализа.\n\n"
    text += "<b>Что будем менять:</b>\n"

    for i, rec in enumerate(recommendations[:3], 1):
        text += f"{i}. {rec.get('type', 'general').capitalize()}\n"

    text += "\nВыбери, что хочешь обновить:"

    builder = InlineKeyboardBuilder()

    for rec in recommendations[:3]:
        rec_type = rec.get('type', 'general')

        if rec_type == 'skills':
            builder.button(
                text="🛠 Обновить технологии",
                callback_data="edit:stack"
            )
        elif rec_type == 'salary':
            builder.button(
                text="💰 Изменить зарплату",
                callback_data="edit:salary"
            )
        elif rec_type == 'location':
            builder.button(
                text="🌍 Изменить локацию",
                callback_data="edit:location"
            )

    builder.button(text="✏️ Редактировать весь профиль", callback_data="edit:full")
    builder.button(text="❌ Отмена", callback_data="menu:insights")
    builder.adjust(1)

    await callback.message.edit_caption(
        caption=text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()