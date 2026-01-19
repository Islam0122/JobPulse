import uuid
import json
import requests
from requests.auth import HTTPBasicAuth
import re
import logging
from typing import Dict, Optional
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class GigaChatAPIError(Exception):
    pass


class GigaChatClient:
    """
    Клиент для работы с GigaChat API

    Использование:
        client = GigaChatClient()
        result = client.analyze_resume(resume_text)
    """

    BASE_URL = "https://ngw.devices.sberbank.ru:9443"
    CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    # Таймауты
    TOKEN_TIMEOUT = 10
    CHAT_TIMEOUT = 60

    # Кэширование токена (55 минут)
    TOKEN_CACHE_KEY = "gigachat_access_token"
    TOKEN_CACHE_TIMEOUT = 55 * 60

    def __init__(self):
        """Инициализация клиента с credentials из настроек"""
        self.client_id = getattr(settings, 'GIGACHAT_CLIENT_ID', None)
        self.secret = getattr(settings, 'GIGACHAT_SECRET', None)

        if not self.client_id or not self.secret:
            raise GigaChatAPIError(
                "GIGACHAT_CLIENT_ID и GIGACHAT_SECRET должны быть установлены в settings"
            )

    def get_access_token(self) -> str:
        """
        Получение access token с кэшированием

        Returns:
            str: Access token

        Raises:
            GigaChatAPIError: Если не удалось получить токен
        """
        # Проверяем кэш
        cached_token = cache.get(self.TOKEN_CACHE_KEY)
        if cached_token:
            logger.debug("Использован кэшированный токен")
            return cached_token

        url = f"{self.BASE_URL}/api/v2/oauth"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4()),
        }
        payload = {"scope": "GIGACHAT_API_PERS"}

        try:
            logger.info("Запрос нового access token...")
            response = requests.post(
                url=url,
                headers=headers,
                auth=HTTPBasicAuth(self.client_id, self.secret),
                data=payload,
                verify=False,
                timeout=self.TOKEN_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            access_token = data.get("access_token")

            if not access_token:
                raise GigaChatAPIError("Токен не найден в ответе API")

            # Кэшируем токен
            cache.set(self.TOKEN_CACHE_KEY, access_token, self.TOKEN_CACHE_TIMEOUT)
            logger.info("Access token успешно получен и закэширован")

            return access_token

        except requests.Timeout:
            logger.error("Timeout при получении токена")
            raise GigaChatAPIError("Превышено время ожидания при получении токена")
        except requests.RequestException as e:
            logger.error(f"Ошибка при получении токена: {e}")
            raise GigaChatAPIError(f"Не удалось получить access token: {str(e)}")

    def send_chat_request(self, message: str, temperature: float = 0.0) -> str:
        """
        Отправка запроса в GigaChat

        Args:
            message: Текст промпта
            temperature: Температура генерации (0.0 - 1.0)

        Returns:
            str: Ответ от модели

        Raises:
            GigaChatAPIError: Если произошла ошибка
        """
        access_token = self.get_access_token()

        payload = {
            "model": "GigaChat",
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": message,
                }
            ],
        }

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        try:
            logger.info("Отправка запроса в GigaChat...")
            response = requests.post(
                self.CHAT_URL,
                headers=headers,
                json=payload,
                verify=False,
                timeout=self.CHAT_TIMEOUT
            )

            # Обработка 401 - невалидный токен
            if response.status_code == 401:
                logger.warning("Токен невалиден, запрашиваем новый...")
                cache.delete(self.TOKEN_CACHE_KEY)

                # Повторная попытка с новым токеном
                access_token = self.get_access_token()
                headers['Authorization'] = f'Bearer {access_token}'

                response = requests.post(
                    self.CHAT_URL,
                    headers=headers,
                    json=payload,
                    verify=False,
                    timeout=self.CHAT_TIMEOUT
                )

            response.raise_for_status()
            data = response.json()

            content = data.get("choices", [{}])[0].get("message", {}).get("content")

            if not content:
                raise GigaChatAPIError("Пустой ответ от модели")

            logger.info("Ответ от GigaChat успешно получен")
            return content

        except requests.Timeout:
            logger.error("Timeout при запросе к GigaChat")
            raise GigaChatAPIError("Превышено время ожидания ответа от GigaChat")
        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе к GigaChat: {e}")
            raise GigaChatAPIError(f"Ошибка API: {str(e)}")

    def analyze_resume(self, resume_text: str, market_year: int = 2026) -> Dict:
        """
        Анализ резюме с помощью GigaChat

        Args:
            resume_text: Текст резюме
            market_year: Год для контекста рынка труда

        Returns:
            dict: Структурированный результат анализа

        Raises:
            GigaChatAPIError: Если произошла ошибка
        """
        if not resume_text or not resume_text.strip():
            raise ValueError("Текст резюме не может быть пустым")

        prompt = self._build_prompt(resume_text, market_year)

        try:
            response = self.send_chat_request(prompt, temperature=0.0)
            parsed = self._parse_response(response)

            # Валидация результата
            self._validate_result(parsed)

            return parsed

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Ошибка парсинга ответа: {e}")
            raise GigaChatAPIError(f"Не удалось распарсить ответ модели: {str(e)}")

    def _build_prompt(self, resume_text: str, market_year: int) -> str:
        """Построение промпта для анализа резюме"""
        return f"""Ты — опытный HR-эксперт и карьерный консультант с 15+ летним опытом.
Ты специализируешься на оценке резюме и даёшь практические рекомендации кандидатам.

КОНТЕКСТ АНАЛИЗА:
• Текущий год: {market_year}
• Рынок: глобальный (IT, дизайн, маркетинг, финансы, управление и др.)
• Цель: помочь кандидату улучшить резюме и повысить шансы на трудоустройство

РЕЗЮМЕ КАНДИДАТА:
\"\"\"
{resume_text}
\"\"\"

ЗАДАЧА:
Проанализируй резюме и верни СТРОГО ВАЛИДНЫЙ JSON без дополнительного текста, markdown или комментариев.

ТРЕБОВАНИЯ К ОТВЕТУ:
1. Формат: чистый JSON (без ```json или других обёрток)
2. Все поля обязательны
3. Массивы должны содержать минимум 2-3 элемента
4. overall_score: число от 0 до 10 (с точностью до 0.5)
5. Рекомендации должны быть конкретными и применимыми

ФОРМАТ ОТВЕТА:
{{
  "summary": "2-3 предложения о резюме",
  "detected_domain": "IT | design | marketing | finance | sales | management | other | unknown",
  "detected_level": "junior | middle | senior | lead | unknown",
  "market_year": {market_year},
  "strengths": [
    "Конкретная сильная сторона 1",
    "Конкретная сильная сторона 2",
    "Конкретная сильная сторона 3"
  ],
  "weaknesses": [
    "Конкретная слабая сторона 1",
    "Конкретная слабая сторона 2",
    "Конкретная слабая сторона 3"
  ],
  "recommendations": [
    "Практическая рекомендация 1",
    "Практическая рекомендация 2",
    "Практическая рекомендация 3"
  ],
  "market_trends_advice": [
    "Актуальный тренд/совет 1 для {market_year}",
    "Актуальный тренд/совет 2 для {market_year}"
  ],
  "skills_to_develop": [
    "Навык для развития 1",
    "Навык для развития 2",
    "Навык для развития 3"
  ],
  "market_competitiveness": "low | medium | high | unknown",
  "overall_score": 7.5
}}

ВАЖНО: Верни ТОЛЬКО JSON, без преамбулы, пояснений или форматирования."""

    def _parse_response(self, response: str) -> Dict:
        """
        Парсинг ответа от модели

        Args:
            response: Текстовый ответ

        Returns:
            dict: Распарсенный JSON
        """
        # Удаляем markdown форматирование если есть
        cleaned = response.strip()

        # Убираем ```json и ``` если есть
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Response: {response[:500]}")
            raise

    def _validate_result(self, result: Dict) -> None:
        """
        Валидация структуры результата

        Args:
            result: Результат для валидации

        Raises:
            ValueError: Если структура невалидна
        """
        required_fields = [
            "summary", "detected_domain", "detected_level",
            "strengths", "weaknesses", "recommendations",
            "market_trends_advice", "skills_to_develop",
            "market_competitiveness", "overall_score"
        ]

        missing = [f for f in required_fields if f not in result]
        if missing:
            raise ValueError(f"Отсутствуют обязательные поля: {missing}")

        # Валидация типов
        for field in ["strengths", "weaknesses", "recommendations",
                      "market_trends_advice", "skills_to_develop"]:
            if not isinstance(result[field], list):
                raise ValueError(f"{field} должен быть массивом")
            if len(result[field]) < 2:
                raise ValueError(f"{field} должен содержать минимум 2 элемента")

        # Валидация overall_score
        score = result["overall_score"]
        if not isinstance(score, (int, float)) or score < 0 or score > 10:
            raise ValueError("overall_score должен быть числом от 0 до 10")


# Публичный API
def analyze_resume_with_ai(resume_text: str) -> Dict:
    """
    Анализ резюме с помощью AI

    Args:
        resume_text: Текст резюме для анализа

    Returns:
        dict: Структурированный результат анализа

    Raises:
        ValueError: Если входные данные невалидны
        GigaChatAPIError: Если произошла ошибка API
    """
    client = GigaChatClient()
    return client.analyze_resume(resume_text)


def extract_grade_from_feedback(feedback_text: str) -> Optional[float]:
    """
    Извлечение оценки из текста обратной связи

    Args:
        feedback_text: Текст с оценкой (например "8.5 / 10")

    Returns:
        float или None: Оценка если найдена
    """
    match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*10', feedback_text)
    if match:
        return float(match.group(1))
    return None