from telethon import TelegramClient

api_id = 39053860
api_hash = "d3fa5ddb3184373ad9d09e89c9e433bd"
phone = "+996552325295"

with TelegramClient("jobpulse", api_id, api_hash) as client:
    client.start(phone=phone)
    print("✅ Успешно авторизован")
