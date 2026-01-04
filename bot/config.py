import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Django Backend API
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api")
API_TIMEOUT = 10


from urllib.parse import urlparse

# Берём URL Redis, если он есть
REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL:
    parsed = urlparse(REDIS_URL)
    REDIS_HOST = parsed.hostname
    REDIS_PORT = parsed.port
    REDIS_DB = int(parsed.path.lstrip("/") or 0)
    REDIS_PASSWORD = parsed.password
else:
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 1))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)