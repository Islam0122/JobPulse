from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.api_client import api
import logging

logger = logging.getLogger(__name__)


class SubscriptionMiddleware(BaseMiddleware):
    WHITELIST_CALLBACKS = ['check_subscription']

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        """
        Основной метод middleware

        Args:
            handler: Следующий обработчик в цепочке
            event: Событие (Message или CallbackQuery)
            data: Дополнительные данные
        """

        if isinstance(event, Message):
            user_id = event.from_user.id
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            chat_id = event.message.chat.id

            # Разрешаем callback проверки подписки
            if event.data in self.WHITELIST_CALLBACKS:
                return await handler(event, data)
        else:
            # Другие типы событий пропускаем
            return await handler(event, data)

        # Получаем бота из контекста
        bot = data['bot']

        # Получаем список обязательных каналов
        required_channels = await api.get_required_channels()

        # Если каналов нет - пропускаем проверку
        if not required_channels:
            return await handler(event, data)

        # Проверяем подписку на каждый канал
        not_subscribed = []
        for channel in required_channels:
            try:
                member = await bot.get_chat_member(
                    chat_id=channel['channel_id'],
                    user_id=user_id
                )
                # Статусы left и kicked означают что пользователь не подписан
                if member.status in ['left', 'kicked']:
                    not_subscribed.append(channel)
            except Exception as e:
                logger.error(
                    f"Ошибка проверки подписки на "
                    f"{channel['channel_id']}: {e}"
                )
                # В случае ошибки считаем что не подписан
                not_subscribed.append(channel)

        # Если есть неподписанные каналы - блокируем
        if not_subscribed:
            await self._send_subscription_required(event, not_subscribed)
            return  # Прерываем обработку

        # Все проверки пройдены - передаем дальше
        return await handler(event, data)

    async def _send_subscription_required(
            self,
            event: Message | CallbackQuery,
            channels: list
    ):
        """
        Отправляет сообщение о необходимости подписки

        Args:
            event: Событие от пользователя
            channels: Список каналов, на которые нужно подписаться
        """

        text = "🔒 <b>Доступ ограничен</b>\n\n"
        text += "Для использования бота необходимо подписаться на:\n\n"

        builder = InlineKeyboardBuilder()

        # Добавляем каналы в сообщение и кнопки
        for i, channel in enumerate(channels, 1):
            username = channel.get('username', '').replace('@', '')

            if username:
                # Если есть username - делаем ссылку
                text += (
                    f"{i}. <a href='https://t.me/{username}'>"
                    f"{channel['title']}</a>\n"
                )
                builder.button(
                    text=f"📢 {channel['title']}",
                    url=f"https://t.me/{username}"
                )
            else:
                # Если нет username - просто текст
                text += f"{i}. {channel['title']}\n"

        text += "\n👇 Подпишитесь и нажмите кнопку ниже"

        # Кнопка проверки подписки
        builder.button(
            text="✅ Проверить подписку",
            callback_data="check_subscription"
        )
        builder.adjust(1)

        # Отправляем/редактируем сообщение
        if isinstance(event, Message):
            try:
                await event.delete()
            except:
                pass

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
                await event.message.delete()
                await event.message.answer(
                    text=text,
                    parse_mode="HTML",
                    reply_markup=builder.as_markup(),
                    disable_web_page_preview=True
                )

            await event.answer(
                "⚠️ Необходима подписка",
                show_alert=False
            )