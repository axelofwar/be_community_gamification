from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from db_api import consumers

websocket_urlpatterns = [
    path("ws/leaderboard_updates/", consumers.LeaderboardConsumer.as_asgi())
]

application = ProtocolTypeRouter({
    "websocket": URLRouter(
        websocket_urlpatterns
    ),
})
