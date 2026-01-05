from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from states.user_states import OnboardingStates
from services.api_client import api
import logging
import html
from keyboards.onboarding_kb import *

logo = "AgACAgIAAxkBAAICS2lb4BQM-xj2JkiR0jz7BfJDHv6RAAKAEWsbTSzYSl2zO5BmDzyyAQADAgADeQADOAQ"
logger = logging.getLogger(__name__)
router = Router()
last_message_id = 0


async def send_or_edit_message(
        target: Message | CallbackQuery,
        text: str,
        reply_markup=None,
        photo: str = None
) -> Message:
    if isinstance(target, CallbackQuery):
        if photo and target.message.photo:
            await target.message.edit_caption(
                caption=text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            return target.message
        elif photo and not target.message.photo:
            message = await target.message.answer_photo(
                photo=photo,
                caption=text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            await target.message.delete()
            return message
        else:
            await target.message.edit_caption(
                caption=text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            return target.message
    else:
        try:
            await target.delete()
        except:
            pass

        if photo:
            return await target.answer_photo(
                photo=photo,
                caption=text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            return await target.answer_photo(
                photo=logo,
                caption=text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )



@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    username = message.from_user.username or f"user_{telegram_id}"

    user = await api.get_user(telegram_id)

    if user and user.get('is_profile_completed'):
        await send_or_edit_message(
            message,
            f"👋 Привет, {html.escape(username)}!\n\n"
            f"Твой профиль уже настроен.\n"
            f"Используй меню ниже для навигации 👇",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        return

    # Профиль не заполнен - начинаем онбординг
    await state.set_state(OnboardingStates.waiting_for_role)
    await state.update_data(
        telegram_id=telegram_id,
        username=username,
        current_message=None
    )
    await ask_role(message, state)


async def ask_role(target: Message | CallbackQuery, state: FSMContext):
    text = (
        "👋 <b>Привет!</b>\n\n"
        "Я помогу тебе настроить профиль для поиска работы.\n"
        "Это займет всего 2-3 минуты.\n\n"
        "Давай начнем! 🚀"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Начать настройку", callback_data="ask_role")

    message = await send_or_edit_message(
        target,
        text,
        reply_markup=builder.as_markup(),
    )
    await state.update_data(current_message_id=message.message_id)


@router.callback_query(F.data == "ask_role")
async def start_role_input(callback: CallbackQuery, state: FSMContext):
    msg = await send_or_edit_message(
        callback,
        "📝 Напиши свою желаемую должность:\n\n"
        "<i>Например: Python Developer, UX Designer, Project Manager</i>"
    )
    await state.update_data(current_message_id=msg.message_id)
    await state.set_state(OnboardingStates.waiting_for_role)
    await callback.answer()


@router.message(OnboardingStates.waiting_for_role)
async def process_role(message: Message, state: FSMContext, bot: Bot):
    role = message.text.strip()

    if len(role) < 2:
        await message.answer("⚠️ Роль слишком короткая. Попробуй еще раз:")
        return

    try:
        await message.delete()
    except:
        pass

    data = await state.get_data()
    if data.get('current_message_id'):
        try:
            await bot.delete_message(message.chat.id, data['current_message_id'])
        except:
            pass

    await state.update_data(role=role)
    await ask_level(message, state)


async def ask_level(target: Message | CallbackQuery, state: FSMContext):
    data = await state.get_data()
    role = data.get('role', '')
    text = f"🎯 {html.escape(role)}\n\nКакой у тебя уровень?"

    await send_or_edit_message(
        target,
        text,
        reply_markup=get_level_keyboard()
    )
    await state.set_state(OnboardingStates.waiting_for_level)


@router.callback_query(OnboardingStates.waiting_for_level, F.data.startswith("level:"))
async def process_level(callback: CallbackQuery, state: FSMContext):
    level = callback.data.split(":")[1]
    await state.update_data(level=level)

    stacks = await api.get_stacks()

    if not stacks:
        await callback.answer("❌ Ошибка загрузки технологий", show_alert=True)
        return

    await state.update_data(
        available_stacks=stacks,
        selected_stack_ids=[]
    )

    await ask_stacks(callback, state)
    await callback.answer()


async def ask_stacks(target: Message | CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get('selected_stack_ids', [])
    stacks = data.get('available_stacks', [])
    text = "🛠 Выбери технологии, которые ты знаешь:\n\n"

    if selected:
        selected_names = [s['name'] for s in stacks if s['id'] in selected]
        text += f"✅ Выбрано ({len(selected)}): {', '.join(selected_names[:3])}"
        if len(selected) > 3:
            text += f"..."
    else:
        text += "Выбери технологии (можно несколько)"

    await send_or_edit_message(
        target,
        text,
        reply_markup=get_stack_keyboard(stacks, selected)
    )
    await state.set_state(OnboardingStates.waiting_for_stack)


@router.callback_query(OnboardingStates.waiting_for_stack, F.data.startswith("stack:"))
async def process_stack_selection(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get('selected_stack_ids', [])
    stacks = data.get('available_stacks', [])

    action = callback.data.split(":")[1]

    if action == "done":
        if not selected:
            await callback.answer("⚠️ Выбери хотя бы одну технологию", show_alert=True)
            return

        await state.update_data(stack_ids=selected)

        # Переход к формату работы
        work_formats = await api.get_work_formats()

        if not work_formats:
            await callback.answer("❌ Ошибка загрузки форматов работы", show_alert=True)
            return

        await state.update_data(
            available_work_formats=work_formats,
            selected_work_format_ids=[]
        )

        await ask_work_formats(callback, state)
    else:
        stack_id = int(action)

        if stack_id in selected:
            selected.remove(stack_id)
        else:
            if len(selected) >= 7:
                await callback.answer("⚠️ Максимум 7 технологий", show_alert=True)
                return
            selected.append(stack_id)

        await state.update_data(selected_stack_ids=selected)

        await ask_stacks(callback, state)

    await callback.answer()


async def ask_work_formats(target: Message | CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get('selected_work_format_ids', [])
    formats = data.get('available_work_formats', [])

    text = "🏢 Какой формат работы тебе подходит?"

    if selected:
        selected_names = [f['title'] for f in formats if f['id'] in selected]
        text += f"\n\n✅ Выбрано: {', '.join(selected_names)}"

    await send_or_edit_message(
        target,
        text,
        reply_markup=get_work_format_keyboard(formats, selected)
    )
    await state.set_state(OnboardingStates.waiting_for_work_format)


@router.callback_query(OnboardingStates.waiting_for_work_format, F.data.startswith("workformat:"))
async def process_work_format(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get('selected_work_format_ids', [])
    formats = data.get('available_work_formats', [])

    action = callback.data.split(":")[1]

    if action == "done":
        if not selected:
            await callback.answer("⚠️ Выбери хотя бы один формат", show_alert=True)
            return

        await state.update_data(work_format_ids=selected)

        # Переход к типу занятости
        employment_types = await api.get_employment_types()

        if not employment_types:
            await callback.answer("❌ Ошибка загрузки типов занятости", show_alert=True)
            return

        await state.update_data(
            available_employment_types=employment_types,
            selected_employment_ids=[]
        )

        await ask_employment_types(callback, state)
    else:
        fmt_id = int(action)

        if fmt_id in selected:
            selected.remove(fmt_id)
        else:
            selected.append(fmt_id)

        await state.update_data(selected_work_format_ids=selected)
        await ask_work_formats(callback, state)

    await callback.answer()


async def ask_employment_types(target: Message | CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get('selected_employment_ids', [])
    types = data.get('available_employment_types', [])

    text = "📋 Какой тип занятости тебя интересует?"

    if selected:
        selected_names = [t['title'] for t in types if t['id'] in selected]
        text += f"\n\n✅ Выбрано: {', '.join(selected_names)}"

    await send_or_edit_message(
        target,
        text,
        reply_markup=get_employment_type_keyboard(types, selected)
    )
    await state.set_state(OnboardingStates.waiting_for_employment_type)


@router.callback_query(OnboardingStates.waiting_for_employment_type, F.data.startswith("employment:"))
async def process_employment_type(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get('selected_employment_ids', [])
    types = data.get('available_employment_types', [])

    action = callback.data.split(":")[1]

    if action == "done":
        if not selected:
            await callback.answer("⚠️ Выбери хотя бы один тип", show_alert=True)
            return

        await state.update_data(employment_type_ids=selected)

        await ask_location(callback, state)
    else:
        type_id = int(action)

        if type_id in selected:
            selected.remove(type_id)
        else:
            selected.append(type_id)

        await state.update_data(selected_employment_ids=selected)
        await ask_employment_types(callback, state)

    await callback.answer()


async def ask_location(target: Message | CallbackQuery, state: FSMContext):
    text = (
        "🌍 В каком городе/стране ты ищешь работу?\n\n"
        "Например:\n"
        "• Moscow\n"
        "• Remote\n"
        "• Saint Petersburg\n"
        "• Berlin, Germany"
    )

    msg = await send_or_edit_message(
        target,
        text,
        reply_markup=get_skip_keyboard()
    )
    await state.update_data(main_message_id=msg.message_id)
    await state.set_state(OnboardingStates.waiting_for_location)


@router.callback_query(OnboardingStates.waiting_for_location, F.data == "skip")
async def skip_location(callback: CallbackQuery, state: FSMContext,bot:Bot):
    await state.update_data(location=None)
    await ask_salary(callback, state,bot)
    await callback.answer()


@router.message(OnboardingStates.waiting_for_location)
async def process_location(message: Message, state: FSMContext,bot:Bot):
    location = message.text.strip()
    await state.update_data(location=location)
    await message.delete()

    await ask_salary(message, state,bot)


async def ask_salary(target: Message | CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    location = data.get('location')
    main_message_id = data.get("main_message_id")

    # Удаляем предыдущее главное сообщение
    if main_message_id and isinstance(target, Message):
        try:
            await bot.delete_message(target.chat.id, main_message_id)
        except:
            pass

    text = "💰 Какая минимальная зарплата тебе нужна?\n\n"

    if location:
        text += f"📍Локация: {html.escape(location)}\n\n"

    text += "Введи число (например: 3000) или пропусти:"

    msg = await send_or_edit_message(
        target,
        text,
        reply_markup=get_skip_keyboard()
    )
    await state.update_data(main_message_id=msg.message_id)
    await state.set_state(OnboardingStates.waiting_for_salary)


@router.callback_query(OnboardingStates.waiting_for_salary, F.data == "skip")
async def skip_salary(callback: CallbackQuery, state: FSMContext):
    await state.update_data(salary_from=None)
    await ask_notification_mode(callback, state)
    await callback.answer()


@router.message(OnboardingStates.waiting_for_salary)
async def process_salary(message: Message, state: FSMContext,bot:Bot):
    try:
        salary = int(message.text.strip())
        if salary < 0:
            await message.answer("⚠️ Зарплата не может быть отрицательной")
            return

        await state.update_data(salary_from=salary)
        await message.delete()  # Удаляем сообщение пользователя

        await ask_currency(message, state,bot)
    except ValueError:
        await message.answer("⚠️ Введи число или нажми Пропустить:")
        return


async def ask_currency(target: Message | CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    salary = data.get('salary_from')
    main_message_id = data.get("main_message_id")

    # Удаляем предыдущее сообщение если это Message
    if main_message_id and isinstance(target, Message):
        try:
            await bot.delete_message(target.chat.id, main_message_id)
        except:
            pass

    text = f"💵 В какой валюте?\n\n💰 Зарплата: {salary}"

    msg = await send_or_edit_message(
        target,
        text,
        reply_markup=get_currency_keyboard()
    )
    await state.update_data(main_message_id=msg.message_id)
    await state.set_state(OnboardingStates.waiting_for_currency)


@router.callback_query(OnboardingStates.waiting_for_currency, F.data.startswith("currency:"))
async def process_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split(":")[1]
    await state.update_data(currency=currency)
    await ask_notification_mode(callback, state)
    await callback.answer()


async def ask_notification_mode(target: Message | CallbackQuery, state: FSMContext):
    data = await state.get_data()
    salary = data.get('salary_from')
    currency = data.get('currency')

    text = "🔔 Как часто ты хочешь получать уведомления о вакансиях?"

    if salary and currency:
        text += f"\n\n💰 Ожидания: {salary} {currency}"

    await send_or_edit_message(
        target,
        text,
        reply_markup=get_notification_mode_keyboard()
    )
    await state.set_state(OnboardingStates.waiting_for_notification_mode)


@router.callback_query(OnboardingStates.waiting_for_notification_mode, F.data.startswith("notify:"))
async def process_notification_mode(callback: CallbackQuery, state: FSMContext):
    notify_mode = callback.data.split(":")[1]
    await state.update_data(notify_mode=notify_mode)
    await save_profile(callback, state)
    await callback.answer()


async def save_profile(target: Message | CallbackQuery, state: FSMContext):
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
        "notify_mode": data.get('notify_mode', 'daily')
    }

    await send_or_edit_message(
        target,
        "⏳ Сохраняю твой профиль..."
    )

    result = await api.create_user(user_data)

    if result:
        await api.complete_onboarding(data['telegram_id'])

        summary = "✅Отлично! Твой профиль создан! 🎉\n\n"
        summary += f"📋Роль: {html.escape(data['role'])}\n"
        summary += f"🎯Уровень: {data['level'].capitalize()}\n"
        summary += f"🛠Технологий: {len(data.get('stack_ids', []))}\n"

        if data.get('salary_from') and data.get('currency'):
            summary += f"💰Зарплата: {data['salary_from']} {data['currency']}\n"

        mode_text = {
            "instant": "Сразу 🔔",
            "daily": "Ежедневно 📅",
            "weekly": "Еженедельно 📆"
        }.get(data.get('notify_mode', 'daily'), "Ежедневно 📅")

        summary += f"🔔 Уведомления: {mode_text}\n\n"
        summary += "Теперь ты будешь получать подходящие вакансии!"

        await send_or_edit_message(
            target,
            summary,
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await send_or_edit_message(
            target,
            "❌ <b>Произошла ошибка при сохранении профиля.</b>\n\n"
            "Попробуй позже или обратись в поддержку.",
            reply_markup=get_main_menu_keyboard()
        )
    await state.clear()


@router.message(Command("cancel"))
@router.callback_query(F.data == "cancel")
async def cancel_onboarding(callback_or_message: CallbackQuery | Message, state: FSMContext):
    await state.clear()

    if isinstance(callback_or_message, CallbackQuery):
        target = callback_or_message
    else:
        target = callback_or_message

    await send_or_edit_message(
        target,
        "🚫 Онбординг отменен.\n\n"
        "Используй /start чтобы начать заново.",
        reply_markup=get_main_menu_keyboard()
    )