from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.api_client import api
from keyboards.onboarding_kb import *
import html

router = Router()

logo = "AgACAgIAAxkBAAICS2lb4BQM-xj2JkiR0jz7BfJDHv6RAAKAEWsbTSzYSl2zO5BmDzyyAQADAgADeQADOAQ"


class EditStates(StatesGroup):
    """Состояния для редактирования профиля"""
    waiting_for_role = State()
    waiting_for_level = State()
    waiting_for_stack = State()
    waiting_for_work_format = State()
    waiting_for_employment = State()
    waiting_for_location = State()
    waiting_for_salary = State()
    waiting_for_currency = State()


@router.callback_query(F.data == "edit:full")
async def start_full_edit(callback: CallbackQuery):
    """Начать полное редактирование профиля"""
    text = (
        "✏️ <b>Редактирование профиля</b>\n\n"
        "Выбери, что хочешь изменить:"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="👔 Роль", callback_data="edit:role")
    builder.button(text="🎯 Уровень", callback_data="edit:level")
    builder.button(text="🛠 Технологии", callback_data="edit:stack")
    builder.button(text="🏢 Формат работы", callback_data="edit:work_format")
    builder.button(text="📋 Тип занятости", callback_data="edit:employment")
    builder.button(text="🌍 Локация", callback_data="edit:location")
    builder.button(text="💰 Зарплата", callback_data="edit:salary")
    builder.button(text="⬅️ Назад", callback_data="menu:profile")
    builder.adjust(2)

    await callback.message.edit_caption(
        caption=text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "edit:role")
async def edit_role_start(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование роли"""
    user = await api.get_user(callback.from_user.id)

    text = (
        f"📝 <b>Текущая роль:</b> {html.escape(user['role'])}\n\n"
        f"Напиши новую роль:\n"
        f"<i>Например: Python Developer, QA Engineer</i>"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="edit:full")

    msg = await callback.message.edit_caption(
        caption=text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

    await state.set_state(EditStates.waiting_for_role)
    await state.update_data(message_id=msg.message_id)
    await callback.answer()


@router.message(EditStates.waiting_for_role)
async def edit_role_process(message: Message, state: FSMContext, bot: Bot):
    """Обработка новой роли"""
    role = message.text.strip()
    telegram_id = message.from_user.id

    if len(role) < 2:
        await message.answer("⚠️ Роль слишком короткая. Попробуй еще раз:")
        return

    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass

    # Обновляем в API
    result = await api.update_user(telegram_id, {"role": role})

    if result:
        text = f"✅ <b>Роль обновлена!</b>\n\nНовая роль: {html.escape(role)}"
    else:
        text = "❌ <b>Ошибка обновления</b>\n\nПопробуй позже."

    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить еще", callback_data="edit:full")
    builder.button(text="🏠 В меню", callback_data="menu:home")
    builder.adjust(1)

    # Получаем ID старого сообщения
    data = await state.get_data()
    message_id = data.get('message_id')

    try:
        await bot.edit_message_caption(
            chat_id=message.chat.id,
            message_id=message_id,
            caption=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except:
        await message.answer_photo(
            photo=logo,
            caption=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

    await state.clear()


@router.callback_query(F.data == "edit:level")
async def edit_level(callback: CallbackQuery, state: FSMContext):
    """Редактирование уровня"""
    user = await api.get_user(callback.from_user.id)

    text = (
        f"🎯 <b>Текущий уровень:</b> {user.get('level_label', 'Не указан')}\n\n"
        f"Выбери новый уровень:"
    )

    await callback.message.edit_caption(
        caption=text,
        reply_markup=get_level_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(EditStates.waiting_for_level)
    await callback.answer()


@router.callback_query(EditStates.waiting_for_level, F.data.startswith("level:"))
async def edit_level_process(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора уровня"""
    level = callback.data.split(":")[1]
    telegram_id = callback.from_user.id

    result = await api.update_user(telegram_id, {"level": level})

    if result:
        text = f"✅ <b>Уровень обновлен!</b>\n\nНовый уровень: {level.capitalize()}"
    else:
        text = "❌ <b>Ошибка обновления</b>"

    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить еще", callback_data="edit:full")
    builder.button(text="🏠 В меню", callback_data="menu:home")
    builder.adjust(1)

    await callback.message.edit_caption(
        caption=text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "edit:stack")
async def edit_stack_start(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование технологий"""
    user = await api.get_user(callback.from_user.id)
    stacks = await api.get_stacks()

    current_stack_ids = [s['id'] for s in user.get('stack', [])]

    await state.set_state(EditStates.waiting_for_stack)
    await state.update_data(
        available_stacks=stacks,
        selected_stack_ids=current_stack_ids
    )

    current_names = ", ".join([s['name'] for s in user.get('stack', [])])
    text = (
        f"🛠 <b>Текущие технологии:</b>\n{current_names or 'Не указаны'}\n\n"
        f"Выбери новые технологии:"
    )

    await callback.message.edit_caption(
        caption=text,
        reply_markup=get_stack_keyboard(stacks, current_stack_ids),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(EditStates.waiting_for_stack, F.data.startswith("stack:"))
async def edit_stack_process(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора технологий"""
    data = await state.get_data()
    selected = data.get('selected_stack_ids', [])
    stacks = data.get('available_stacks', [])

    action = callback.data.split(":")[1]

    if action == "done":
        if not selected:
            await callback.answer("⚠️ Выбери хотя бы одну технологию", show_alert=True)
            return

        telegram_id = callback.from_user.id
        result = await api.update_user(telegram_id, {"stack_ids": selected})

        if result:
            selected_names = [s['name'] for s in stacks if s['id'] in selected]
            text = f"✅ <b>Технологии обновлены!</b>\n\n{', '.join(selected_names)}"
        else:
            text = "❌ <b>Ошибка обновления</b>"

        builder = InlineKeyboardBuilder()
        builder.button(text="✏️ Изменить еще", callback_data="edit:full")
        builder.button(text="🏠 В меню", callback_data="menu:home")
        builder.adjust(1)

        await callback.message.edit_caption(
            caption=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await state.clear()
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

        text = f"🛠 Выбрано технологий: {len(selected)}\n\nПродолжай выбор:"

        await callback.message.edit_caption(
            caption=text,
            reply_markup=get_stack_keyboard(stacks, selected),
            parse_mode="HTML"
        )

    await callback.answer()


@router.callback_query(F.data == "edit:location")
async def edit_location_start(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование локации"""
    user = await api.get_user(callback.from_user.id)

    current_location = user.get('location', 'Не указана')

    text = (
        f"🌍 <b>Текущая локация:</b> {html.escape(current_location)}\n\n"
        f"Напиши новую локацию:\n"
        f"<i>Например: Moscow, Remote, Berlin</i>"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="edit:full")

    msg = await callback.message.edit_caption(
        caption=text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

    await state.set_state(EditStates.waiting_for_location)
    await state.update_data(message_id=msg.message_id)
    await callback.answer()


@router.message(EditStates.waiting_for_location)
async def edit_location_process(message: Message, state: FSMContext, bot: Bot):
    """Обработка новой локации"""
    location = message.text.strip()
    telegram_id = message.from_user.id

    try:
        await message.delete()
    except:
        pass

    result = await api.update_user(telegram_id, {"location": location})

    if result:
        text = f"✅ <b>Локация обновлена!</b>\n\nНовая локация: {html.escape(location)}"
    else:
        text = "❌ <b>Ошибка обновления</b>"

    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить еще", callback_data="edit:full")
    builder.button(text="🏠 В меню", callback_data="menu:home")
    builder.adjust(1)

    data = await state.get_data()
    message_id = data.get('message_id')

    try:
        await bot.edit_message_caption(
            chat_id=message.chat.id,
            message_id=message_id,
            caption=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except:
        await message.answer_photo(
            photo=logo,
            caption=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

    await state.clear()


@router.callback_query(F.data == "edit:salary")
async def edit_salary_start(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование зарплаты"""
    user = await api.get_user(callback.from_user.id)

    current_salary = user.get('salary_from', 'Не указана')
    currency = user.get('currency', 'USD')

    text = (
        f"💰 <b>Текущая зарплата:</b> {current_salary} {currency}\n\n"
        f"Напиши новую минимальную зарплату:\n"
        f"<i>Например: 3000</i>"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="edit:full")

    msg = await callback.message.edit_caption(
        caption=text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

    await state.set_state(EditStates.waiting_for_salary)
    await state.update_data(message_id=msg.message_id)
    await callback.answer()


@router.message(EditStates.waiting_for_salary)
async def edit_salary_amount(message: Message, state: FSMContext):
    """Обработка суммы зарплаты"""
    try:
        salary = int(message.text.strip())
        if salary < 0:
            await message.answer("⚠️ Зарплата не может быть отрицательной")
            return

        await state.update_data(salary_from=salary)

        try:
            await message.delete()
        except:
            pass

        # Переходим к выбору валюты
        text = f"💵 Выбери валюту:\n\n💰 Сумма: {salary}"

        data = await state.get_data()
        message_id = data.get('message_id')

        try:
            await message.bot.edit_message_caption(
                chat_id=message.chat.id,
                message_id=message_id,
                caption=text,
                reply_markup=get_currency_keyboard(),
                parse_mode="HTML"
            )
        except:
            pass

        await state.set_state(EditStates.waiting_for_currency)

    except ValueError:
        await message.answer("⚠️ Введи число. Например: 3000")


@router.callback_query(EditStates.waiting_for_currency, F.data.startswith("currency:"))
async def edit_salary_currency(callback: CallbackQuery, state: FSMContext):
    """Обработка валюты"""
    currency = callback.data.split(":")[1]
    data = await state.get_data()
    salary = data.get('salary_from')
    telegram_id = callback.from_user.id

    result = await api.update_user(
        telegram_id,
        {"salary_from": salary, "currency": currency}
    )

    if result:
        text = f"✅ <b>Зарплата обновлена!</b>\n\nНовая зарплата: от {salary} {currency}"
    else:
        text = "❌ <b>Ошибка обновления</b>"

    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить еще", callback_data="edit:full")
    builder.button(text="🏠 В меню", callback_data="menu:home")
    builder.adjust(1)

    await callback.message.edit_caption(
        caption=text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.clear()
    await callback.answer()