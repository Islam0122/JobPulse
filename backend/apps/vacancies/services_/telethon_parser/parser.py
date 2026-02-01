import asyncio
from typing import List, Dict
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.errors import ChannelPrivateError, UsernameNotOccupiedError
import logging
from datetime import datetime, timedelta, timezone
from .client import TelethonClient
from .extractor import VacancyExtractor
from .channels import get_all_channels, get_channels_by_category

logger = logging.getLogger(__name__)


class TelegramVacancyParser:
    def __init__(self):
        self.client_wrapper = TelethonClient()
        self.extractor = VacancyExtractor()
        self.client: TelegramClient = None

    async def parse_channels(
            self,
            channels: List[str] = None,
            category: str = None,
            limit_per_channel: int = 50,
            days_ago: int = 7
    ) -> List[Dict]:
        if channels is None:
            if category:
                channels = get_channels_by_category(category)
            else:
                channels = get_all_channels()

        logger.info(f"🚀 Начинаем парсинг {len(channels)} каналов")

        self.client = await self.client_wrapper.get_client()

        all_vacancies = []

        for channel in channels:
            try:
                vacancies = await self._parse_channel(
                    channel,
                    limit_per_channel,
                    days_ago
                )
                all_vacancies.extend(vacancies)

                logger.info(f"✅ {channel}: найдено {len(vacancies)} вакансий")
                await asyncio.sleep(2)

            except ChannelPrivateError:
                logger.warning(f"⚠️ {channel}: приватный канал")
            except UsernameNotOccupiedError:
                logger.warning(f"⚠️ {channel}: канал не найден")
            except Exception as e:
                logger.error(f"❌ {channel}: ошибка - {e}")

        logger.info(f"🎉 Парсинг завершён. Всего вакансий: {len(all_vacancies)}")
        await self.client_wrapper.disconnect()
        return all_vacancies

    async def _parse_channel(
            self,
            channel_username: str,
            limit: int,
            days_ago: int
    ) -> List[Dict]:
        vacancies = []
        entity = await self.client.get_entity(channel_username)
        min_date = datetime.now(timezone.utc) - timedelta(days=days_ago)

        messages = await self.client.get_messages(
            entity,
            limit=limit
        )

        for message in messages:
            if message.date < min_date:
                continue

            if not message.text:
                continue

            # Извлекаем вакансию
            vacancy_data = self.extractor.extract_vacancy(
                message_text=message.text,
                message_id=message.id,
                chat_username=channel_username.replace('@', ''),
                published_date=message.date
            )

            if vacancy_data:
                vacancies.append(vacancy_data)

        return vacancies

    async def parse_single_message(
            self,
            channel_username: str,
            message_id: int
    ) -> Dict:
        self.client = await self.client_wrapper.get_client()

        entity = await self.client.get_entity(channel_username)
        message = await self.client.get_messages(entity, ids=message_id)

        if not message or not message.text:
            return None

        return self.extractor.extract_vacancy(
            message_text=message.text,
            message_id=message.id,
            chat_username=channel_username.replace('@', ''),
            published_date=message.date
        )