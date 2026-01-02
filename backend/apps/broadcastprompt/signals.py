from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import BroadcastMessage
from .services import send_broadcast_message


@receiver(post_save, sender=BroadcastMessage)
def broadcast_post_save(sender, instance, created, **kwargs):
    if instance.is_published and not instance.published_at:
        send_broadcast_message(instance)
