from rest_framework import serializers
from django.db import connection


class MessageSerializer(serializers.Serializer):
    sender_name = serializers.CharField()
    receiver_name = serializers.CharField()
    description = serializers.CharField()
    time = serializers.TimeField()

    def fetch_all_messages(self, sender_name, receiver_name):
        """
        Fetch messages using raw SQL.
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT au1.username AS sender_name, 
                       au2.username AS receiver_name, 
                       cm.description, 
                       cm.time
                FROM chat_messages cm
                JOIN auth_user au1 ON cm.sender_name_id = au1.id
                JOIN auth_user au2 ON cm.receiver_name_id = au2.id
                WHERE (au1.username = %s AND au2.username = %s)
                   OR (au1.username = %s AND au2.username = %s)
                ORDER BY cm.time ASC
                """,
                [sender_name, receiver_name, receiver_name, sender_name]
            )
            rows = cursor.fetchall()

        # Transform the result into a list of dictionaries
        return [
            {
                "sender_name": row[0],
                "receiver_name": row[1],
                "description": row[2],
                "time": row[3],
            }
            for row in rows
        ]

    def save_message(self, sender_name, receiver_name, description):
        """
        Save a message using raw SQL.
        """
        with connection.cursor() as cursor:
            # Get sender and receiver IDs
            cursor.execute("SELECT id FROM auth_user WHERE username = %s", [sender_name])
            sender = cursor.fetchone()
            if not sender:
                raise serializers.ValidationError(f"Sender '{sender_name}' not found.")

            cursor.execute("SELECT id FROM auth_user WHERE username = %s", [receiver_name])
            receiver = cursor.fetchone()
            if not receiver:
                raise serializers.ValidationError(f"Receiver '{receiver_name}' not found.")

            # Insert the message into the database
            cursor.execute(
                """
                INSERT INTO chat_messages (description, sender_name_id, receiver_name_id, time, timestamp, seen)
                VALUES (%s, %s, %s, CURRENT_TIME, CURRENT_TIMESTAMP, FALSE)
                RETURNING id
                """,
                [description, sender[0], receiver[0]]
            )
            new_message_id = cursor.fetchone()[0]
        return {"id": new_message_id, "status": "Message saved"}
