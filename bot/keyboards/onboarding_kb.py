from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict


def get_level_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора уровня"""
    builder = InlineKeyboardBuilder()
    levels = ["Junior", "Middle", "Senior", "Lead"]

    for level in levels:
        builder.button(
            text=level,
            callback_data=f"level:{level.lower()}"
        )

    builder.adjust(2)  # 2 кнопки в ряд
    return builder.as_markup()


def get_stack_keyboard(
        stacks: List[Dict],
        selected: List[int] | None = None
) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора технологий

    Args:
        stacks: Список технологий с сервера
        selected: ID выбранных технологий
    """
    selected = selected or []
    builder = InlineKeyboardBuilder()

    for stack in stacks:
        # Добавляем галочку если выбрано
        prefix = "✅ " if stack["id"] in selected else ""
        builder.button(
            text=f"{prefix}{stack['name']}",
            callback_data=f"stack:{stack['id']}"
        )

    builder.adjust(3)  # 3 кнопки в ряд

    # Кнопка "Готово" появляется только если что-то выбрано
    if selected:
        builder.row(
            InlineKeyboardButton(
                text=f"✅ Готово ({len(selected)})",
                callback_data="stack:done"
            )
        )

    return builder.as_markup()


def get_work_format_keyboard(
        formats: List[Dict],
        selected: List[int] | None = None
) -> InlineKeyboardMarkup:
    """Клавиатура выбора формата работы"""
    selected = selected or []
    builder = InlineKeyboardBuilder()

    for fmt in formats:
        prefix = "✅ " if fmt["id"] in selected else ""
        builder.button(
            text=f"{prefix}{fmt['title']}",
            callback_data=f"workformat:{fmt['id']}"
        )

    builder.adjust(1)  # Вертикально

    if selected:
        builder.row(
            InlineKeyboardButton(
                text="✅ Готово",
                callback_data="workformat:done"
            )
        )

    return builder.as_markup()


def get_employment_type_keyboard(
        types: List[Dict],
        selected: List[int] | None = None
) -> InlineKeyboardMarkup:
    """Клавиатура выбора типа занятости"""
    selected = selected or []
    builder = InlineKeyboardBuilder()

    for t in types:
        prefix = "✅ " if t["id"] in selected else ""
        builder.button(
            text=f"{prefix}{t['title']}",
            callback_data=f"employment:{t['id']}"
        )

    builder.adjust(1)

    if selected:
        builder.row(
            InlineKeyboardButton(
                text="✅ Готово",
                callback_data="employment:done"
            )
        )

    return builder.as_markup()


def get_currency_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора валюты"""
    builder = InlineKeyboardBuilder()
    currencies = [
        ("USD 💵", "USD"),
        ("EUR 💶", "EUR"),
        ("RUB ₽", "RUB"),
        ("KZT ₸", "KZT"),
    ]

    for text, code in currencies:
        builder.button(
            text=text,
            callback_data=f"currency:{code}"
        )

    builder.adjust(2)
    return builder.as_markup()


def get_notification_mode_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора режима уведомлений"""
    builder = InlineKeyboardBuilder()
    modes = [
        ("Сразу 🔔", "instant"),
        ("Ежедневно 📅", "daily"),
        ("Еженедельно 📆", "weekly"),
    ]

    for text, value in modes:
        builder.button(
            text=text,
            callback_data=f"notify:{value}"
        )

    builder.adjust(1)
    return builder.as_markup()


def get_notification_mode_keyboard2() -> InlineKeyboardMarkup:
    """Клавиатура настроек уведомлений с кнопкой назад"""
    builder = InlineKeyboardBuilder()

    modes = [
        ("Сразу 🔔", "notify:instant"),
        ("Ежедневно 📅", "notify:daily"),
        ("Еженедельно 📆", "notify:weekly"),
    ]

    for text, callback_data in modes:
        builder.button(
            text=text,
            callback_data=callback_data
        )

    builder.adjust(1)

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="menu:home"
        )
    )

    return builder.as_markup()


def get_skip_keyboard() -> InlineKeyboardMarkup:
    """Кнопка пропуска (для необязательных полей)"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⏭ Пропустить",
        callback_data="skip"
    )
    return builder.as_markup()


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Главное меню бота
    Показывается после успешного онбординга
    """
    builder = InlineKeyboardBuilder()

    buttons = [
        ("💼 Вакансии", "menu:vacancies"),
        ("📊 Мой профиль", "menu:profile"),
        ("📈 Аналитика", "menu:insights"),
        ("🔔 Настройки", "menu:settings"),
        ("❓ Помощь", "menu:help"),
        ("💡 Почему бот бесплатный?", "sponsors:info"),
    ]

    for text, cb in buttons:
        builder.button(text=text, callback_data=cb)

    builder.adjust(1, 2, 2, 2)  # Раскладка кнопок
    return builder.as_markup()


def get_return_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="⬅️ Назад",
        callback_data="menu:home"
    )

    return builder.as_markup()