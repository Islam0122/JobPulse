import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Django Backend API
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api")
API_TIMEOUT = 10


REDIS_URL = os.getenv("REDIS_URL")
