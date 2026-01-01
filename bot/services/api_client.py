import aiohttp
import config
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class APIClient:
    """Клиент для работы с Django REST API"""

    def __init__(self):
        self.base_url = config.BACKEND_URL
        self.timeout = aiohttp.ClientTimeout(total=config.API_TIMEOUT)

    async def _make_request(
            self,
            method: str,
            endpoint: str,
            data: Optional[Dict] = None,
            params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Базовый метод для HTTP запросов"""
        url = f"{self.base_url}/{endpoint}"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.request(
                        method=method,
                        url=url,
                        json=data,
                        params=params
                ) as response:
                    if response.status in [200, 201]:
                        return await response.json()
                    else:
                        logger.error(f"API Error {response.status}: {await response.text()}")
                        return None
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None

    # ============= USER ENDPOINTS =============

    async def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Получить пользователя по telegram_id"""
        return await self._make_request("GET", f"users/{telegram_id}/")

    async def create_user(self, user_data: Dict) -> Optional[Dict]:
        """Создать нового пользователя"""
        return await self._make_request("POST", "users/", data=user_data)

    async def update_user(self, telegram_id: int, user_data: Dict) -> Optional[Dict]:
        """Обновить данные пользователя (PATCH)"""
        return await self._make_request("PATCH", f"users/{telegram_id}/", data=user_data)

    async def complete_onboarding(self, telegram_id: int) -> Optional[Dict]:
        """Завершить онбординг пользователя"""
        return await self._make_request("POST", f"users/{telegram_id}/complete_onboarding/")

    async def update_notification_mode(self, telegram_id: int, mode: str) -> Optional[Dict]:
        """Обновить режим уведомлений"""
        return await self._make_request(
            "PATCH",
            f"users/{telegram_id}/update_notification_mode/",
            data={"notify_mode": mode}
        )

    # ============= REFERENCE DATA =============

    async def get_stacks(self) -> List[Dict]:
        """Получить список технологий"""
        result = await self._make_request("GET", "stacks/")
        return result.get("results", []) if result else []

    async def get_work_formats(self) -> List[Dict]:
        """Получить форматы работы"""
        result = await self._make_request("GET", "work-formats/")
        return result.get("results", []) if result else []

    async def get_employment_types(self) -> List[Dict]:
        """Получить типы занятости"""
        result = await self._make_request("GET", "employment-types/")
        return result.get("results", []) if result else []


# Singleton instance
api = APIClient()