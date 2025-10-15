from channels.generic.websocket import WebsocketConsumer
from channels.exceptions import StopConsumer
from asgiref.sync import async_to_sync


class Chatconsumer(WebsocketConsumer):
    def websocket_connect(self, message):
        # 获取群号
        group = self.scope['url_route']['kwargs'].get("group", "default_group")
        print(f"WebSocket 连接请求，群组: {group}")  # 调试信息

        # 检查 group 是否为空
        if not group:
            group = "default_group"

        async_to_sync(self.channel_layer.group_add)(
            group,
            self.channel_name
        )
        self.accept()
        print(f"WebSocket 连接已接受")  # 调试信息

    def websocket_receive(self, message):
        group = self.scope['url_route']['kwargs'].get("group", "default_group")
        print(f"收到消息: {message['text']}")  # 调试信息

        # 发送到群组
        async_to_sync(self.channel_layer.group_send)(
            group,
            {
                "type": "xx_oo",
                "message": message['text']  # 直接传递字符串
            }
        )

    def xx_oo(self, event):
        # 修正：event['message'] 已经是字符串，不需要再取 ['text']
        text = event['message']
        print(f"发送消息到客户端: {text}")  # 调试信息
        self.send(text_data=text)

    def websocket_disconnect(self, message):
        group = self.scope['url_route']['kwargs'].get("group", "default_group")
        print(f"WebSocket 连接断开")  # 调试信息

        async_to_sync(self.channel_layer.group_discard)(
            group,
            self.channel_name
        )
        raise StopConsumer()