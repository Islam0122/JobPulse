from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.api_client import api
import logging

logger = logging.getLogger(__name__)


class SubscriptionMiddleware(BaseMiddleware):
    WHITELIST_COMMANDS = ['/start', '/help']
    WHITELIST_CALLBACKS = ['check_subscription', 'ask_role']

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            user_id = event.from_user.id
            chat_id = event.chat.id

            if event.text and any(event.text.startswith(cmd) for cmd in self.WHITELIST_COMMANDS):
                return await handler(event, data)

        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            chat_id = event.message.chat.id

            if event.data in self.WHITELIST_CALLBACKS:
                return await handler(event, data)
        else:
            return await handler(event, data)

        bot = data['bot']
        required_channels = await api.get_required_channels()

        if not required_channels:
            return await handler(event, data)

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
                logger.error(f"Error checking subscription for channel {channel['channel_id']}: {e}")
                not_subscribed.append(channel)

        if not_subscribed:
            await self._send_subscription_required(
                event=event,
                channels=not_subscribed
            )
            return

        return await handler(event, data)

    async def _send_subscription_required(
            self,
            event: Message | CallbackQuery,
            channels: list
    ):
        text = "🔒 <b>Доступ ограничен</b>\n\n"
        text += "Для использования бота необходимо подписаться на:\n\n"

        for i, channel in enumerate(channels, 1):
            username = channel.get('username', '').replace('@', '')
            if username:
                text += f"{i}. <a href='https://t.me/{username}'>{channel['title']}</a>\n"
            else:
                text += f"{i}. {channel['title']}\n"

        text += "\n👇 Подпишитесь и нажмите кнопку ниже"

        builder = InlineKeyboardBuilder()

        for channel in channels:
            username = channel.get('username', '').replace('@', '')
            if username:
                builder.button(
                    text=f"📢 {channel['title']}",
                    url=f"https://t.me/{username}"
                )

        builder.button(
            text="✅ Проверить подписку",
            callback_data="check_subscription"
        )

        builder.adjust(1)

        if isinstance(event, Message):
            await event.answer(
                text=text,
                parse_mode="HTML",
                reply_markup=builder.as_markup(),
                disable_web_page_preview=True
            )
        elif isinstance(event, CallbackQuery):
            try:
                await event.message.edit_text(
                    text=text,
                    parse_mode="HTML",
                    reply_markup=builder.as_markup(),
                    disable_web_page_preview=True
                )
            except:
                await event.message.answer(
                    text=text,
                    parse_mode="HTML",
                    reply_markup=builder.as_markup(),
                    disable_web_page_preview=True
                )

            await event.answer(
                "⚠️ Подпишитесь на канал",
                show_alert=False
            )