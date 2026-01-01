from aiogram import Router
from aiogram.types import Message

router = Router()

@router.message()
async def echo_message(message: Message):
    if message.text:
        await message.answer(f"Ты написал: {message.text}")

    elif message.photo:
        photo = message.photo[-1]  # самое большое фото
        await message.answer(f"file_id фото:\n{photo.file_id}")
