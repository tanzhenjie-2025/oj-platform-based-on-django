"""
ASGI config for CheckObjection project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

# import os
#
# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# from . import routing
# from django.core.asgi import get_asgi_application
#
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CheckObjection.settings")
#
# # application = get_asgi_application()
# application = ProtocolTypeRouter({
# "http": get_asgi_application(),
# "websocket": URLRouter(routing.websockets_urlpatterns),
# })

# CheckObjection/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import CheckObjection.routing  # 导入您的应用路由

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CheckObjection.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            CheckObjection.routing.websocket_urlpatterns  # 确保变量名一致
        )
    ),
})

