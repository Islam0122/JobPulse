from celery import shared_task
from django.core.cache import cache
from .models import User
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_notification(user_id: int, message: str):
    try:
        user = User.objects.get(telegram_id=user_id)
        logger.info(f'Sending notification to {user.username}: {message}')
        # Здесь логика отправки через Telegram API
        return f'Notification sent to {user_id}'
    except User.DoesNotExist:
        logger.error(f'User {user_id} not found')
        return f'User {user_id} not found'


@shared_task
def send_daily_notifications():
    users = User.objects.filter(
        is_active=True,
        notify_mode='daily'
    )

    count = 0
    for user in users:
        send_notification.delay(user.telegram_id, 'Daily digest')
        count += 1

    return f'Scheduled {count} notifications'


@shared_task
def clear_expired_cache():
    try:
        cache.delete_pattern('user:*')
        logger.info('Cache cleared successfully')
        return 'Cache cleared'
    except Exception as e:
        logger.error(f'Cache clear error: {e}')
        return f'Error: {e}'


@shared_task
def update_user_statistics():
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()

    cache.set('stats:total_users', total_users, 3600)
    cache.set('stats:active_users', active_users, 3600)

    return f'Stats updated: {total_users} total, {active_users} active'