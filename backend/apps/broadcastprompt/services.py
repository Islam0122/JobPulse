import requests
from django.conf import settings
from django.utils import timezone
from apps.users.models import User


def send_broadcast_message(broadcast):
    users = User.objects.exclude(telegram_id__isnull=True)

    for user in users:
        payload = {
            "chat_id": user.telegram_id,
            "text": f"📌 {broadcast.subject}\n\n{broadcast.content}",
            "parse_mode": "HTML"
        }

        try:
            requests.post(
                f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
                json=payload,
                timeout=5
            )
        except Exception as e:
            print(f"Ошибка отправки {user.telegram_id}: {e}")

    broadcast.is_published = True
    broadcast.published_at = timezone.now()
    broadcast.save(update_fields=["is_published", "published_at"])
