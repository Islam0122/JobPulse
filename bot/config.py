import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api")
API_TIMEOUT = 10  # Таймаут запросов к API (секунды)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")