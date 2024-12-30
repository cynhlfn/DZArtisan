from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

@csrf_exempt
def chat(request, username):
    if not request.user.is_authenticated:
        logger.warning("Bypassing authentication for testing purposes.")
        request.user = User.objects.get(username="karim")  # Set a specific user for testing
    try:
        usersen = request.user
        friend = None
        user_relation_exists = False
        messages_list = []

        # Fetch the friend user
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username FROM auth_user WHERE username = %s", [username])
            friend_row = cursor.fetchone()
        if not friend_row:
            return JsonResponse({"error": "Friend not found."}, status=404)

        friend = {"id": friend_row[0], "username": friend_row[1]}

        # Check if UserRelation exists and is accepted
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM chat_userrelation 
                WHERE user_id = %s AND friend_id = %s AND accepted = TRUE
                """,
                [usersen.id, friend['id']]
            )
            user_relation_exists = cursor.fetchone() is not None

        if not user_relation_exists:
            return JsonResponse({"error": "You are not able to chat with this user."}, status=403)

        # Fetch messages between users
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT description, sender_name_id, receiver_name_id, time, seen, timestamp
                FROM chat_messages
                WHERE (sender_name_id = %s AND receiver_name_id = %s)
                   OR (sender_name_id = %s AND receiver_name_id = %s)
                ORDER BY timestamp ASC
                """,
                [usersen.id, friend['id'], friend['id'], usersen.id]
            )
            for row in cursor.fetchall():
                messages_list.append({
                    "description": row[0],
                    "sender_name_id": row[1],
                    "receiver_name_id": row[2],
                    "time": row[3],
                    "seen": row[4],
                    "timestamp": row[5],
                })

        # Fetch the relation key
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT relation_key FROM chat_userrelation
                WHERE user_id = %s AND friend_id = %s AND accepted = TRUE
                """,
                [usersen.id, friend['id']]
            )
            relation = cursor.fetchone()
        if not relation:
            return JsonResponse({"error": "Relation not found."}, status=404)

        return JsonResponse({
            "relation_key": relation[0],
            "messages": messages_list,
            "curr_user": {"id": usersen.id, "username": usersen.username},
            "friend": friend,
        }, status=200)

    except Exception as e:
        logger.error(f"Error in chat view: {e}", exc_info=True)
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)


@csrf_exempt
def message_list(request, sender=None, receiver=None):
    if not request.user.is_authenticated:
        logger.warning("Bypassing authentication for testing purposes.")
        request.user = User.objects.get(username="karim")  # Set a specific user for testing
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
