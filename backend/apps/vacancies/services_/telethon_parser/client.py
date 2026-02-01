import os
from telethon import TelegramClient
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class TelethonClient:
    def __init__(self):
        self.api_id = settings.TELETHON_API_ID
        self.api_hash = settings.TELETHON_API_HASH
        self.phone = settings.TELETHON_PHONE
        self.session_name = settings.TELETHON_SESSION_NAME
        self._client = None
        self._pid = None

    async def get_client(self) -> TelegramClient:
        current_pid = os.getpid()

        if self._client is None or self._pid != current_pid:
            if self._client is not None:
                try:
                    await self._client.disconnect()
                except:
                    pass

            self._pid = current_pid
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
                logger.warning("Telethon requires authorization")
                await self._authorize()
            else:
                logger.info(f"✅ Telethon connected (PID: {self._pid})")

        except Exception as e:
            logger.error(f"❌ Error creating Telethon client: {e}")
            raise

    async def disconnect(self):
        if self._client and self._client.is_connected():
            await self._client.disconnect()