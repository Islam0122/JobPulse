from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List, Dict


def get_level_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для выбора уровня"""
    kb = ReplyKeyboardBuilder()
    levels = ["Junior", "Middle", "Senior", "Lead"]

    for level in levels:
        kb.add(KeyboardButton(text=level))

    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


def get_stack_keyboard(stacks: List[Dict], selected: List[int] = None) -> InlineKeyboardMarkup:
    """Клавиатура для выбора стека (множественный выбор)"""
    if selected is None:
        selected = []

    builder = InlineKeyboardBuilder()

    for stack in stacks:
        stack_id = stack['id']
        stack_name = stack['name']

        # Добавляем ✅ к выбранным
        prefix = "✅ " if stack_id in selected else ""

        builder.button(
            text=f"{prefix}{stack_name}",
            callback_data=f"stack_{stack_id}"
        )

    builder.adjust(3)

    # Кнопка "Готово"
    if selected:
        builder.row(InlineKeyboardButton(
            text=f"✅ Готово ({len(selected)})",
            callback_data="stack_done"
        ))

    return builder.as_markup()


def get_work_format_keyboard(formats: List[Dict], selected: List[int] = None) -> InlineKeyboardMarkup:
    """Клавиатура для выбора формата работы"""
    if selected is None:
        selected = []

    builder = InlineKeyboardBuilder()

    for fmt in formats:
        fmt_id = fmt['id']
        fmt_title = fmt['title']

        prefix = "✅ " if fmt_id in selected else ""

        builder.button(
            text=f"{prefix}{fmt_title}",
            callback_data=f"workformat_{fmt_id}"
        )

    builder.adjust(1)

    if selected:
        builder.row(InlineKeyboardButton(
            text="✅ Готово",
            callback_data="workformat_done"
        ))

    return builder.as_markup()


def get_employment_type_keyboard(types: List[Dict], selected: List[int] = None) -> InlineKeyboardMarkup:
    """Клавиатура для выбора типа занятости"""
    if selected is None:
        selected = []

    builder = InlineKeyboardBuilder()

    for emp_type in types:
        type_id = emp_type['id']
        type_title = emp_type['title']

        prefix = "✅ " if type_id in selected else ""

        builder.button(
            text=f"{prefix}{type_title}",
            callback_data=f"employment_{type_id}"
        )

    builder.adjust(1)

    if selected:
        builder.row(InlineKeyboardButton(
            text="✅ Готово",
            callback_data="employment_done"
        ))

    return builder.as_markup()


def get_currency_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для выбора валюты"""
    kb = ReplyKeyboardBuilder()
    currencies = ["USD 💵", "EUR 💶", "RUB ₽", "KZT ₸"]

    for currency in currencies:
        kb.add(KeyboardButton(text=currency))

    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


def get_notification_mode_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для выбора режима уведомлений"""
    kb = ReplyKeyboardBuilder()
    modes = [
        "Сразу 🔔",
        "Ежедневно 📅",
        "Еженедельно 📆"
    ]

    for mode in modes:
        kb.add(KeyboardButton(text=mode))

    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def get_skip_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой пропустить"""
    kb = ReplyKeyboardBuilder()
    kb.add(KeyboardButton(text="⏭ Пропустить"))
    return kb.as_markup(resize_keyboard=True)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню после завершения онбординга"""
    kb = ReplyKeyboardBuilder()

    buttons = [
        "📊 Мой профиль",
        "🔔 Настройки уведомлений",
        "✏️ Редактировать профиль",
        "❓ Помощь"
    ]

    for button in buttons:
        kb.add(KeyboardButton(text=button))

    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)