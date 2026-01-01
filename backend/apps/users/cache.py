from django.core.cache import cache
from django.conf import settings
from typing import Optional, Any
import json


class UserCache:
    CACHE_TTL = 300  # 5 минут

    @staticmethod
    def get_user_key(telegram_id: int) -> str:
        return f'user:{telegram_id}'

    @classmethod
    def get_user(cls, telegram_id: int) -> Optional[dict]:
        key = cls.get_user_key(telegram_id)
        data = cache.get(key)
        return json.loads(data) if data else None

    @classmethod
    def set_user(cls, telegram_id: int, user_data: dict, timeout: int = None):
        key = cls.get_user_key(telegram_id)
        timeout = timeout or cls.CACHE_TTL
        cache.set(key, json.dumps(user_data), timeout)

    @classmethod
    def delete_user(cls, telegram_id: int):
        key = cls.get_user_key(telegram_id)
        cache.delete(key)

    @classmethod
    def clear_all_users(cls):
        cache.delete_pattern('user:*')


class ReferenceCache:
    CACHE_TTL = 3600  # 1 час

    @staticmethod
    def get_stacks() -> Optional[list]:
        return cache.get('stacks:all')

    @staticmethod
    def set_stacks(stacks: list):
        cache.set('stacks:all', stacks, ReferenceCache.CACHE_TTL)

    @staticmethod
    def get_work_formats() -> Optional[list]:
        return cache.get('work_formats:all')

    @staticmethod
    def set_work_formats(formats: list):
        cache.set('work_formats:all', formats, ReferenceCache.CACHE_TTL)

    @staticmethod
    def clear_references():
        cache.delete_pattern('stacks:*')
        cache.delete_pattern('work_formats:*')
        cache.delete_pattern('employment_types:*')