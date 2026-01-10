from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.api_client import api
from typing import List, Dict
import html

router = Router()


@router.callback_query(F.data == "menu:vacancies")
async def show_vacancies_menu(callback: CallbackQuery):
    """Главное меню вакансий"""
    text = (
        "💼 <b>Вакансии</b>\n\n"
        "Выбери действие:"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="🎯 Рекомендации для меня", callback_data="vacancies:recommended")
    builder.button(text="🔍 Все вакансии", callback_data="vacancies:all")
    builder.button(text="⭐️ Избранное", callback_data="vacancies:favorites")
    builder.button(text="📋 История просмотров", callback_data="vacancies:history")
    builder.button(text="⬅️ Назад", callback_data="menu:home")
    builder.adjust(2, 2, 1)

    await callback.message.edit_caption(
        caption=text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "vacancies:recommended")
async def show_recommended_vacancies(callback: CallbackQuery):
    """Показать персональные рекомендации"""
    telegram_id = callback.from_user.id

    await callback.message.edit_caption(
        caption="⏳ Загружаю рекомендации...",
        parse_mode="HTML"
    )

    vacancies = await api.get_recommended_vacancies(telegram_id, limit=20)

    if not vacancies:
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Назад", callback_data="menu:vacancies")

        await callback.message.edit_caption(
            caption=(
                "🤷‍♂️ <b>Пока нет подходящих вакансий</b>\n\n"
                "Попробуй:\n"
                "• Изменить настройки профиля\n"
                "• Добавить больше технологий\n"
                "• Проверить позже - мы парсим вакансии каждые 30 минут"
            ),
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    await show_vacancy_card(callback, vacancies, 0, "recommended")


@router.callback_query(F.data == "vacancies:all")
async def show_all_vacancies(callback: CallbackQuery):
    """Показать все активные вакансии"""
    await callback.message.edit_caption(
        caption="⏳ Загружаю вакансии...",
        parse_mode="HTML"
    )

    vacancies = await api.get_vacancies(limit=50)

    if not vacancies:
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Назад", callback_data="menu:vacancies")

        await callback.message.edit_caption(
            caption="😔 Вакансий пока нет. Проверьте позже.",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    await show_vacancy_card(callback, vacancies, 0, "all")


@router.callback_query(F.data == "vacancies:favorites")
async def show_favorite_vacancies(callback: CallbackQuery):
    """Показать избранные вакансии"""
    telegram_id = callback.from_user.id

    await callback.message.edit_caption(
        caption="⏳ Загружаю избранное...",
        parse_mode="HTML"
    )

    favorites = await api.get_favorite_vacancies(telegram_id)

    if not favorites:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔍 Смотреть вакансии", callback_data="vacancies:recommended")
        builder.button(text="⬅️ Назад", callback_data="menu:vacancies")
        builder.adjust(1)

        await callback.message.edit_caption(
            caption=(
                "⭐️ <b>Избранное пусто</b>\n\n"
                "Начни добавлять интересные вакансии,\n"
                "чтобы вернуться к ним позже!"
            ),
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # Преобразуем формат избранного
    vacancies = [fav['vacancy'] for fav in favorites]
    await show_vacancy_card(callback, vacancies, 0, "favorites")


@router.callback_query(F.data == "vacancies:history")
async def show_vacancy_history(callback: CallbackQuery):
    """Показать историю просмотренных вакансий"""
    telegram_id = callback.from_user.id

    await callback.message.edit_caption(
        caption="⏳ Загружаю историю...",
        parse_mode="HTML"
    )

    vacancies = await api.get_vacancy_history(telegram_id)

    if not vacancies:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔍 Смотреть вакансии", callback_data="vacancies:recommended")
        builder.button(text="⬅️ Назад", callback_data="menu:vacancies")
        builder.adjust(1)

        await callback.message.edit_caption(
            caption=(
                "📋 <b>История пуста</b>\n\n"
                "Здесь будут отображаться вакансии,\n"
                "которые ты просмотрел."
            ),
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    await show_vacancy_card(callback, vacancies, 0, "history")


async def show_vacancy_card(
        callback: CallbackQuery,
        vacancies: List[Dict],
        index: int,
        source: str
):
    """
    Показать карточку вакансии

    Args:
        vacancies: Список вакансий
        index: Индекс текущей вакансии
        source: Источник (recommended/all/favorites/history)
    """
    if index >= len(vacancies):
        await callback.answer("Вакансии закончились", show_alert=True)
        return

    vacancy = vacancies[index]
    telegram_id = callback.from_user.id

    await api.mark_vacancy_viewed(telegram_id, vacancy['id'])
    text = format_vacancy_full(vacancy, index + 1, len(vacancies))
    keyboard = build_vacancy_keyboard(
        vacancy_id=vacancy['id'],
        current_index=index,
        total=len(vacancies),
        source=source,
        hh_url=vacancy.get('url')
    )

    try:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception:
        pass

    await callback.answer()


def format_vacancy_full(vacancy: Dict, current: int, total: int) -> str:
    """Форматирование полной карточки вакансии"""
    lines = [
        f"💼 <b>Вакансия {current}/{total}</b>\n",
        f"<b>{html.escape(vacancy['title'])}</b>",
        f"🏢 {html.escape(vacancy['company_name'])}\n"
    ]

    if vacancy.get('salary_range'):
        lines.append(f"💰 <b>Зарплата:</b> {vacancy['salary_range']}")

    if vacancy.get('location'):
        lines.append(f"📍 <b>Локация:</b> {html.escape(vacancy['location'])}")

    if vacancy.get('experience'):
        lines.append(f"⏳ <b>Опыт:</b> {html.escape(vacancy['experience'])}")

    if vacancy.get('employment'):
        lines.append(f"📋 <b>Занятость:</b> {html.escape(vacancy['employment'])}")

    if vacancy.get('schedule'):
        lines.append(f"🕐 <b>График:</b> {html.escape(vacancy['schedule'])}")

    if vacancy.get('skills'):
        skills_text = ", ".join(vacancy['skills'][:7])
        if len(vacancy['skills']) > 7:
            skills_text += f" и еще {len(vacancy['skills']) - 7}"
        lines.append(f"\n🛠 <b>Навыки:</b> {html.escape(skills_text)}")

    if vacancy.get('description'):
        desc = vacancy['description'][:250]
        if len(vacancy['description']) > 250:
            desc += "..."
        lines.append(f"\n📝 <b>Описание:</b>\n{html.escape(desc)}")

    return "\n".join(lines)


def build_vacancy_keyboard(
        vacancy_id: int,
        current_index: int,
        total: int,
        source: str,
        hh_url: str
) -> InlineKeyboardBuilder:
    """Клавиатура для карточки вакансии"""
    builder = InlineKeyboardBuilder()

    # Лайк/Дизлайк
    builder.button(
        text="👍 Интересно",
        callback_data=f"vacancy:like:{vacancy_id}:{source}:{current_index}"
    )
    builder.button(
        text="👎 Не подходит",
        callback_data=f"vacancy:dislike:{vacancy_id}:{source}:{current_index}"
    )

    # Избранное
    builder.button(
        text="⭐️ В избранное",
        callback_data=f"vacancy:favorite:{vacancy_id}:{source}:{current_index}"
    )

    # Полное описание
    builder.button(
        text="📝 Полное описание",
        callback_data=f"vacancy:full:{vacancy_id}:{source}:{current_index}"
    )

    # Навигация
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(
            InlineKeyboardBuilder().button(
                text="⬅️",
                callback_data=f"vacancy:nav:{source}:{current_index - 1}"
            ).as_markup().inline_keyboard[0][0]
        )

    nav_buttons.append(
        InlineKeyboardBuilder().button(
            text=f"{current_index + 1}/{total}",
            callback_data="vacancy:noop"
        ).as_markup().inline_keyboard[0][0]
    )

    if current_index < total - 1:
        nav_buttons.append(
            InlineKeyboardBuilder().button(
                text="➡️",
                callback_data=f"vacancy:nav:{source}:{current_index + 1}"
            ).as_markup().inline_keyboard[0][0]
        )

    # Ссылка на HH.ru
    builder.button(text="🔗 Открыть на HH.ru", url=hh_url)
    builder.button(text="🔙 К меню", callback_data="menu:vacancies")

    builder.adjust(2, 2, len(nav_buttons), 1, 1)

    # Добавляем навигацию
    kb = builder.as_markup()
    kb.inline_keyboard.insert(-2, nav_buttons)

    return kb


@router.callback_query(F.data.startswith("vacancy:like:"))
async def vacancy_like(callback: CallbackQuery):
    """Лайк вакансии"""
    parts = callback.data.split(":")
    vacancy_id = int(parts[2])
    source = parts[3]
    current_index = int(parts[4])

    telegram_id = callback.from_user.id

    result = await api.react_to_vacancy(telegram_id, vacancy_id, "like")

    if result:
        await callback.answer("👍 Отмечено как интересное", show_alert=False)

        # Переходим к следующей вакансии
        vacancies = await get_vacancies_by_source(source, telegram_id)
        if vacancies and current_index + 1 < len(vacancies):
            await show_vacancy_card(callback, vacancies, current_index + 1, source)
    else:
        await callback.answer("❌ Ошибка. Попробуйте позже", show_alert=True)


@router.callback_query(F.data.startswith("vacancy:dislike:"))
async def vacancy_dislike(callback: CallbackQuery):
    """Дизлайк вакансии"""
    parts = callback.data.split(":")
    vacancy_id = int(parts[2])
    source = parts[3]
    current_index = int(parts[4])

    telegram_id = callback.from_user.id

    result = await api.react_to_vacancy(telegram_id, vacancy_id, "dislike")

    if result:
        await callback.answer("👎 Учтем в рекомендациях", show_alert=False)

        # Переходим к следующей вакансии
        vacancies = await get_vacancies_by_source(source, telegram_id)
        if vacancies and current_index + 1 < len(vacancies):
            await show_vacancy_card(callback, vacancies, current_index + 1, source)
    else:
        await callback.answer("❌ Ошибка. Попробуйте позже", show_alert=True)


@router.callback_query(F.data.startswith("vacancy:favorite:"))
async def vacancy_favorite(callback: CallbackQuery):
    """Добавить в избранное"""
    parts = callback.data.split(":")
    vacancy_id = int(parts[2])

    telegram_id = callback.from_user.id

    result = await api.add_to_favorites(telegram_id, vacancy_id)

    if result:
        if result.get('status') == 'already_exists':
            await callback.answer("⭐️ Уже в избранном!", show_alert=False)
        else:
            await callback.answer("⭐️ Добавлено в избранное!", show_alert=False)
    else:
        await callback.answer("❌ Ошибка добавления", show_alert=True)


@router.callback_query(F.data.startswith("vacancy:full:"))
async def vacancy_full_description(callback: CallbackQuery):
    """Показать полное описание"""
    parts = callback.data.split(":")
    vacancy_id = int(parts[2])
    source = parts[3]
    current_index = int(parts[4])

    vacancy = await api.get_vacancy_detail(vacancy_id)
    telegram_id = callback.from_user.id
    await api.mark_vacancy_viewed(telegram_id, vacancy_id)

    if not vacancy:
        await callback.answer("Вакансия не найдена", show_alert=True)
        return

    # Полное описание
    full_text = f"<b>{html.escape(vacancy['title'])}</b>\n"
    full_text += f"🏢 {html.escape(vacancy['company_name'])}\n\n"

    if vacancy.get('salary_range'):
        full_text += f"💰 {vacancy['salary_range']}\n"
    if vacancy.get('location'):
        full_text += f"📍 {html.escape(vacancy['location'])}\n"
    if vacancy.get('experience'):
        full_text += f"⏳ {html.escape(vacancy['experience'])}\n\n"

    # Описание (с обрезкой под лимит Telegram)
    desc = vacancy.get('description', '')
    max_length = 900  # Оставляем место для заголовка
    if len(desc) > max_length:
        desc = desc[:max_length] + "..."

    full_text += f"<b>Описание:</b>\n{html.escape(desc)}"

    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Читать на HH.ru", url=vacancy['url'])
    builder.button(
        text="⬅️ Назад к вакансии",
        callback_data=f"vacancy:back:{source}:{current_index}"
    )
    builder.adjust(1)

    await callback.message.edit_caption(
        caption=full_text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("vacancy:back:"))
async def vacancy_back(callback: CallbackQuery):
    """Вернуться к карточке вакансии"""
    parts = callback.data.split(":")
    source = parts[2]
    index = int(parts[3])

    telegram_id = callback.from_user.id
    vacancies = await get_vacancies_by_source(source, telegram_id)

    if vacancies:
        await show_vacancy_card(callback, vacancies, index, source)
    else:
        await callback.answer("❌ Ошибка загрузки", show_alert=True)


@router.callback_query(F.data.startswith("vacancy:nav:"))
async def vacancy_navigation(callback: CallbackQuery):
    """Навигация между вакансиями"""
    parts = callback.data.split(":")
    source = parts[2]
    index = int(parts[3])

    telegram_id = callback.from_user.id
    vacancies = await get_vacancies_by_source(source, telegram_id)
    vacancy = vacancies[index]
    await api.mark_vacancy_viewed(telegram_id, vacancy['id'])

    if vacancies:
        await show_vacancy_card(callback, vacancies, index, source)
    else:
        await callback.answer("❌ Ошибка загрузки", show_alert=True)


@router.callback_query(F.data == "vacancy:noop")
async def vacancy_noop(callback: CallbackQuery):
    """Пустой callback для счетчика"""
    await callback.answer()


async def get_vacancies_by_source(
        source: str,
        telegram_id: int
) -> List[Dict]:
    """
    Получить вакансии в зависимости от источника

    Args:
        source: recommended/all/favorites/history
        telegram_id: ID пользователя
    """
    if source == "recommended":
        return await api.get_recommended_vacancies(telegram_id, limit=20)
    elif source == "all":
        return await api.get_vacancies(limit=50)
    elif source == "favorites":
        favorites = await api.get_favorite_vacancies(telegram_id)
        return [fav['vacancy'] for fav in favorites]
    elif source == "history":
        return await api.get_vacancy_history(telegram_id)
    else:
        return []