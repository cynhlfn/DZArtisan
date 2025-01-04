import os
import psycopg
from django.http import JsonResponse
from django.db import transaction
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from math import ceil
from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.models import User

from django.contrib.auth.hashers import check_password

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
import json

from datetime import datetime, timedelta
from django.utils.timezone import now  # Ensures compatibility with timezone-aware databases

import cloudinary.uploader

import cloudinary


cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


import logging


logger = logging.getLogger(__name__)


# Fonction de connection a la base de donnée
def get_db_connection():
    try:
        connection = psycopg.connect(
            host=settings.DATABASES['default']['HOST'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            dbname=settings.DATABASES['default']['NAME'],
            sslmode='require'  # Ensures SSL connection to Neon database
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
            job_name = data.get("job")

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
                            "SELECT idMetier FROM metier WHERE Nmetier = %s",
                            [job_name]
                        )

                        metier_row = cursor.fetchone()
                        if not metier_row:
                            return JsonResponse({"success": False, "message": "Le métier spécifié est invalide."}, status=400)
                        
                        id_metier = metier_row[0]

                        cursor.execute(
                            "SELECT id FROM auth_user WHERE email = %s",
                            [email]
                        )
                        if cursor.fetchone():
                            return JsonResponse({"success": False, "message": "Cet email est déjà utilisé."}, status=400)

                        # Insert artisan data into auth_user table
                        
                        cursor.execute(
                            """
                            INSERT INTO auth_user (username, first_name, last_name, email, password, phoneNumber, isCertified, isAssured, is_staff, idMetier)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s)
                            RETURNING id
                            """,
                            [email, first_name, last_name, email, hashed_password, phone_number, is_certified, is_assured, id_metier]
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
                        "SELECT id, username, email, password, is_superuser, is_staff, first_name, last_name, phoneNumber, pfp FROM auth_user WHERE email = %s OR username = %s",
                        [email_or_username, email_or_username]
                    )
                    user_row = cursor.fetchone()

                    if not user_row:
                        return JsonResponse({"success": False, "message": "L'utilisateur est introuvable. Veuillez vérifier votre email/username."}, status=404)

                    # Extract user data
                    (
                    user_id, username, email, db_password, is_superuser, is_staff , first_name, last_name, phone_number, pfp
                    ) = user_row

                    # Validate password
                    if not check_password(password, db_password):
                        return JsonResponse({"success": False, "message": "Le mot de passe est incorrect."}, status=400)
                    
                    # Update last_login timestamp
                    cursor.execute(
                        "UPDATE auth_user SET last_login = %s WHERE id = %s",
                        [now(), user_id]
                    )

            finally:
                connection.commit()
                connection.close()

            # Log the user in by creating a custom user-like object
            request.session['user_id'] = user_id
            request.session['username'] = username
            request.session['email'] = email
            request.session['is_authenticated'] = True
            request.session['is_superuser'] = is_superuser
            request.session['is_staff'] = is_staff


            role = "admin" if is_superuser else "artisan" if is_staff else "client"

            
            response_data = {
                "idUser":user_id,
                "role": role,
                "firstName": first_name,
                "lastName": last_name,
                "email": email,
                "phoneNumber": phone_number,
                "pfpLink": pfp
            }


            return JsonResponse({"success": True, "message": "Vous avez été connecté avec succès.", "data": response_data }, status=200)

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
    """
    Save files to Cloudinary and store their URLs in the database.
    :param files: List of uploaded files
    :param artisan_id: ID of the artisan
    :param table_name: Name of the table to save data into ('certificat' or 'assurance')
    :param connection: Active database connection
    """
    with connection.cursor() as cursor:
        for file in files:
            # Upload file to Cloudinary
            try:
                upload_result = cloudinary.uploader.upload(file)
                file_url = upload_result['secure_url']  # Get the URL of the uploaded file

                # Determine the column name based on the table
                column_name = "assurance" if table_name == "assurance" else "certificat_joint"

                # Save file URL to the appropriate table
                cursor.execute(
                    f"""
                    INSERT INTO {table_name} (id_user, {column_name})
                    VALUES (%s, %s)
                    """,
                    [artisan_id, file_url]
                )
            except Exception as e:
                print(f"Error uploading file to Cloudinary: {str(e)}")
                raise

@csrf_exempt
def EditProfile(request):
    connection = get_db_connection()
    if not request.user.is_authenticated:
        #logger.warning("Bypassing authentication for testing purposes.")
        #request.user = User.objects.get(username="karim") 
        return JsonResponse({"error": "You must be logged in to perform this action."}, status=403)
    
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


@csrf_exempt
def email_taken(request):
    if request.method == "POST":
        try:
            if not request.body:
                return JsonResponse({"success": False, "message":"le corps de la requête est vide."}, status=400)
            
            if request.content_type == "application/json":
                data = json.loads(request.body.decode("utf-8"))
            else:
                data = request.POST.dict()

            email = data.get("email")

            connection = get_db_connection()
            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT id FROM auth_user WHERE email = %s",
                            [email]
                        )
                        if cursor.fetchone():
                            is_used = True
                        else:
                            is_used = False
                        
                return JsonResponse({"is_used": is_used}, status=201)
            finally:
                connection.close()
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)

 # Ensure only superusers can access
def admin_dashboard(request):
    # Bypass for testing purposes
    if not request.user.is_authenticated:
        #logger.warning("Bypassing authentication for testing purposes.")
        #from django.contrib.auth.models import User
        #request.user = User.objects.get(username="admin@example.com")
        return JsonResponse({"error": "You must be logged in to perform this action."}, status=403)      

    try:
        connection = get_db_connection()  # Use your custom database connection
        try:
            with connection.cursor() as cursor:
                # Total Clients
                cursor.execute(
                    "SELECT COUNT(*) FROM auth_user WHERE is_staff = FALSE AND is_superuser = FALSE"
                )
                total_clients = cursor.fetchone()[0]

                # Total Artisans
                cursor.execute(
                    "SELECT COUNT(*) FROM auth_user WHERE is_staff = TRUE AND is_superuser = FALSE"
                )
                total_artisans = cursor.fetchone()[0]

                # Total Deals
                cursor.execute(
                    "SELECT COUNT(*) FROM demande_de_devis"
                )
                total_deals = cursor.fetchone()[0]

                # Percentage Calculations
                total_users = total_clients + total_artisans
                artisan_percentage = (
                    (total_artisans / total_users) * 100 if total_users > 0 else 0
                )
                client_percentage = (
                    (total_clients / total_users) * 100 if total_users > 0 else 0
                )

                # Recent Undone Tasks (Last 5)
                cursor.execute(
                    """
                    SELECT idTache, titre, description 
                    FROM tache_admin 
                    WHERE etat != 'fait' 
                    ORDER BY idTache DESC 
                    LIMIT 5
                    """
                )
                recent_taches = [
                    {"id": str(row[0]), "title": row[1], "description": row[2]}
                    for row in cursor.fetchall()
                ]

                # Recent Demands with is_validated = False (Last 5)
                cursor.execute(
                    """
                    SELECT u.first_name, u.last_name, d.id_demande 
                    FROM demande_de_devis d
                    INNER JOIN auth_user u ON d.id_user = u.id
                    WHERE u.is_validated = FALSE
                    ORDER BY d.id_demande DESC 
                    LIMIT 5
                    """
                )
                recent_demandes = [
                    {"firstName": row[0], "lastName": row[1], "id": str(row[2])}
                    for row in cursor.fetchall()
                ]

                # Visitors Data (Last 7 days)
                cursor.execute(
                    """
                    SELECT DATE(date_joined) AS date, COUNT(*) AS visits
                    FROM auth_user
                    WHERE date_joined >= %s
                    GROUP BY DATE(date_joined)
                    ORDER BY DATE(date_joined) DESC
                    LIMIT 7
                    """,
                    [datetime.now() - timedelta(days=7)],
                )
                visitors = [
                    {"date": str(row[0]), "visits": row[1]}
                    for row in cursor.fetchall()
                ]

            # Response Data
            response_data = {
                "totalClients": total_clients,
                "totalArtisans": total_artisans,
                "totalDeals": total_deals,
                "artisanPercentage": round(artisan_percentage, 2),
                "clientPercentage": round(client_percentage, 2),
                "recentTaches": recent_taches,
                "recentDemandes": recent_demandes,
                "visitors": visitors,
            }

            return JsonResponse(response_data, status=200)
        finally:
            connection.close()  # Ensure the connection is closed
    except Exception as e:
        logger.error(f"Error in superuser_dashboard: {e}")
        return JsonResponse({"success": False, "message": f"An error occurred: {str(e)}"}, status=500)

@csrf_exempt
def search_artisans_by_job(request):
    if request.method == "POST":
        try:
            # Check if the request body is empty
            if not request.body:
                return JsonResponse({"success": False, "message": "Request body is empty."}, status=400)

            # Parse JSON payload
            data = json.loads(request.body.decode("utf-8"))
            job_name = data.get("job")

            # Validate input
            if not job_name:
                return JsonResponse({"success": False, "message": "Job field is required."}, status=400)

            # Connect to the database
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    # Query to find artisans based on partial match of the job name
                    cursor.execute(
                        """
                        SELECT u.first_name || ' ' || u.last_name AS artisanName,
                               u.pfp AS artisanPfpLink,
                               c.certificat_joint AS artisanPortfolio
                        FROM auth_user u
                        LEFT JOIN certificat c ON u.id = c.id_user
                        INNER JOIN metier m ON u.idMetier = m.idMetier
                        WHERE m.Nmetier ILIKE %s AND u.isCertified = TRUE AND u.is_validated = TRUE
                        """,
                        [f"%{job_name}%"]  # Use % for partial matching
                    )

                    # Fetch results
                    artisans = []
                    rows = cursor.fetchall()
                    for row in rows:
                        artisan_name, pfp_link, portfolio_link = row
                        artisans.append({
                            "artisanName": artisan_name,
                            "artisanPfpLink": pfp_link or "",  # Default to empty string if no profile picture
                            "artisanPortfolio": portfolio_link or ""  # Default to empty string if no portfolio
                        })

                    # Return results
                    return JsonResponse({"artisans": artisans}, status=200)

            finally:
                connection.close()

        except Exception as e:
            return JsonResponse({"success": False, "message": f"An error occurred: {str(e)}"}, status=500)

    # Handle invalid request methods
    return JsonResponse({"success": False, "message": "Method not allowed."}, status=405)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from math import ceil

@csrf_exempt
def admin_clients(request):
    if request.method == "GET":
        try:
            # Get page number from query parameters
            page = int(request.GET.get("page", 1))  # Default to page 1 if not provided
            clients_per_page = 5  # Number of clients per page

            # Connect to the database
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    # Get total number of clients
                    cursor.execute(
                        "SELECT COUNT(*) FROM auth_user WHERE is_staff = FALSE AND is_superuser = FALSE"
                    )
                    total_clients = cursor.fetchone()[0]

                    # Calculate total pages
                    total_pages = ceil(total_clients / clients_per_page)

                    # Validate page number
                    if page < 1 or page > total_pages:
                        return JsonResponse(
                            {"success": False, "message": "Invalid page number."},
                            status=400,
                        )

                    # Fetch clients for the current page
                    offset = (page - 1) * clients_per_page
                    cursor.execute(
                        """
                        SELECT first_name, last_name, id, email, phoneNumber, 
                               CASE 
                                   WHEN pfp ILIKE '%%female%%' THEN 'Female'
                                   WHEN pfp ILIKE '%%male%%' THEN 'Male'
                                   ELSE 'Unknown' 
                               END AS gender
                        FROM auth_user
                        WHERE is_staff = FALSE AND is_superuser = FALSE
                        ORDER BY id
                        LIMIT %s OFFSET %s
                        """,
                        [clients_per_page, offset],
                    )
                    rows = cursor.fetchall()

                    # Format the clients data
                    clients = [
                        {
                            "firstName": row[0],
                            "lastName": row[1],
                            "id": row[2],
                            "email": row[3],
                            "phoneNumber": row[4],
                            "gender": row[5],
                        }
                        for row in rows
                    ]

                    # Response with pagination metadata
                    response_data = {
                        "clients": clients,
                        "pagination": {
                            "currentPage": page,
                            "totalPages": total_pages,
                            "totalClients": total_clients,
                        },
                    }
                    return JsonResponse(response_data, status=200)
            finally:
                connection.close()

        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"An error occurred: {str(e)}"},
                status=500,
            )

    return JsonResponse({"success": False, "message": "Method not allowed."}, status=405)

@csrf_exempt
def delete_client(request):
    if request.method == "POST":
        try:
            # Parse the request body to get the client ID
            data = json.loads(request.body.decode("utf-8"))
            client_id = data.get("id")

            # Validate that 'id' is provided
            if not client_id:
                return JsonResponse({"success": False, "message": "Client ID is required."}, status=400)

            # Connect to the database
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    # Check if the client exists
                    cursor.execute(
                        "SELECT id FROM auth_user WHERE id = %s AND is_staff = FALSE AND is_superuser = FALSE",
                        [client_id]
                    )
                    if not cursor.fetchone():
                        return JsonResponse({"success": False, "message": "Client not found."}, status=404)

                    # Delete the client
                    cursor.execute(
                        "DELETE FROM auth_user WHERE id = %s AND is_staff = FALSE AND is_superuser = FALSE",
                        [client_id]
                    )
                    connection.commit()

                    # Success response
                    return JsonResponse({"success": True, "message": "Client deleted successfully."}, status=200)

            finally:
                connection.close()

        except Exception as e:
            # Handle errors
            return JsonResponse({"success": False, "message": f"An error occurred: {str(e)}"}, status=500)

    # Handle invalid HTTP methods
    return JsonResponse({"success": False, "message": "Method not allowed."}, status=405)

@csrf_exempt
def admin_artisans(request):
    if request.method == "GET":
        try:
            # Get page number from query parameters
            page = int(request.GET.get("page", 1))  # Default to page 1
            artisans_per_page = 5  # Number of artisans per page

            # Connect to the database
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    # Get total number of artisans
                    cursor.execute(
                        "SELECT COUNT(*) FROM auth_user WHERE is_staff = TRUE AND is_superuser = FALSE"
                    )
                    total_artisans = cursor.fetchone()[0]

                    # Calculate total pages
                    total_pages = ceil(total_artisans / artisans_per_page)

                    # Validate page number
                    if page < 1 or page > total_pages:
                        return JsonResponse(
                            {"success": False, "message": "Invalid page number."},
                            status=400,
                        )

                    # Fetch artisans for the current page
                    offset = (page - 1) * artisans_per_page
                    cursor.execute(
                        """
                        SELECT first_name, last_name, id, email, phoneNumber, 
                               CASE 
                                   WHEN isCertified THEN 'Certified' 
                                   ELSE 'Not Certified' 
                               END AS status
                        FROM auth_user
                        WHERE is_staff = TRUE AND is_superuser = FALSE
                        ORDER BY id
                        LIMIT %s OFFSET %s
                        """,
                        [artisans_per_page, offset],
                    )
                    rows = cursor.fetchall()

                    # Format the artisans data
                    artisans = [
                        {
                            "firstName": row[0],
                            "lastName": row[1],
                            "id": str(row[2]),
                            "email": row[3],
                            "phoneNumber": row[4],
                            "status": row[5],
                        }
                        for row in rows
                    ]

                    # Response with pagination metadata
                    response_data = {
                        "artisans": artisans,
                        "pagination": {
                            "currentPage": page,
                            "totalPages": total_pages,
                            "totalArtisans": total_artisans,
                        },
                    }
                    return JsonResponse(response_data, status=200)
            finally:
                connection.close()

        except Exception as e:
            # Handle errors
            return JsonResponse(
                {"success": False, "message": f"An error occurred: {str(e)}"},
                status=500,
            )

    # Handle invalid HTTP methods
    return JsonResponse({"success": False, "message": "Method not allowed."}, status=405)

@csrf_exempt
def delete_artisan(request):
    if request.method == "POST":
        try:
            # Parse the request body to get the artisan ID
            data = json.loads(request.body.decode("utf-8"))
            artisan_id = data.get("id")

            # Validate that 'id' is provided
            if not artisan_id:
                return JsonResponse({"success": False, "message": "Artisan ID is required."}, status=400)

            # Connect to the database
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    # Check if the artisan exists
                    cursor.execute(
                        "SELECT id FROM auth_user WHERE id = %s AND is_staff = TRUE AND is_superuser = FALSE",
                        [artisan_id]
                    )
                    if not cursor.fetchone():
                        return JsonResponse({"success": False, "message": "Artisan not found."}, status=404)

                    # Delete the artisan
                    cursor.execute(
                        "DELETE FROM auth_user WHERE id = %s AND is_staff = TRUE AND is_superuser = FALSE",
                        [artisan_id]
                    )
                    connection.commit()

                    # Success response
                    return JsonResponse({"success": True, "message": "Artisan deleted successfully."}, status=200)

            finally:
                connection.close()

        except Exception as e:
            # Handle errors
            return JsonResponse({"success": False, "message": f"An error occurred: {str(e)}"}, status=500)

    # Handle invalid HTTP methods
    return JsonResponse({"success": False, "message": "Method not allowed."}, status=405)