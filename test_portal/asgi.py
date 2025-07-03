import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from exams.consumers import ChatConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_portal.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path('ws/chat/', ChatConsumer.as_asgi()),
        ])
    ),
})
