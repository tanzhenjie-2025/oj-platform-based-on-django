from django.urls import re_path
from CheckObjectionApp import consumers
# websockets_urlpatterns =[
# re_path(r'ws/(?P<group>\w+)/$',consumers.Chatconsumer.as_asgi()),]

websocket_urlpatterns = [
    re_path(r'ws/(?P<group>\w+)/$', consumers.Chatconsumer.as_asgi()),
]