from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import connection
import logging
import json

logger = logging.getLogger(__name__)


def userprofile(request, username):
    if username == request.user.username:
        return JsonResponse({"redirect": "home"}, status=302)  # Redirect to home if viewing own profile

    friend_dict = {
        "accepted": False,
        "name": ""
    }
    send_request = False
    not_accepted = False
    me_not_accepted = False
    is_friend = False

    try:
        # Fetch the user whose profile is being viewed
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, email FROM auth_user WHERE username = %s",
                [username]
            )
            user_row = cursor.fetchone()
            if not user_row:
                return JsonResponse({"error": "User does not exist."}, status=404)
            profile_user_id = user_row[0]
            profile_user_email = user_row[1]

        # Fetch all UserRelations once to optimize performance
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, friend_id, accepted FROM chat_userrelation"
            )
            friends_data = cursor.fetchall()

        # Iterate through UserRelations to find relevant relations
        for relation in friends_data:
            relation_user_id, relation_friend_id, relation_accepted = relation
            if relation_user_id == request.user.id and relation_friend_id == profile_user_id:
                friend_dict = {
                    "name": username,
                    "accepted": relation_accepted,
                }
            elif relation_friend_id == request.user.id and relation_user_id == profile_user_id:
                if not relation_accepted:
                    me_not_accepted = True

    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    # Determine the state of the friendship
    if friend_dict["name"] == "":
        if me_not_accepted:
            send_request = False  # Optionally, handle pending requests
        else:
            send_request = True  # Allow sending a friend request
    elif not friend_dict["accepted"]:
        not_accepted = True  # Friend request is pending
    else:
        is_friend = True  # Users are friends

    user_details = {
        "username": username,
        "email": profile_user_email,
        "send_request": send_request,
        "not_accepted": not_accepted,
        "is_friend": is_friend,
        "me_not_accepted": me_not_accepted,
    }

    return JsonResponse({"user_details": user_details}, status=200)



def HomePage(request):
    if not request.user.is_authenticated:
        #logger.warning("Bypassing authentication for testing purposes.")
        #request.user = User.objects.get(username="karim") 
        return JsonResponse({"error": "You must be logged in to perform this action."}, status=403)   
            
    
    friends_list = []
    request_list = []

    try:
        # Fetch all UserRelations once to optimize performance
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, friend_id, accepted FROM chat_userrelation"
            )
            friends_data = cursor.fetchall()

        for relation in friends_data:
            relation_user_id, relation_friend_id, relation_accepted = relation
            if relation_user_id == request.user.id:
                # Current user has sent a friend request
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT username FROM auth_user WHERE id = %s",
                        [relation_friend_id]
                    )
                    friend_username_row = cursor.fetchone()
                    if friend_username_row:
                        friend_username = friend_username_row[0]
                        friends_list.append({
                            "username": friend_username,
                            "accepted": relation_accepted
                        })
            elif relation_friend_id == request.user.id and not relation_accepted:
                # Current user has received a friend request
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT username FROM auth_user WHERE id = %s",
                        [relation_user_id]
                    )
                    friend_username_row = cursor.fetchone()
                    if friend_username_row:
                        friend_username = friend_username_row[0]
                        request_list.append({
                            "username": friend_username
                        })

    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    data = {
        "email": request.user.email,
        "username": request.user.username,
        "friends": friends_list,
        "requests": request_list,
    }

    return JsonResponse({"data": data}, status=200)
