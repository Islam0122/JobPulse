from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict


def get_level_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    levels = ["Junior", "Middle", "Senior", "Lead"]

    for level in levels:
        builder.button(
            text=level,
            callback_data=f"level:{level.lower()}"
        )

    builder.adjust(2)
    return builder.as_markup()


def get_stack_keyboard(
    stacks: List[Dict],
    selected: List[int] | None = None
) -> InlineKeyboardMarkup:
    selected = selected or []
    builder = InlineKeyboardBuilder()

    for stack in stacks:
        prefix = "✅ " if stack["id"] in selected else ""
        builder.button(
            text=f"{prefix}{stack['name']}",
            callback_data=f"stack:{stack['id']}"
        )

    builder.adjust(3)

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
    selected = selected or []
    builder = InlineKeyboardBuilder()

    for fmt in formats:
        prefix = "✅ " if fmt["id"] in selected else ""
        builder.button(
            text=f"{prefix}{fmt['title']}",
            callback_data=f"workformat:{fmt['id']}"
        )

    builder.adjust(1)

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


def get_skip_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⏭ Пропустить",
        callback_data="skip"
    )
    return builder.as_markup()


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    buttons = [
        ("📊 Мой профиль", "menu:profile"),
        ("🔔 Настройки", "menu:notifications"),
        ("✏️ Редактировать", "menu:edit"),
        ("❓ Помощь", "menu:help"),
    ]

    for text, cb in buttons:
        builder.button(text=text, callback_data=cb)

    builder.adjust(2)
    return builder.as_markup()
