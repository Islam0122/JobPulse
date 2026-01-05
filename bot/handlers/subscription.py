from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from services.api_client import api
from keyboards.onboarding_kb import get_main_menu_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

logo = "AgACAgIAAxkBAAICS2lb4BQM-xj2JkiR0jz7BfJDHv6RAAKAEWsbTSzYSl2zO5BmDzyyAQADAgADeQADOAQ"


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, bot: Bot):
    """
    Проверка подписки пользователя на обязательные каналы

    Вызывается когда пользователь нажимает "Проверить подписку"
    """
    user_id = callback.from_user.id

    # Получаем список обязательных каналов
    required_channels = await api.get_required_channels()

    if not required_channels:
        await callback.answer(
            "✅ Нет обязательных каналов",
            show_alert=True
        )
        return

    # Проверяем подписку на каждый канал
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
            logger.error(f"Ошибка проверки подписки: {e}")
            not_subscribed.append(channel)

    # Если все еще есть неподписанные каналы
    if not_subscribed:
        channel_names = ", ".join([ch['title'] for ch in not_subscribed])
        await callback.answer(
            f"❌ Подпишитесь на: {channel_names}",
            show_alert=True
        )
        return

    # Подписка подтверждена!
    await callback.answer("✅ Подписка подтверждена!", show_alert=False)

    # Получаем профиль пользователя
    user = await api.get_user(user_id)

    # Удаляем старое сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Отправляем приветствие
    if user and user.get('is_profile_completed'):
        # Если профиль уже заполнен - показываем меню
        await callback.message.answer_photo(
            photo=logo,
            caption=(
                "✅ <b>Добро пожаловать в JobPulse!</b> 🚀\n\n"
                "Твой профиль уже настроен.\n"
                "Используй меню ниже для навигации 👇"
            ),
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        # Если профиль не заполнен - предлагаем начать
        await callback.message.answer(
            "✅ <b>Подписка подтверждена!</b>\n\n"
            "Теперь давай настроим твой профиль 🚀\n\n"
            "Нажми /start чтобы начать",
            parse_mode="HTML"
        )