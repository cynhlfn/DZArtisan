import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from channels.db import database_sync_to_async
from django.db import connection

# Define an async function to save the message to the database
@database_sync_to_async
def save_message(sender_name, receiver_name, message):
    with connection.cursor() as cursor:
        # Get sender and receiver user IDs
        cursor.execute("SELECT id FROM auth_user WHERE username = %s", [sender_name])
        sender_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM auth_user WHERE username = %s", [receiver_name])
        receiver_id = cursor.fetchone()[0]

        # Insert message into Messages table
        cursor.execute(
            """
            INSERT INTO chat_messages (description, sender_name_id, receiver_name_id, time, timestamp, seen)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [message, sender_id, receiver_id, timezone.now().time(), timezone.now(), True]
        )

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        print(self.room_name, self.room_group_name)
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender_name = text_data_json['sender_name']
        receiver_name = text_data_json['receiver_name']
        await save_message(sender_name, receiver_name, message)
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender_name
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender
        }))
