import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from channels.db import database_sync_to_async
from django.db import connection

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]
        sender_name = data["sender_name"]
        receiver_name = data["receiver_name"]

        # Save the message to the database
        await self.save_message(sender_name, receiver_name, message)

        # Broadcast message to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "sender_name": sender_name,
            },
        )

    @database_sync_to_async
    def save_message(self, sender_name, receiver_name, message):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO chat_messages (description, sender_name_id, receiver_name_id, time, timestamp, seen)
                VALUES (%s, (SELECT id FROM auth_user WHERE username = %s), (SELECT id FROM auth_user WHERE username = %s), CURRENT_TIME, CURRENT_TIMESTAMP, FALSE)
                """,
                [message, sender_name, receiver_name],
            )

    async def chat_message(self, event):
        message = event["message"]
        sender_name = event["sender_name"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message, "sender_name": sender_name}))