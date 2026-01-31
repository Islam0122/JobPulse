import os
from pathlib import Path

TELETHON_API_ID = int(os.getenv('TELETHON_API_ID', '0'))
TELETHON_API_HASH = os.getenv('TELETHON_API_HASH', '')
TELETHON_PHONE = os.getenv('TELETHON_PHONE', '')

TELETHON_SESSION_NAME = os.getenv('TELETHON_SESSION_NAME', 'jobpulse_parser')

TELETHON_SESSIONS_DIR = Path(os.getenv(
    'TELETHON_SESSIONS_DIR',
    str(Path(__file__).resolve().parent.parent.parent / 'sessions')
))

TELETHON_MESSAGES_LIMIT = int(os.getenv('TELETHON_MESSAGES_LIMIT', '50'))
TELETHON_DAYS_AGO = int(os.getenv('TELETHON_DAYS_AGO', '7'))
TELETHON_CHANNEL_DELAY = int(os.getenv('TELETHON_CHANNEL_DELAY', '2'))
TELETHON_MAX_CHANNELS_PER_RUN = int(os.getenv('TELETHON_MAX_CHANNELS_PER_RUN', '10'))