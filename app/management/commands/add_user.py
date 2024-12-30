from django.contrib.auth.hashers import make_password
from django.db import connection

def add_user():
    email = "user@example.com"
    password_hash = make_password("mypassword")

    with connection.cursor() as cursor:
        cursor.execute(
            'INSERT INTO "User" ("email", "password_hash", "firstName", "lastName") VALUES (%s, %s, %s, %s);',
            (email, password_hash, "John", "Doe")
        )
    print("User added successfully")


add_user()
