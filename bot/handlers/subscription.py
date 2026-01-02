from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from services.api_client import api
from keyboards.onboarding_kb import get_main_menu_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

logo = "AgACAgIAAxkBAANdaVaQDKbUzpyPbrB9DbKWbkck63YAAscNaxvqqrlKq_AlEQiE2TUBAAMCAAN5AAM4BA"


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = callback.from_user.id

    required_channels = await api.get_required_channels()

    if not required_channels:
        await callback.answer("✅ Нет обязательных каналов", show_alert=True)
        return

    not_subscribed = []

    for channel in required_channels:
        try:
            member = await bot.get_chat_member(
                chat_id=channel['channel_id'],
                user_id=user_id
            )

            if member.status in ['left', 'kicked']:
                not_subscribed.append(channel)

        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            not_subscribed.append(channel)

    if not_subscribed:
        channel_names = ", ".join([ch['title'] for ch in not_subscribed])
        await callback.answer(
            f"❌ Вы ещё не подписаны на: {channel_names}",
            show_alert=True
        )
        return

    await callback.answer("✅ Подписка подтверждена!", show_alert=False)
    user = await api.get_user(user_id)

    if user and user.get('is_profile_completed'):
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=logo,
            caption=(
                "✅ <b>Доступ разрешён!</b>\n\n"
                "Добро пожаловать в JobPulse 🚀\n"
                "Используй меню ниже для навигации"
            ),
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
            "✅ <b>Подписка подтверждена!</b>\n\n"
            "Теперь давай настроим твой профиль 🚀\n\n"
            "Нажми /start чтобы начать",
            parse_mode="HTML"
        )