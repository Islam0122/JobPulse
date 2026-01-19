import uuid
import json
import requests
from requests.auth import HTTPBasicAuth
import re

CLIENT_ID = '71b92890-bf91-4b6b-9645-6561b93e3d7d'
SECRET = '3278c7e4-6c0c-4b7b-a8b7-9baadb679504'



def get_access_token() -> str:
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': str(uuid.uuid4()),
    }
    payload = {"scope": "GIGACHAT_API_PERS"}

    try:
        res = requests.post(
            url=url,
            headers=headers,
            auth=HTTPBasicAuth(CLIENT_ID, SECRET),
            data=payload,
            verify=False,
        )
        res.raise_for_status()
        access_token = res.json().get("access_token")
        if not access_token:
            raise ValueError("Токен доступа не был получен.")
        return access_token
    except requests.RequestException as e:
        print("Ошибка при получении access token:", e)
        return None


def send_prompt(msg: str, access_token: str):
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    payload = json.dumps({
        "model": "GigaChat",
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": msg,
            }
        ],
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    try:
        response = requests.post(url, headers=headers, data=payload, verify=False)
        response.raise_for_status()  # проверка на наличие ошибок
        return response.json()["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        print("Ошибка при отправке запроса к GigaChat API:", e)
        return "Ошибка при получении ответа от GigaChat."


def sent_prompt_and_get_response(msg: str):
    access_token = get_access_token()
    message = msg
    if access_token:
        response = send_prompt(message, access_token)
        decorated_response = f'{response}'
        return decorated_response
    else:
        return "Не удалось получить access token."
    
    
def extract_grade_from_feedback(feedback_text: str):
    match = re.search(r'(\d+(\.\d+)?)\s*/\s*10', feedback_text)
    if match:
        return float(match.group(1))
    return None

def build_prompt(resume_text: str, market_year: int = 2026) -> str:
    return f"""
Ты — опытный HR-эксперт и карьерный консультант.
Ты хорошо понимаешь рынок труда, тренды найма и требования работодателей.

Контекст анализа:
- год рынка труда: {market_year}
- рынок: глобальный (если не указано иное)
- профессии: любые (IT, дизайн, маркетинг, финансы, продажи, управление и др.)

Твоя задача:
1. Проанализировать резюме кандидата
2. Оценить его конкурентоспособность на рынке {market_year}
3. Дать практические рекомендации по улучшению профиля
4. Подсказать, какие навыки и акценты повысят ценность кандидата в ближайший год

Резюме кандидата:
\"\"\"
{resume_text}
\"\"\"

Требования к ответу:
- Верни СТРОГО валидный JSON
- Не используй markdown, комментарии или пояснения
- Все массивы — массивы строк
- overall_score — число от 0 до 10
- Советы должны быть ориентированы на рынок {market_year}

Формат ответа:
{{
  "summary": "Краткое общее впечатление",
  "detected_domain": "IT | design | marketing | finance | sales | management | other | unknown",
  "detected_level": "junior | middle | senior | lead | unknown",
  "market_year": {market_year},
  "strengths": [],
  "weaknesses": [],
  "recommendations": [
    "Конкретные шаги по улучшению резюме и профиля"
  ],
  "market_trends_advice": [
    "Советы с учётом трендов рынка {market_year}"
  ],
  "skills_to_develop": [
    "Навыки и направления для развития в {market_year}"
  ],
  "market_competitiveness": "low | medium | high | unknown",
  "overall_score": 0
}}
"""



def parse_ai_response(res):
    if isinstance(res, dict):
        return res

    if isinstance(res, str):
        try:
            return json.loads(res)
        except json.JSONDecodeError:
            raise ValueError("AI returned invalid JSON")

    raise TypeError(f"Unsupported AI response type: {type(res)}")


def analyze_resume_with_ai(resume_text: str) -> dict:
    response = sent_prompt_and_get_response(
        build_prompt(resume_text)
    )
    return json.loads(response)

