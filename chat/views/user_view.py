import os

from django.http import JsonResponse
from django.db import transaction
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
import json
import logging
import psycopg

logger = logging.getLogger(__name__)
# Fonction de connection a la base de donnée
def get_db_connection():
    try:
        connection = psycopg.connect(
            host=settings.DATABASES['default']['HOST'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            dbname=settings.DATABASES['default']['NAME'],
              # Ensures SSL connection to Neon database
        )
        return connection
    except Exception as e:
        raise Exception(f"erreur de connection a la base de donnée: {str(e)}")
@csrf_exempt
def artisan_signup(request):
    if request.method == "POST":
        try:
            # Vérifiez si le corps de la requête est vide ou mal formé
            if not request.body:
                return JsonResponse({"success": False, "message": "Le corps de la requête est vide."}, status=400)

            # Parse JSON payload
            if request.content_type == "application/json":
                data = json.loads(request.body.decode("utf-8"))
            else:
                data = request.POST.dict()  # Use form data instead

            
            # Extract data from request
            first_name = data.get("first_name")
            last_name = data.get("last_name")
            email = data.get("email")
            password1 = data.get("password1")
            password2 = data.get("password2")
            phone_number = data.get("phone_number", None)  # Optional
            is_certified = data.get("is_certified", False)
            is_assured = data.get("is_assured", False)
            job = data.get("job")

            # Files must be handled separately (Postman will send files as multipart form-data)
            certification_files = request.FILES.getlist("certification_files") if is_certified else []
            insurance_files = request.FILES.getlist("insurance_files") if is_assured else []

            if is_certified == True and not certification_files:
                return JsonResponse({"success":False, "message":"vous devez ajouter un justificatif de certification"})
            
            if is_assured == True and not insurance_files:
                return JsonResponse({"success":False, "message":"vous devez ajouter un justificatif d'assurance"})

            # Validate required fields
            if not first_name or not last_name or not email or not password1 or not password2 :
                return JsonResponse({"success": False, "message": "Tous les champs obligatoires doivent être remplis."}, status=400)

            # Validate password match
            if password1 != password2:
                return JsonResponse({"success": False, "message": "Les mots de passe ne correspondent pas."}, status=400)

            # Hash password
            hashed_password = make_password(password1)

            # Start database operations
            connection = get_db_connection()
            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        # Check email uniqueness
                        cursor.execute(
                            "SELECT id FROM auth_user WHERE email = %s",
                            [email]
                        )
                        if cursor.fetchone():
                            return JsonResponse({"success": False, "message": "Cet email est déjà utilisé."}, status=400)

                        # Insert artisan data into auth_user table
                        cursor.execute(
                            """
                            INSERT INTO auth_user (username, first_name, last_name, email, password, phoneNumber, isCertified, isAssured, is_staff, job)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                            RETURNING id
                            """,
                            [email, first_name, last_name, email, hashed_password, phone_number, is_certified, is_assured, job]
                        )
                        artisan_id = cursor.fetchone()[0]


                    # Handle certification files
                    if is_certified and certification_files:
                        save_files(certification_files, artisan_id, "certificat", connection)

                    # Handle insurance files
                    if is_assured and insurance_files:
                        save_files(insurance_files, artisan_id, "assurance", connection)

                
                # Success response
                return JsonResponse({"success": True, "message": "Votre demande a été envoyée avec succès.", "artisan_id": artisan_id}, status=201)

            finally:
                # Close database connection
                connection.commit()
                connection.close()

        except Exception as e:
            # Error response
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)

    # If not POST, return error
    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)

@csrf_exempt
def client_signup(request):
    if request.method == "POST":
        try:
            # Vérifiez si le corps de la requête est vide ou mal formé
            if not request.body:
                return JsonResponse({"success": False, "message": "Le corps de la requête est vide."}, status=400)

            # Parse JSON payload
            if request.content_type == "application/json":
                data = json.loads(request.body.decode("utf-8"))
            else:
                data = request.POST.dict()  # Use form data instead

            
            # Extract data from request
            first_name = data.get("first_name")
            last_name = data.get("last_name")
            email = data.get("email")
            password1 = data.get("password1")
            password2 = data.get("password2")
            phone_number = data.get("phone_number", None)  # Optional



            # Validate required fields
            if not first_name or not last_name or not email or not password1 or not password2 :
                return JsonResponse({"success": False, "message": "Tous les champs obligatoires doivent être remplis."}, status=400)

            # Validate password match
            if password1 != password2:
                return JsonResponse({"success": False, "message": "Les mots de passe ne correspondent pas."}, status=400)

            # Hash password
            hashed_password = make_password(password1)

            # Start database operations
            connection = get_db_connection()
            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        # Check email uniqueness
                        cursor.execute(
                            "SELECT id FROM auth_user WHERE email = %s",
                            [email]
                        )
                        if cursor.fetchone():
                            return JsonResponse({"success": False, "message": "Cet email est déjà utilisé."}, status=400)

                        # Insert artisan data into auth_user table
                        cursor.execute(
                            """
                            INSERT INTO auth_user (username, first_name, last_name, email, password, phoneNumber)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING id
                            """,
                            [email, first_name, last_name, email, hashed_password, phone_number]
                        )
                        client_id = cursor.fetchone()[0]

                
                # Success response
                return JsonResponse({"success": True, "message": "Votre compte a été crée avec succès.", "client_id": client_id}, status=201)

            finally:
                # Close database connection
                connection.commit()
                connection.close()

        except Exception as e:
            # Error response
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)

    # If not POST, return error
    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)
@csrf_exempt
def user_login(request):
    if request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Vous êtes déjà connecté."}, status=200)

    if request.method == "POST":
        try:
            # Parse JSON payload
            if not request.body:
                return JsonResponse({"success": False, "message": "Le corps de la requête est vide."}, status=400)

            data = json.loads(request.body.decode("utf-8"))

            # Extract email/username and password
            email_or_username = data.get("email_or_username")
            password = data.get("password")

            # Validate input
            if not email_or_username or not password:
                return JsonResponse({"success": False, "message": "L'email/username et le mot de passe sont requis."}, status=400)

            # Database connection
            connection = get_db_connection()

            try:
                with connection.cursor() as cursor:
                    # Query user by email or username
                    cursor.execute(
                        "SELECT id, username, email, password, is_superuser, is_staff FROM auth_user WHERE email = %s OR username = %s",
                        [email_or_username, email_or_username]
                    )
                    user_row = cursor.fetchone()

                    if not user_row:
                        return JsonResponse({"success": False, "message": "L'utilisateur est introuvable. Veuillez vérifier votre email/username."}, status=404)

                    # Extract user data
                    user_id, username, email, db_password, is_superuser, is_staff = user_row

                    # Validate password
                    if not check_password(password, db_password):
                        return JsonResponse({"success": False, "message": "Le mot de passe est incorrect."}, status=400)

            finally:
                connection.close()

            # Log the user in by creating a custom user-like object
            request.session['user_id'] = user_id
            request.session['username'] = username
            request.session['email'] = email
            request.session['is_authenticated'] = True
            request.session['is_superuser'] = is_superuser
            request.session['is_staff'] = is_staff

            return JsonResponse({"success": True, "message": "Vous avez été connecté avec succès."}, status=200)

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)

@csrf_exempt
def user_logout(request):
    if request.method == "POST":
        # Clear the session
        request.session.flush()
        return JsonResponse({"success": True, "message": "Vous avez été déconnecté avec succès."}, status=200)

    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)





@csrf_exempt
def validate_artisan(request, artisan_id):
    # Check if the user is authenticated via session
    if not request.session.get('is_authenticated'):
        return JsonResponse({"success": False, "message": "Vous devez être connecté pour valider un artisan."}, status=403)

    # Check if the user is a superuser
    if not request.session.get('is_superuser', False):
        return JsonResponse({"success": False, "message": "Vous n'avez pas les droits nécessaires pour valider cet artisan."}, status=403)

    if request.method == "POST":
        try:
            # Query to check if the artisan exists and is not already validated
            connection = get_db_connection()

            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id, is_validated
                        FROM auth_user
                        WHERE id = %s
                        """,
                        [artisan_id]
                    )
                    artisan_row = cursor.fetchone()

                    if not artisan_row:
                        return JsonResponse({"success": False, "message": "Aucun artisan trouvé avec cet ID."}, status=404)

                    artisan_id, is_validated = artisan_row

                    # Check if the artisan is already validated
                    if is_validated:
                        return JsonResponse({"success": False, "message": "Cet artisan est déjà validé."}, status=400)

                    # Update artisan's validation status
                    cursor.execute(
                        """
                        UPDATE auth_user
                        SET is_validated = TRUE
                        WHERE id = %s
                        """,
                        [artisan_id]
                    )
                    connection.commit()

                return JsonResponse({"success": True, "message": "L'artisan a été validé avec succès."}, status=200)

            finally:
                connection.close()

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)
def save_files(files, artisan_id, table_name, connection):
    upload_path = os.path.join(settings.MEDIA_ROOT, table_name)
    os.makedirs(upload_path, exist_ok=True)

    with connection.cursor() as cursor:
        for file in files:
            fs = FileSystemStorage(location=upload_path)
            filename = fs.save(file.name, file)
            file_path = os.path.join(upload_path, filename)

            column_name = "assurance" if table_name == "assurance" else "certificat_joint"

            # Save file path to the appropriate table
            cursor.execute(
                f"""
                INSERT INTO {table_name} (id, {column_name})
                VALUES (%s, %s)
                """,
                [artisan_id, file_path]
            )

@csrf_exempt
def EditProfile(request):
    connection = get_db_connection()
    if not request.user.is_authenticated:
        logger.warning("Bypassing authentication for testing purposes.")
        request.user = User.objects.get(username="karim")  # Default to a specific user for testing
    
    success_message = None
    error_message = None

    if request.method == "POST":
        new_email = request.POST.get("email")
        new_username = request.POST.get("username")

        # Initialize flags
        username_exists = False
        email_exists = False

        # Check if the new username is already taken
        if new_username and new_username != request.user.username:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id FROM auth_user WHERE username = %s",
                        [new_username]
                    )
                    username_exists = cursor.fetchone() is not None
                    if username_exists:
                        logger.info(f"Username '{new_username}' already exists.")
            except Exception as e:
                error_message = "An error occurred while checking username availability."
                logger.error(f"EditProfile Username Check Error: {e}")

        if username_exists:
            error_message = "Username already exists. Please choose a different one."

        # Check if the new email is already taken
        if not error_message and new_email != request.user.email:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id FROM auth_user WHERE email = %s",
                        [new_email]
                    )
                    email_exists = cursor.fetchone() is not None
                    if email_exists:
                        logger.info(f"Email '{new_email}' already exists.")
            except Exception as e:
                error_message = "An error occurred while checking email availability."
                logger.error(f"EditProfile Email Check Error: {e}")

        if email_exists:
            error_message = "Email address already associated with another account. Please choose a different one."

        # If no errors, proceed to update
        if not error_message and new_username:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE auth_user
                        SET username = %s, email = %s
                        WHERE id = %s
                        """,
                        [new_username, new_email, request.user.id]
                    )
                connection.commit()  # Ensure commit after the update
                success_message = "Profile updated successfully."

                # Manually update the request.user object to reflect changes
                request.user.username = new_username
                request.user.email = new_email

            except Exception as e:
                error_message = "An error occurred while updating your profile."
                logger.error(f"EditProfile Update Error: {e}")

    # Return JSON response
    response_data = {
        "success": error_message is None,
        "message": success_message or error_message,
    }

    return JsonResponse(response_data)
