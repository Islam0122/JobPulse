from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from services.api_client import api
from keyboards.onboarding_kb import *

router = Router()
logo = "AgACAgIAAxkBAAICS2lb4BQM-xj2JkiR0jz7BfJDHv6RAAKAEWsbTSzYSl2zO5BmDzyyAQADAgADeQADOAQ"


def build_profile_text(user: dict) -> str:
    """Форматирование текста профиля"""
    stack_text = ", ".join(s["name"] for s in user.get("stack", [])) or "Не указано"
    work_format_text = ", ".join(w["title"] for w in user.get("work_formats", [])) or "Не указано"
    employment_text = ", ".join(e["title"] for e in user.get("employment_types", [])) or "Не указано"

    salary_text = (
        f"{user['salary_from']} {user['currency']}"
        if user.get("salary_from")
        else "Не указано"
    )

    return f"""👤 <b>Твой профиль</b>

📝 <b>Роль:</b> {user.get('role', 'Не указано')}
🎯 <b>Уровень:</b> {user.get('level_label', 'Не указано')}
🛠 <b>Стек:</b> {stack_text}

🏢 <b>Формат работы:</b> {work_format_text}
📋 <b>Занятость:</b> {employment_text}
🌍 <b>Локация:</b> {user.get('location', 'Не указано')}
💰 <b>Зарплата от:</b> {salary_text}

🔔 <b>Уведомления:</b> {user.get('notify_mode_label', 'Не указано')}
✅ <b>Статус:</b> {'Активен' if user.get('is_active') else 'Неактивен'}
"""


MENU_TEXT = (
    "🏠 <b>Главное меню</b>\n\n"
    "Выбери действие 👇"
)


@router.callback_query(F.data == "menu:home")
async def show_menu(callback: CallbackQuery):
    """Главное меню"""
    await callback.message.edit_caption(
        caption=MENU_TEXT,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:profile")
async def show_profile_callback(callback: CallbackQuery):
    """Показать профиль"""
    user = await api.get_user(callback.from_user.id)

    if not user:
        await callback.answer("Профиль не найден", show_alert=True)
        return

    # Добавляем кнопку "Редактировать"
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать профиль", callback_data="edit:full")
    builder.button(text="⬅️ Назад", callback_data="menu:home")
    builder.adjust(1)

    try:
        await callback.message.edit_caption(
            caption=build_profile_text(user),
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=logo,
            caption=build_profile_text(user),
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    await callback.answer()


HELP_TEXT = """❓ <b>Помощь</b>

<b>Что умеет бот:</b>
• Помогает найти подходящие вакансии
• Учитывает твой профиль и предпочтения
• Присылает уведомления автоматически
• Анализирует твои предпочтения

<b>Разделы меню:</b>
💼 Вакансии — просмотр вакансий  
📊 Мой профиль — твои данные  
📈 Аналитика — статистика и рекомендации
🔔 Настройки — частота уведомлений  
❓ Помощь — этот экран  

<b>Как работать с вакансиями:</b>
1️⃣ Открой раздел "Вакансии"
2️⃣ Смотри рекомендации
3️⃣ Ставь 👍 или 👎
4️⃣ Добавляй в ⭐️ избранное

<b>Как это работает:</b>
1️⃣ Ты заполняешь профиль  
2️⃣ Бот парсит вакансии с HH.ru
3️⃣ Алгоритм подбирает подходящие
4️⃣ Ты получаешь уведомления  

<b>Частота уведомлений:</b>
• Сразу 🔔 — как только найдена подходящая вакансия
• Ежедневно 📅 — дайджест раз в день
• Еженедельно 📆 — сводка раз в неделю

<b>Поддержка:</b> @islam_duishobaev
"""


@router.callback_query(F.data == "menu:help")
async def show_help(callback: CallbackQuery):
    """Помощь"""
    await callback.message.edit_caption(
        caption=HELP_TEXT,
        parse_mode="HTML",
        reply_markup=get_return_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "sponsors:info")
async def sponsors_info_callback(callback: CallbackQuery):
    """Информация о спонсорах"""
    channels = await api.get_required_channels()

    text = (
        "💡 <b>Почему нужна подписка?</b>\n\n"
        "Этот бот полностью <b>бесплатный</b>.\n"
        "Он работает и развивается благодаря поддержке\n"
        "<b>каналов-спонсоров</b>.\n\n"
        "📌 Подписка позволяет:\n"
        "• поддерживать серверы и разработку\n"
        "• сохранять доступ ко всем функциям\n"
        "• избегать платных подписок\n\n"
        "📢 <b>Наши спонсоры:</b>\n"
    )

    if channels:
        for ch in channels:
            title = ch["title"]
            username = ch.get("username")

            if username:
                text += f"• <b>{title}</b> — {username}\n"
            else:
                text += f"• <b>{title}</b>\n"
    else:
        text += "• Сейчас нет активных спонсоров\n"

    text += "\n🙏 Спасибо за поддержку проекта!"

    await callback.message.edit_caption(
        caption=text,
        parse_mode="HTML",
        reply_markup=get_return_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:settings")
async def notification_settings_callback(callback: CallbackQuery):
    """Настройки уведомлений"""
    telegram_id = callback.from_user.id
    user = await api.get_user(telegram_id)

    if not user:
        await callback.answer("❌ Профиль не найден.", show_alert=True)
        return

    try:
        await callback.message.edit_caption(
            caption=f"🔔 <b>Настройки уведомлений</b>\n\n"
                    f"<b>Текущий режим:</b> {user.get('notify_mode_label')}\n\n"
                    f"Выбери новый режим:",
            parse_mode="HTML",
            reply_markup=get_notification_mode_keyboard2()
        )
    except Exception:
        await callback.message.answer_photo(
            photo=logo,
            caption=f"🔔 <b>Настройки уведомлений</b>\n\n"
                    f"<b>Текущий режим:</b> {user.get('notify_mode_label')}\n\n"
                    f"Выбери новый режим:",
            parse_mode="HTML",
            reply_markup=get_notification_mode_keyboard2()
        )

    await callback.answer()


@router.callback_query(F.data.startswith("notify:"))
async def update_notifications_callback(callback: CallbackQuery):
    """Обновить режим уведомлений"""
    notify_mode = callback.data.split(":")[1]
    telegram_id = callback.from_user.id

    mode_labels = {
        "instant": "Сразу 🔔",
        "daily": "Ежедневно 📅",
        "weekly": "Еженедельно 📆"
    }

    result = await api.update_notification_mode(telegram_id, notify_mode)

    if result:
        mode_label = mode_labels.get(notify_mode, notify_mode)

        try:
            await callback.message.edit_caption(
                caption=f"✅ <b>Настройки сохранены!</b>\n\n"
                        f"Режим уведомлений: {mode_label}",
                parse_mode="HTML",
                reply_markup=get_return_keyboard()
            )
        except Exception:
            await callback.message.answer(
                f"✅ <b>Настройки сохранены!</b>\n\n"
                f"Режим уведомлений: {mode_label}",
                parse_mode="HTML",
                reply_markup=get_return_keyboard()
            )

        await callback.answer(f"✅ Режим изменен на: {mode_label}")
    else:
        await callback.answer("❌ Ошибка обновления настроек", show_alert=True)