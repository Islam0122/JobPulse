from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.api_client import api
from typing import List, Dict
import html
router = Router()


@router.callback_query(F.data == "menu:vacancies")
async def show_vacancies_menu(callback: CallbackQuery):
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
    telegram_id = callback.from_user.id
    vacancies = await api.get_recommended_vacancies(telegram_id, limit=10)

    if not vacancies:
        await callback.answer(
            "🤷‍♂️ Пока нет подходящих вакансий.\n"
            "Попробуй изменить настройки профиля.",
            show_alert=True
        )
        return

    await show_vacancy_card(callback, vacancies, 0, "recommended")


@router.callback_query(F.data == "vacancies:all")
async def show_all_vacancies(callback: CallbackQuery):
    vacancies = await api.get_vacancies(limit=20)

    if not vacancies:
        await callback.answer("Вакансий пока нет", show_alert=True)
        return

    await show_vacancy_card(callback, vacancies, 0, "all")


async def show_vacancy_card(
        callback: CallbackQuery,
        vacancies: List[Dict],
        index: int,
        source: str
):
    if index >= len(vacancies):
        await callback.answer("Вакансии закончились", show_alert=True)
        return

    vacancy = vacancies[index]
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
    lines = [
        f"💼 <b>Вакансия {current}/{total}</b>\n",
        f"<b>{html.escape(vacancy['title'])}</b>",
        f"🏢 {html.escape(vacancy['company_name'])}\n"
    ]

    if vacancy.get('salary_range'):
        lines.append(f"💰 <b>Зарплата:</b> {vacancy['salary_range']}")

    if vacancy.get('location'):
        lines.append(f"📍 <b>Локация:</b> {vacancy['location']}")

    if vacancy.get('experience'):
        lines.append(f"⏳ <b>Опыт:</b> {vacancy['experience']}")

    if vacancy.get('employment'):
        lines.append(f"📋 <b>Занятость:</b> {vacancy['employment']}")

    if vacancy.get('schedule'):
        lines.append(f"🕐 <b>График:</b> {vacancy['schedule']}")

    if vacancy.get('skills'):
        skills_text = ", ".join(vacancy['skills'][:7])
        if len(vacancy['skills']) > 7:
            skills_text += f" и еще {len(vacancy['skills']) - 7}"
        lines.append(f"\n🛠 <b>Навыки:</b> {skills_text}")

    if vacancy.get('description'):
        desc = vacancy['description'][:300]
        if len(vacancy['description']) > 300:
            desc += "..."
        lines.append(f"\n📝 <b>Описание:</b>\n{html.escape(desc)}")

    return "\n".join(lines)


def build_vacancy_keyboard(
        vacancy_id: int,
        current_index: int,
        total: int,
        source: str,
        hh_url: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="👍 Интересно",
        callback_data=f"vacancy:like:{vacancy_id}:{source}:{current_index}"
    )
    builder.button(
        text="👎 Не подходит",
        callback_data=f"vacancy:dislike:{vacancy_id}:{source}:{current_index}"
    )

    builder.button(
        text="⭐️ В избранное",
        callback_data=f"vacancy:favorite:{vacancy_id}:{source}:{current_index}"
    )
    builder.button(
        text="📝 Полное описание",
        callback_data=f"vacancy:full:{vacancy_id}:{source}:{current_index}"
    )

    if current_index > 0:
        builder.button(
            text="⬅️ Пред.",
            callback_data=f"vacancy:nav:{source}:{current_index - 1}"
        )

    builder.button(
        text=f"{current_index + 1}/{total}",
        callback_data="vacancy:noop"
    )

    if current_index < total - 1:
        builder.button(
            text="След. ➡️",
            callback_data=f"vacancy:nav:{source}:{current_index + 1}"
        )

    builder.button(text="🔗 Открыть на HH.ru", url=hh_url)
    builder.button(text="🔙 К списку", callback_data="menu:vacancies")

    builder.adjust(2, 2, 3, 2)
    return builder.as_markup()



@router.callback_query(F.data.startswith("vacancy:like:"))
async def vacancy_like(callback: CallbackQuery):
    parts = callback.data.split(":")
    vacancy_id = int(parts[2])
    source = parts[3]
    current_index = int(parts[4])

    telegram_id = callback.from_user.id

    await api.react_to_vacancy(telegram_id, vacancy_id, "like")
    await callback.answer("👍 Отмечено как интересное", show_alert=False)
    vacancies = await get_vacancies_by_source(source, telegram_id)
    if current_index + 1 < len(vacancies):
        await show_vacancy_card(callback, vacancies, current_index + 1, source)


@router.callback_query(F.data.startswith("vacancy:dislike:"))
async def vacancy_dislike(callback: CallbackQuery):
    parts = callback.data.split(":")
    vacancy_id = int(parts[2])
    source = parts[3]
    current_index = int(parts[4])

    telegram_id = callback.from_user.id

    await api.react_to_vacancy(telegram_id, vacancy_id, "dislike")

    await callback.answer("👎 Учтем в рекомендациях", show_alert=False)

    vacancies = await get_vacancies_by_source(source, telegram_id)
    if current_index + 1 < len(vacancies):
        await show_vacancy_card(callback, vacancies, current_index + 1, source)


@router.callback_query(F.data.startswith("vacancy:favorite:"))
async def vacancy_favorite(callback: CallbackQuery):
    parts = callback.data.split(":")
    vacancy_id = int(parts[2])

    telegram_id = callback.from_user.id

    result = await api.add_to_favorites(telegram_id, vacancy_id)

    if result:
        await callback.answer("⭐️ Добавлено в избранное!", show_alert=False)
    else:
        await callback.answer("❌ Ошибка добавления", show_alert=True)


@router.callback_query(F.data.startswith("vacancy:full:"))
async def vacancy_full_description(callback: CallbackQuery):
    parts = callback.data.split(":")
    vacancy_id = int(parts[2])

    vacancy = await api.get_vacancy_detail(vacancy_id)

    if not vacancy:
        await callback.answer("Вакансия не найдена", show_alert=True)
        return

    full_text = f"<b>{html.escape(vacancy['title'])}</b>\n\n"
    full_text += f"<b>Описание:</b>\n{html.escape(vacancy['description'])}"

    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Открыть на HH.ru", url=vacancy['url'])
    builder.button(text="🔙 Назад", callback_data=f"vacancy:back:{parts[3]}:{parts[4]}")
    builder.adjust(1)

    await callback.message.answer(
        text=full_text[:4096],  # Telegram limit
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("vacancy:nav:"))
async def vacancy_navigation(callback: CallbackQuery):
    parts = callback.data.split(":")
    source = parts[2]
    index = int(parts[3])

    telegram_id = callback.from_user.id
    vacancies = await get_vacancies_by_source(source, telegram_id)

    await show_vacancy_card(callback, vacancies, index, source)


async def get_vacancies_by_source(source: str, telegram_id: int) -> List[Dict]:
    if source == "recommended":
        return await api.get_recommended_vacancies(telegram_id, limit=20)
    elif source == "all":
        return await api.get_vacancies(limit=20)
    elif source == "favorites":
        return await api.get_favorite_vacancies(telegram_id)
    else:
        return []


@router.callback_query(F.data == "vacancy:noop")
async def vacancy_noop(callback: CallbackQuery):
    await callback.answer()