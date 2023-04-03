from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json
from db_api.models import Tweet


@receiver(post_save, sender=Tweet)
def handle_leaderboard_update(sender, instance, **kwargs):
    # Send a websocket message to all connected clients in the leaderboard_updates channel
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "leaderboard_updates",
        {
            "type": "leaderboard_update",
            # Convert the instance to a JSON-serializable dict
            "data": json.dumps(instance.to_dict()),
        },
    )
