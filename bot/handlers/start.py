from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from states.user_states import OnboardingStates
from keyboards.onboarding_kb import (
    get_level_keyboard,
    get_stack_keyboard,
    get_work_format_keyboard,
    get_employment_type_keyboard,
    get_currency_keyboard,
    get_notification_mode_keyboard,
    get_skip_keyboard,
    get_main_menu_keyboard
)
from services.api_client import api
import logging

logger = logging.getLogger(__name__)
router = Router()


# ============= START COMMAND =============

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start - начало онбординга"""
    telegram_id = message.from_user.id
    username = message.from_user.username or f"user_{telegram_id}"

    # Проверяем, существует ли пользователь
    user = await api.get_user(telegram_id)

    if user and user.get('is_profile_completed'):
        # Пользователь уже прошел онбординг
        await message.answer(
            f"С возвращением, {username}! 👋\n\n"
            f"Ваш профиль уже настроен.\n"
            f"Используйте меню ниже для навигации.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        return

    # Начинаем онбординг
    await message.answer(
        f"👋 Привет, {username}!\n\n"
        f"Я помогу тебе настроить профиль для поиска работы.\n"
        f"Это займет всего 2-3 минуты.\n\n"
        f"Давай начнем! 🚀"
    )

    await message.answer(
        "📝 Какая у тебя роль?\n\n"
        "Например: Backend Developer, Frontend Developer, DevOps Engineer"
    )

    await state.set_state(OnboardingStates.waiting_for_role)

    # Сохраняем базовую инфу в состояние
    await state.update_data(
        telegram_id=telegram_id,
        username=username
    )


# ============= ROLE =============

@router.message(OnboardingStates.waiting_for_role)
async def process_role(message: Message, state: FSMContext):
    """Обработка роли пользователя"""
    role = message.text.strip()

    if len(role) < 3:
        await message.answer("⚠️ Роль слишком короткая. Попробуй еще раз:")
        return

    await state.update_data(role=role)

    await message.answer(
        f"Отлично! {role} 👨‍💻\n\n"
        f"Какой у тебя уровень?",
        reply_markup=get_level_keyboard()
    )

    await state.set_state(OnboardingStates.waiting_for_level)


# ============= LEVEL =============

@router.message(OnboardingStates.waiting_for_level)
async def process_level(message: Message, state: FSMContext):
    """Обработка уровня"""
    level_map = {
        "Junior": "junior",
        "Middle": "middle",
        "Senior": "senior",
        "Lead": "lead"
    }

    level = level_map.get(message.text)

    if not level:
        await message.answer("⚠️ Выбери уровень из кнопок ниже:")
        return

    await state.update_data(level=level)

    # Получаем стеки из API
    stacks = await api.get_stacks()

    if not stacks:
        await message.answer("❌ Ошибка загрузки технологий. Попробуй позже.")
        return

    await state.update_data(available_stacks=stacks, selected_stack_ids=[])

    await message.answer(
        "🛠 Выбери технологии, которые ты знаешь:\n\n"
        "(Можно выбрать до 7 технологий)",
        reply_markup=get_stack_keyboard(stacks, [])
    )

    await state.set_state(OnboardingStates.waiting_for_stack)


# ============= STACK SELECTION =============

@router.callback_query(OnboardingStates.waiting_for_stack, F.data.startswith("stack_"))
async def process_stack_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора технологий"""
    data = await state.get_data()
    selected = data.get('selected_stack_ids', [])
    stacks = data.get('available_stacks', [])

    if callback.data == "stack_done":
        if not selected:
            await callback.answer("⚠️ Выбери хотя бы одну технологию", show_alert=True)
            return

        await callback.message.edit_text(
            f"✅ Выбрано технологий: {len(selected)}"
        )

        await state.update_data(stack_ids=selected)

        # Переход к формату работы
        work_formats = await api.get_work_formats()

        if not work_formats:
            await callback.message.answer("❌ Ошибка загрузки форматов работы.")
            return

        await state.update_data(available_work_formats=work_formats, selected_work_format_ids=[])

        await callback.message.answer(
            "🏢 Какой формат работы тебе подходит?",
            reply_markup=get_work_format_keyboard(work_formats, [])
        )

        await state.set_state(OnboardingStates.waiting_for_work_format)
        await callback.answer()
        return

    # Toggle выбранной технологии
    stack_id = int(callback.data.split("_")[1])

    if stack_id in selected:
        selected.remove(stack_id)
    else:
        if len(selected) >= 7:
            await callback.answer("⚠️ Максимум 7 технологий", show_alert=True)
            return
        selected.append(stack_id)

    await state.update_data(selected_stack_ids=selected)

    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=get_stack_keyboard(stacks, selected)
    )

    await callback.answer()


# ============= WORK FORMAT =============

@router.callback_query(OnboardingStates.waiting_for_work_format, F.data.startswith("workformat_"))
async def process_work_format(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора формата работы"""
    data = await state.get_data()
    selected = data.get('selected_work_format_ids', [])
    formats = data.get('available_work_formats', [])

    if callback.data == "workformat_done":
        if not selected:
            await callback.answer("⚠️ Выбери хотя бы один формат", show_alert=True)
            return

        await callback.message.edit_text("✅ Формат работы сохранен")
        await state.update_data(work_format_ids=selected)

        # Переход к типу занятости
        employment_types = await api.get_employment_types()

        if not employment_types:
            await callback.message.answer("❌ Ошибка загрузки типов занятости.")
            return

        await state.update_data(available_employment_types=employment_types, selected_employment_ids=[])

        await callback.message.answer(
            "📋 Какой тип занятости тебя интересует?",
            reply_markup=get_employment_type_keyboard(employment_types, [])
        )

        await state.set_state(OnboardingStates.waiting_for_employment_type)
        await callback.answer()
        return

    # Toggle формата
    fmt_id = int(callback.data.split("_")[1])

    if fmt_id in selected:
        selected.remove(fmt_id)
    else:
        selected.append(fmt_id)

    await state.update_data(selected_work_format_ids=selected)

    await callback.message.edit_reply_markup(
        reply_markup=get_work_format_keyboard(formats, selected)
    )

    await callback.answer()


# ============= EMPLOYMENT TYPE =============

@router.callback_query(OnboardingStates.waiting_for_employment_type, F.data.startswith("employment_"))
async def process_employment_type(callback: CallbackQuery, state: FSMContext):
    """Обработка типа занятости"""
    data = await state.get_data()
    selected = data.get('selected_employment_ids', [])
    types = data.get('available_employment_types', [])

    if callback.data == "employment_done":
        if not selected:
            await callback.answer("⚠️ Выбери хотя бы один тип", show_alert=True)
            return

        await callback.message.edit_text("✅ Тип занятости сохранен")
        await state.update_data(employment_type_ids=selected)

        await callback.message.answer(
            "🌍 В каком городе/стране ты ищешь работу?\n\n"
            "Например: Moscow, Remote, Saint Petersburg",
            reply_markup=get_skip_keyboard()
        )

        await state.set_state(OnboardingStates.waiting_for_location)
        await callback.answer()
        return

    # Toggle типа
    type_id = int(callback.data.split("_")[1])

    if type_id in selected:
        selected.remove(type_id)
    else:
        selected.append(type_id)

    await state.update_data(selected_employment_ids=selected)

    await callback.message.edit_reply_markup(
        reply_markup=get_employment_type_keyboard(types, selected)
    )

    await callback.answer()


# ============= LOCATION =============

@router.message(OnboardingStates.waiting_for_location)
async def process_location(message: Message, state: FSMContext):
    """Обработка локации"""
    if message.text == "⏭ Пропустить":
        location = None
    else:
        location = message.text.strip()

    await state.update_data(location=location)

    await message.answer(
        "💰 Какая минимальная зарплата тебе нужна?\n\n"
        "Введи число (например: 3000) или нажми Пропустить:",
        reply_markup=get_skip_keyboard()
    )

    await state.set_state(OnboardingStates.waiting_for_salary)


# ============= SALARY =============

@router.message(OnboardingStates.waiting_for_salary)
async def process_salary(message: Message, state: FSMContext):
    """Обработка зарплаты"""
    if message.text == "⏭ Пропустить":
        salary = None
    else:
        try:
            salary = int(message.text.strip())
            if salary < 0:
                await message.answer("⚠️ Зарплата не может быть отрицательной. Попробуй еще раз:")
                return
        except ValueError:
            await message.answer("⚠️ Введи число или нажми Пропустить:")
            return

    await state.update_data(salary_from=salary)

    if salary:
        await message.answer(
            "💵 В какой валюте?",
            reply_markup=get_currency_keyboard()
        )
        await state.set_state(OnboardingStates.waiting_for_currency)
    else:
        # Пропускаем валюту, переходим к уведомлениям
        await message.answer(
            "🔔 Как часто ты хочешь получать уведомления о вакансиях?",
            reply_markup=get_notification_mode_keyboard()
        )
        await state.set_state(OnboardingStates.waiting_for_notification_mode)


# ============= CURRENCY =============

@router.message(OnboardingStates.waiting_for_currency)
async def process_currency(message: Message, state: FSMContext):
    """Обработка валюты"""
    currency_map = {
        "USD 💵": "USD",
        "EUR 💶": "EUR",
        "RUB ₽": "RUB",
        "KZT ₸": "KZT"
    }

    currency = currency_map.get(message.text, "USD")
    await state.update_data(currency=currency)

    await message.answer(
        "🔔 Как часто ты хочешь получать уведомления о вакансиях?",
        reply_markup=get_notification_mode_keyboard()
    )

    await state.set_state(OnboardingStates.waiting_for_notification_mode)


@router.message(OnboardingStates.waiting_for_notification_mode)
async def process_notification_mode(message: Message, state: FSMContext):
    mode_map = {
        "Сразу 🔔": "instant",
        "Ежедневно 📅": "daily",
        "Еженедельно 📆": "weekly"
    }

    notify_mode = mode_map.get(message.text, "daily")
    await state.update_data(notify_mode=notify_mode)

    data = await state.get_data()

    user_data = {
        "telegram_id": data['telegram_id'],
        "username": data['username'],
        "role": data['role'],
        "level": data['level'],
        "stack_ids": data.get('stack_ids', []),
        "work_format_ids": data.get('work_format_ids', []),
        "employment_type_ids": data.get('employment_type_ids', []),
        "location": data.get('location'),
        "salary_from": data.get('salary_from'),
        "currency": data.get('currency', 'USD'),
        "notify_mode": notify_mode
    }

    await message.answer("⏳ Сохраняю твой профиль...")

    result = await api.create_user(user_data)

    if result:
        await api.complete_onboarding(data['telegram_id'])

        await message.answer(
            "✅ Отлично! Твой профиль создан! 🎉\n\n"
            f"📋 Роль: {data['role']}\n"
            f"🎯 Уровень: {data['level']}\n"
            f"🛠 Технологий: {len(data.get('stack_ids', []))}\n"
            f"🔔 Уведомления: {message.text}\n\n"
            "Теперь ты будешь получать подходящие вакансии!",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await message.answer(
            "❌ Произошла ошибка при сохранении профиля.\n"
            "Попробуй позже или обратись в поддержку."
        )

    await state.clear()