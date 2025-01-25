from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)
@csrf_exempt
def send_message(request, user_id, friend_id):
    if request.method == "POST":
        # Parse the request body
        if request.content_type == "application/json":
            data = json.loads(request.body)
        else:
            return JsonResponse({"error": "Invalid content type. Use JSON."}, status=400)

        message_content = data.get("message")

        # Validate required fields
        if not message_content:
            return JsonResponse({"error": "The 'message' field is required."}, status=400)

        # Check if both users exist in the database
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM auth_user WHERE id = %s", [user_id])
            sender = cursor.fetchone()
            if not sender:
                return JsonResponse({"error": f"Sender with ID {user_id} not found."}, status=404)

            cursor.execute("SELECT id FROM auth_user WHERE id = %s", [friend_id])
            receiver = cursor.fetchone()
            if not receiver:
                return JsonResponse({"error": f"Receiver with ID {friend_id} not found."}, status=404)

        # Insert the message into the database
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO chat_messages (description, sender_name_id, receiver_name_id)
                    VALUES (%s, %s, %s)
                    """,
                    [message_content, user_id, friend_id]
                )

            return JsonResponse({"message": "Message sent successfully."}, status=201)
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return JsonResponse({"error": "An error occurred while sending the message."}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)

@csrf_exempt
def message_list(request, sender=None, receiver=None):
    if not request.user.is_authenticated:
        #logger.warning("Bypassing authentication for testing purposes.")
        #request.user = User.objects.get(username="karim") 
        return JsonResponse({"error": "You must be logged in to perform this action."}, status=403)
    try:
        if request.method == "GET":
            messages_list = []
            # Fetch unseen messages
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, description, sender_name_id, receiver_name_id, seen, timestamp 
                    FROM chat_messages
                    WHERE sender_name_id = %s AND receiver_name_id = %s AND seen = FALSE
                    """,
                    [sender, receiver]
                )
                for row in cursor.fetchall():
                    messages_list.append({
                        "id": row[0],
                        "description": row[1],
                        "sender_name_id": row[2],
                        "receiver_name_id": row[3],
                        "seen": row[4],
                        "timestamp": row[5],
                    })

            # Mark messages as seen
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE chat_messages
                    SET seen = TRUE
                    WHERE sender_name_id = %s AND receiver_name_id = %s AND seen = FALSE
                    """,
                    [sender, receiver]
                )

            return JsonResponse(messages_list, safe=False, status=200)

        elif request.method == "POST":
            data = json.loads(request.body)

            # Insert a new message
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO chat_messages (description, sender_name_id, receiver_name_id, time, timestamp, seen)
                    VALUES (%s, %s, %s, CURRENT_TIME, CURRENT_TIMESTAMP, FALSE)
                    RETURNING id
                    """,
                    [data['description'], sender, receiver]
                )
                new_message_id = cursor.fetchone()[0]

            return JsonResponse({"id": new_message_id, "status": "Message sent"}, status=201)

        return JsonResponse({"error": "Invalid request method"}, status=405)

    except Exception as e:
        logger.error(f"Error in message_list view: {e}", exc_info=True)
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)
@csrf_exempt
def get_messages(request, user_id, friend_id):
    if request.method == "GET":
        try:
            # Query the database for messages between the two users
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 
                        id_chat_messages AS id,
                        description AS message,
                        sender_name_id AS senderId,
                        receiver_name_id AS receiverId,
                        time,
                        seen
                    FROM chat_messages
                    WHERE 
                        (sender_name_id = %s AND receiver_name_id = %s) OR 
                        (sender_name_id = %s AND receiver_name_id = %s)
                    ORDER BY timestamp ASC
                    """,
                    [user_id, friend_id, friend_id, user_id]
                )
                messages = cursor.fetchall()

            # Format the messages into a list of dictionaries
            messages_list = [
                {
                    "id": row[0],
                    "message": row[1],
                    "senderId": row[2],
                    "receiverId": row[3],
                    "time": str(row[4]),
                    "seen": row[5],
                }
                for row in messages
            ]

            # Return the list of messages
            return JsonResponse({"messages": messages_list}, status=200)

        except Exception as e:
            logger.error(f"Error retrieving messages: {str(e)}")
            return JsonResponse({"error": "An error occurred while retrieving messages."}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)
