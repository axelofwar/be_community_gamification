from channels.generic.websocket import AsyncWebsocketConsumer
import json
from db_api import signals
from db_api.models import Tweet
from asgiref.sync import sync_to_async


class LeaderboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Accept the websocket connection
        await self.accept()

        # Subscribe the client to a specific channel (e.g. leaderboard_updates)
        await self.channel_layer.group_add("leaderboard_updates", self.channel_name)

    async def disconnect(self, close_code):
        # Unsubscribe the client from the channel
        await self.channel_layer.group_discard("leaderboard_updates", self.channel_name)

    async def update_leaderboard(self, event):
        # Send a websocket message to the client with the updated data
        await self.send(text_data=json.dumps(event["data"]))

    @sync_to_async
    def get_leaderboard_data(self):
        # get the leaderboard data from the database
        # sorted by scores in descending order
        leaderboard_data = Tweet.objects.order_by('-Global_Reach')
        return leaderboard_data

    async def leaderboard_update_handler(self, event):
        leaderboard_data = await self.get_leaderboard_data()
        data = {
            'type': 'leaderboard_data',
            'leaderboard_data': leaderboard_data
        }
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'update_leaderboard',
                'data': data
            }
        )
