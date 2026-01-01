from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from services.api_client import api
from keyboards.onboarding_kb import get_main_menu_keyboard

router = Router()


@router.message(F.text == "📊 Мой профиль")
async def show_profile(message: Message):
    """Показать профиль пользователя"""
    telegram_id = message.from_user.id

    user = await api.get_user(telegram_id)

    if not user:
        await message.answer(
            "❌ Профиль не найден.\n"
            "Используй /start для регистрации."
        )
        return

    # Форматируем стек
    stack_names = [s['name'] for s in user.get('stack', [])]
    stack_text = ", ".join(stack_names) if stack_names else "Не указано"

    # Форматируем форматы работы
    work_formats = [w['title'] for w in user.get('work_formats', [])]
    work_format_text = ", ".join(work_formats) if work_formats else "Не указано"

    # Форматируем типы занятости
    employment = [e['title'] for e in user.get('employment_types', [])]
    employment_text = ", ".join(employment) if employment else "Не указано"

    # Зарплата
    salary_text = f"{user.get('salary_from', 0)} {user.get('currency', 'USD')}" if user.get(
        'salary_from') else "Не указано"

    profile_text = f"""
👤 <b>Твой профиль</b>

📝 <b>Роль:</b> {user.get('role', 'Не указано')}
🎯 <b>Уровень:</b> {user.get('level_label', 'Не указано')}
🛠 <b>Стек:</b> {stack_text}

🏢 <b>Формат работы:</b> {work_format_text}
📋 <b>Занятость:</b> {employment_text}
🌍 <b>Локация:</b> {user.get('location', 'Не указано')}
💰 <b>Зарплата от:</b> {salary_text}

🔔 <b>Уведомления:</b> {user.get('notify_mode_label', 'Не указано')}
✅ <b>Статус:</b> {'Активен' if user.get('is_active') else 'Неактивен'}

📅 <b>Создан:</b> {user.get('created_at', '')[:10]}
"""

    await message.answer(
        profile_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(F.text == "🔔 Настройки уведомлений")
async def notification_settings(message: Message):
    telegram_id = message.from_user.id
    user = await api.get_user(telegram_id)

    if not user:
        await message.answer("❌ Профиль не найден.")
        return

    from keyboards.onboarding_kb import get_notification_mode_keyboard

    await message.answer(
        f"🔔 <b>Текущий режим:</b> {user.get('notify_mode_label')}\n\n"
        f"Выбери новый режим:",
        parse_mode="HTML",
        reply_markup=get_notification_mode_keyboard()
    )


@router.message(F.text.in_(["Сразу 🔔", "Ежедневно 📅", "Еженедельно 📆"]))
async def update_notifications(message: Message):
    mode_map = {
        "Сразу 🔔": "instant",
        "Ежедневно 📅": "daily",
        "Еженедельно 📆": "weekly"
    }

    notify_mode = mode_map.get(message.text)
    telegram_id = message.from_user.id

    result = await api.update_notification_mode(telegram_id, notify_mode)

    if result:
        await message.answer(
            f"✅ Режим уведомлений изменен на: {message.text}",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await message.answer("❌ Ошибка обновления настроек.")


@router.message(F.text == "✏️ Редактировать профиль")
async def edit_profile(message: Message):
    await message.answer(
        "✏️ <b>Редактирование профиля</b>\n\n"
        "Чтобы изменить профиль, используй /start заново.\n"
        "Твои текущие данные будут обновлены.",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(F.text == "❓ Помощь")
async def help_command(message: Message):
    help_text = """
❓ <b>Помощь</b>

<b>Доступные команды:</b>
/start - Настроить/обновить профиль
/profile - Показать профиль
/help - Эта справка

<b>Кнопки меню:</b>
📊 Мой профиль - Просмотр твоих данных
🔔 Настройки уведомлений - Изменить частоту
✏️ Редактировать профиль - Обновить данные
❓ Помощь - Эта справка

<b>Как работает бот:</b>
1. Ты заполняешь профиль
2. Бот находит подходящие вакансии
3. Ты получаешь уведомления по расписанию

<b>Поддержка:</b> @support_username
"""

    await message.answer(
        help_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )