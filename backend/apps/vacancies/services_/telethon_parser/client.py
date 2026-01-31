import os
import asyncio
from telethon import TelegramClient, errors
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class TelethonClient:
    _instance = None
    _client = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.api_id = settings.TELETHON_API_ID
            self.api_hash = settings.TELETHON_API_HASH
            self.phone = settings.TELETHON_PHONE
            self.session_name = settings.TELETHON_SESSION_NAME
            self._initialized = True

    async def get_client(self) -> TelegramClient:
        if self._client is None or not self._client.is_connected():
            await self._create_client()

        return self._client

    async def _create_client(self):
        try:
            session_path = os.path.join(
                settings.BASE_DIR,
                'sessions',
                self.session_name
            )
            os.makedirs(os.path.dirname(session_path), exist_ok=True)
            self._client = TelegramClient(
                session_path,
                self.api_id,
                self.api_hash,
                device_model='JobPulse Parser',
                app_version='1.0.0',
                system_version='Linux'
            )

            await self._client.connect()

            if not await self._client.is_user_authorized():
                logger.warning("Требуется авторизация Telethon")
                await self._authorize()
            else:
                logger.info("✅ Telethon клиент подключен")

        except Exception as e:
            logger.error(f"❌ Ошибка создания Telethon клиента: {e}")
            raise

    async def _authorize(self):
        try:
            await self._client.send_code_request(self.phone)

            logger.warning(
                f"📱 Отправлен код авторизации на {self.phone}\n"
                f"Введи код через команду: python manage.py telethon_auth <code>"
            )
        except errors.FloodWaitError as e:
            logger.error(f"⏳ Flood wait: {e.seconds} секунд")
            raise

    async def disconnect(self):
        if self._client and self._client.is_connected():
            await self._client.disconnect()
            logger.info("Telethon клиент отключен")

    async def __aenter__(self):
        return await self.get_client()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()