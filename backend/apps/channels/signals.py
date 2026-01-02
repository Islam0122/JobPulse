from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import RequiredChannel


@receiver(post_migrate)
def create_default_required_channel(sender, **kwargs):
    if RequiredChannel.objects.exists():
        return

    RequiredChannel.objects.create(
        title="Islam Dev 💎",
        channel_id=3063896635,
        username="@islam_duishobaev_dev",
        is_active=True,
    )
