from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.api_client import api
from keyboards.onboarding_kb import *
from aiogram.filters import Command
import html

router = Router()

logo = "AgACAgIAAxkBAAICS2lb4BQM-xj2JkiR0jz7BfJDHv6RAAKAEWsbTSzYSl2zO5BmDzyyAQADAgADeQADOAQ"


@router.message(Command("comment"))
async def handle_comment(message: Message):
    text = message.text.removeprefix("/comment").strip()
    if not text:

        await message.answer_photo(
            photo=logo,
            caption="💬 *Хотите оставить комментарий?*\n\n"
            "Просто напишите его сразу после команды 👇\n\n"
            "`/comment Мне очень нравится ваш бот 👍`\n\n"
            "Это может быть:\n"
            "• отзыв\n"
            "• идея\n"
            "• сообщение о проблеме\n\n"
            "Мы читаем все комментарии 🙌",
            parse_mode="Markdown"
        )
        return

    if len(text) < 5:
        await message.answer(
            "✍️ Комментарий получился слишком коротким\n\n"
            "Попробуйте написать чуть подробнее 🙂\n"
            "Например:\n"
            "`/comment Было бы удобно добавить фильтр по зарплате`",
            parse_mode="Markdown"
        )
        return

    result = await api.send_comment(
        telegram_id=message.from_user.id,
        text=text
    )

    if result:
        await message.answer(
            "🙏 *Спасибо за ваш комментарий!*\n\n"
            "Мы обязательно его прочитаем и учтём.\n"
            "Вы помогаете сделать JobPlus лучше 💙",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "⚠️ *Не удалось отправить комментарий*\n\n"
            "Пожалуйста, попробуйте чуть позже 🙏",
            parse_mode="Markdown"
        )
