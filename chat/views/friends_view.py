from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
import json

logger = logging.getLogger(__name__)
@csrf_exempt
def delete_friend(request, user_id, friend_id):
    if request.method == "DELETE":
        try:
            # Query to delete the friend relationship
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM chat_userrelation
                    WHERE (user_id = %s AND friend_id = %s) OR (user_id = %s AND friend_id = %s)
                    """,
                    [user_id, friend_id, friend_id, user_id]
                )

                # Check if any rows were affected (if the relationship existed)
                if cursor.rowcount == 0:
                    return JsonResponse({"error": "Friend relationship not found."}, status=404)

                return JsonResponse({"message": "Friend deleted successfully."}, status=200)

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


@csrf_exempt
def accept_friend(request, receiver_id):
    if request.method == "POST":
        # Parse request body
        if request.content_type == "application/json":
            data = json.loads(request.body)
            username = data.get("username")
        else:
            username = request.POST.get("username")

        logger.info(f"Received request to accept friend: {username} by receiver ID: {receiver_id}")

        # Verify receiver exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM auth_user WHERE id = %s", [receiver_id])
            receiver_row = cursor.fetchone()
            if not receiver_row:
                return JsonResponse({"error": "Receiver user does not exist."}, status=404)

        # Verify sender exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM auth_user WHERE username = %s", [username])
            sender_row = cursor.fetchone()
            if not sender_row:
                return JsonResponse({"error": "Friend user does not exist."}, status=404)

            sender_id = sender_row[0]

        # Update the friend request to "accepted"
        try:
            with connection.cursor() as cursor:
                # Update existing friend request
                cursor.execute(
                    """
                    UPDATE chat_userrelation
                    SET accepted = TRUE
                    WHERE user_id = %s AND friend_id = %s
                    """,
                    [sender_id, receiver_id]
                )

                # Add reverse relation (if it doesn't exist)
                cursor.execute(
                    """
                    INSERT INTO chat_userrelation (user_id, friend_id, accepted)
                    SELECT %s, %s, TRUE
                    WHERE NOT EXISTS (
                        SELECT 1 FROM chat_userrelation WHERE user_id = %s AND friend_id = %s
                    )
                    """,
                    [receiver_id, sender_id, receiver_id, sender_id]
                )

            return JsonResponse({"message": "Friend request accepted successfully."}, status=200)
        except Exception as e:
            logger.error(f"Error while accepting friend request: {str(e)}")
            return JsonResponse({"error": "An error occurred while accepting the friend request."}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)

@csrf_exempt
def add_friend(request, sender_id):
    if request.method == "POST":
        # Parse the request body to get the friend's username
        if request.content_type == "application/json":
            data = json.loads(request.body)
            username = data.get("username")
        else:
            username = request.POST.get("username")

        # Log the username being processed
        logger.info(f"Received friend request from user ID {sender_id} to username: {username}")

        # Verify sender exists
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM auth_user WHERE id = %s",
                [sender_id]
            )
            sender_row = cursor.fetchone()
            if not sender_row:
                return JsonResponse({"error": "Sender user does not exist."}, status=404)

        # Verify recipient exists
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM auth_user WHERE username = %s",
                [username]
            )
            friend_row = cursor.fetchone()
            if not friend_row:
                return JsonResponse({"error": "Friend user does not exist."}, status=404)

            friend_id = friend_row[0]

        # Insert the friend request
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO chat_userrelation (user_id, friend_id, accepted)
                    SELECT %s, %s, FALSE
                    WHERE NOT EXISTS (
                        SELECT 1 FROM chat_userrelation WHERE user_id = %s AND friend_id = %s
                    )
                    """,
                    [sender_id, friend_id, sender_id, friend_id]
                )

            return JsonResponse({"message": "Friend request sent successfully."}, status=201)
        except Exception as e:
            logger.error(f"Error while sending friend request: {str(e)}")
            return JsonResponse({"error": "An error occurred while sending the friend request."}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)

@csrf_exempt
def search(request):
    if request.method == "GET":
        query = request.GET.get("q", "").strip()  # Extract the search query from the URL
        if query:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, username, email, first_name, last_name
                    FROM auth_user
                    WHERE username ILIKE %s OR email ILIKE %s OR first_name ILIKE %s OR last_name ILIKE %s
                    """,
                    [f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"]
                )
                users = cursor.fetchall()

            if users:
                users_list = [
                    {
                        "id": user[0],
                        "username": user[1],
                        "email": user[2],
                        "first_name": user[3],
                        "last_name": user[4],
                    }
                    for user in users
                ]
                return JsonResponse({"query": query, "results": users_list}, status=200)
            else:
                return JsonResponse({"query": query, "message": "No users found."}, status=404)

    return JsonResponse({"error": "Invalid request method."}, status=405)
