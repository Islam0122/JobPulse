import aiohttp
import config
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class APIClient:
    """Клиент для работы с Backend API"""

    def __init__(self):
        self.base_url = config.BACKEND_URL
        self.timeout = aiohttp.ClientTimeout(total=config.API_TIMEOUT)
        # Кэш для каналов
        self._channels_cache = None
        self._channels_cache_time = 0
        self.CACHE_TTL = 300  # 5 минут

    async def _make_request(
            self,
            method: str,
            endpoint: str,
            data: Optional[Dict] = None,
            params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Базовый метод для HTTP запросов

        Args:
            method: HTTP метод (GET, POST, PATCH, DELETE)
            endpoint: Путь API (например: "users/")
            data: JSON данные для POST/PATCH
            params: Query параметры для GET

        Returns:
            Dict с ответом или None при ошибке
        """
        url = f"{self.base_url}/{endpoint}"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.request(
                        method=method,
                        url=url,
                        json=data,
                        params=params
                ) as response:
                    if response.status in [200, 201, 204]:
                        if response.status == 204:
                            return {"status": "success"}
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"API Error {response.status}: {error_text}"
                        )
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

    async def update_user(
            self,
            telegram_id: int,
            user_data: Dict
    ) -> Optional[Dict]:
        """Обновить данные пользователя (PATCH)"""
        return await self._make_request(
            "PATCH",
            f"users/{telegram_id}/",
            data=user_data
        )

    async def complete_onboarding(self, telegram_id: int) -> Optional[Dict]:
        """Завершить онбординг пользователя"""
        return await self._make_request(
            "POST",
            f"users/{telegram_id}/complete_onboarding/"
        )

    async def update_notification_mode(
            self,
            telegram_id: int,
            mode: str
    ) -> Optional[Dict]:
        """
        Обновить режим уведомлений

        Args:
            mode: 'instant', 'daily', 'weekly'
        """
        return await self._make_request(
            "PATCH",
            f"users/{telegram_id}/update_notification_mode/",
            data={"notify_mode": mode}
        )

    # ============= СПРАВОЧНИКИ =============

    async def get_stacks(self) -> List[Dict]:
        """Получить список технологий"""
        result = await self._make_request("GET", "stacks/")
        return result.get("results", []) if result else []

    async def get_work_formats(self) -> List[Dict]:
        """Получить форматы работы (Remote/Office/Hybrid)"""
        result = await self._make_request("GET", "work-formats/")
        return result.get("results", []) if result else []

    async def get_employment_types(self) -> List[Dict]:
        """Получить типы занятости (Full-time/Part-time/Contract)"""
        result = await self._make_request("GET", "employment-types/")
        return result.get("results", []) if result else []

    async def get_required_channels(self) -> List[Dict]:
        """
        Получить список обязательных каналов для подписки
        Использует кэш для снижения нагрузки
        """
        import time
        now = time.time()

        # Проверяем кэш
        if (self._channels_cache and
                (now - self._channels_cache_time) < self.CACHE_TTL):
            return self._channels_cache

        # Запрашиваем с сервера
        result = await self._make_request("GET", "required-channels/")
        channels = result.get("results", []) if result else []

        # Сохраняем в кэш
        self._channels_cache = channels
        self._channels_cache_time = now

        return channels

    # ============= VACANCY ENDPOINTS =============

    async def get_vacancies(
            self,
            limit: int = 20,
            **filters
    ) -> List[Dict]:
        """
        Получить список вакансий

        Args:
            limit: количество вакансий
            **filters: location, search и т.д.
        """
        params = {"limit": limit, **filters}
        result = await self._make_request("GET", "vacancies/", params=params)
        return result.get("results", []) if result else []

    async def get_recommended_vacancies(
            self,
            telegram_id: int,
            limit: int = 10
    ) -> List[Dict]:
        """Получить персональные рекомендации для пользователя"""
        params = {"telegram_id": telegram_id, "limit": limit}
        result = await self._make_request(
            "GET",
            "vacancies/recommended/",
            params=params
        )
        return result.get("results", []) if result else []

    async def get_vacancy_detail(self, vacancy_id: int) -> Optional[Dict]:
        """Получить полную информацию о вакансии"""
        return await self._make_request("GET", f"vacancies/{vacancy_id}/")

    async def react_to_vacancy(
            self,
            telegram_id: int,
            vacancy_id: int,
            reaction: str
    ) -> Optional[Dict]:
        """
        Поставить реакцию на вакансию

        Args:
            reaction: 'like' или 'dislike'
        """
        data = {
            "telegram_id": telegram_id,
            "reaction": reaction
        }
        return await self._make_request(
            "POST",
            f"vacancies/{vacancy_id}/react/",
            data=data
        )

    async def add_to_favorites(
            self,
            telegram_id: int,
            vacancy_id: int,
            notes: str = ""
    ) -> Optional[Dict]:
        """Добавить вакансию в избранное"""
        data = {
            "telegram_id": telegram_id,
            "notes": notes
        }
        return await self._make_request(
            "POST",
            f"vacancies/{vacancy_id}/add_to_favorites/",
            data=data
        )

    async def remove_from_favorites(
            self,
            telegram_id: int,
            vacancy_id: int
    ) -> Optional[Dict]:
        """Удалить вакансию из избранного"""
        params = {"telegram_id": telegram_id}
        return await self._make_request(
            "DELETE",
            f"vacancies/{vacancy_id}/remove_from_favorites/",
            params=params
        )

    async def get_favorite_vacancies(
            self,
            telegram_id: int
    ) -> List[Dict]:
        """Получить избранные вакансии"""
        params = {"telegram_id": telegram_id}
        result = await self._make_request(
            "GET",
            "vacancies/favorites/",
            params=params
        )
        return result.get("results", []) if result else []

    async def get_vacancy_history(self, telegram_id: int) -> List[Dict]:
        """Получить историю просмотренных вакансий"""
        params = {"telegram_id": telegram_id}
        result = await self._make_request(
            "GET",
            "vacancies/history/",
            params=params
        )
        return result.get("results", []) if result else []

    async def mark_vacancy_viewed(
            self,
            telegram_id: int,
            vacancy_id: int
    ) -> Optional[Dict]:
        """Отметить вакансию как просмотренную"""
        data = {"telegram_id": telegram_id}
        return await self._make_request(
            "POST",
            f"vacancies/{vacancy_id}/mark_viewed/",
            data=data
        )

    # ============= АНАЛИТИКА =============

    async def get_user_insights(self, telegram_id: int) -> Optional[Dict]:
        """
        Получить аналитику предпочтений пользователя
        Основано на лайках и дизлайках
        """
        params = {"telegram_id": telegram_id}
        return await self._make_request(
            "GET",
            "users/insights/",
            params=params
        )



    async def get_user_stats(self, telegram_id: int) -> Optional[Dict]:
        """Получить статистику активности пользователя"""
        params = {"telegram_id": telegram_id}
        return await self._make_request(
            "GET",
            "users/stats/",
            params=params
        )

    async def send_comment(
            self,
            telegram_id: int,
            text: str
    ) -> Optional[Dict]:
        """
        Отправить комментарий / фидбек боту

        Args:
            telegram_id: Telegram ID пользователя
            text: Текст комментария
        """
        data = {
            "telegram_id": telegram_id,
            "text": text
        }

        return await self._make_request(
            "POST",
            "comments/",
            data=data
        )


api = APIClient()