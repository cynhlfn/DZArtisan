import os
import psycopg
from django.db import transaction
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import json
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from math import ceil
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from math import ceil
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
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

            session_id = request.session.session_key

            request.session.save()

            if not session_id:
                request.session.create()  # Create session if it does not exist
                session_id = request.session.session_key

            role = "admin" if is_superuser else "artisan" if is_staff else "client"

            
            response_data = {
                "idUser":user_id,
                "role": role,
                "firstName": first_name,
                "lastName": last_name,
                "email": email,
                "phoneNumber": phone_number,
                "pfpLink": pfp,
                "sessionID": session_id,
            }


            return JsonResponse({
                "success": True,
                "message": "Vous avez été connecté avec succès.",
                "data": response_data
                }, status=200)

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

@csrf_exempt
def refuser_artisan(request, artisan_id):
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
                        DELETE FROM auth_user
                        WHERE id = %s
                        """,
                        [artisan_id]
                    )
                    connection.commit()

                return JsonResponse({"success": True, "message": "L'artisan a été supprimer avec success."}, status=200)

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

@csrf_exempt
def admin_dashboard(request):
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

                # Visitors Data (Current Month)
                cursor.execute(
                    """
                    SELECT DATE(date_joined) AS date, COUNT(*) AS visits
                    FROM auth_user
                    WHERE date_joined >= %s AND date_joined < %s
                    GROUP BY DATE(date_joined)
                    ORDER BY DATE(date_joined) ASC
                    """,
                    [datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0),  # Start of current month
                    (datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=32)).replace(day=1)],  # Start of next month
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

@csrf_exempt
def edit_password(request):      
    if request.method == "POST":
        try:
            # Check if the user is authenticated via session
            if not request.session.get('is_authenticated'):
                return JsonResponse({"success": False, "message": "Vous devez être connecté pour modifier votre mot de passe."}, status=403)

            # Parse the request body
            data = json.loads(request.body.decode("utf-8"))
            old_password = data.get("oldPassword")
            new_password = data.get("newPassword")

            # Validate input
            if not old_password or not new_password:
                return JsonResponse({"success": False, "message": "Les champs 'oldPassword' et 'newPassword' sont requis."}, status=400)

            # Get user ID from session
            user_id = request.session.get('user_id')
            if not user_id:
                return JsonResponse({"success": False, "message": "Utilisateur non trouvé dans la session."}, status=404)

            # Connect to the database
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    # Retrieve user's current password from the database
                    cursor.execute(
                        "SELECT password FROM auth_user WHERE id = %s",
                        [user_id]
                    )
                    user_row = cursor.fetchone()
                    if not user_row:
                        return JsonResponse({"success": False, "message": "Utilisateur introuvable."}, status=404)

                    db_password = user_row[0]

                    # Verify the old password
                    if not check_password(old_password, db_password):
                        return JsonResponse({"success": False, "message": "L'ancien mot de passe est incorrect."}, status=400)

                    # Hash the new password
                    hashed_new_password = make_password(new_password)

                    # Update the user's password in the database
                    cursor.execute(
                        "UPDATE auth_user SET password = %s WHERE id = %s",
                        [hashed_new_password, user_id]
                    )
                    connection.commit()

                # Return success response
                return JsonResponse({"success": True, "message": "Mot de passe modifié avec succès."}, status=200)

            finally:
                connection.close()

        except Exception as e:
            # Handle any unexpected errors
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)

    # Handle non-POST requests
    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)

@csrf_exempt
def edit_client_profile(request):
    if request.method == "POST":
        try:
            # Parse the request body
            if not request.body:
                return JsonResponse({"success": False, "message": "Le corps de la requête est vide."}, status=400)

            data = json.loads(request.body.decode("utf-8"))

            # Extract client ID and fields to update
            client_id = data.get("id")
            first_name = data.get("firstName", "").strip()
            last_name = data.get("LastName", "").strip()
            phone_number = data.get("PhoneNumber", "").strip()
            email = data.get("email", "").strip()
            pfp = data.get("pfp", "").strip()  # Profile picture URL or Base64

            # Validate client ID
            if not client_id:
                return JsonResponse({"success": False, "message": "Client ID is required."}, status=400)

            # Prepare fields for update
            fields_to_update = []
            params = []

            if first_name:
                fields_to_update.append("first_name = %s")
                params.append(first_name)
            if last_name:
                fields_to_update.append("last_name = %s")
                params.append(last_name)
            if phone_number:
                fields_to_update.append("phoneNumber = %s")
                params.append(phone_number)
            if email:
                fields_to_update.append("email = %s")
                params.append(email)

            pfp_updated = False
            if pfp:
                fields_to_update.append("pfp = %s")
                params.append(pfp)
                pfp_updated = True

            # If no fields to update, return success message
            if not fields_to_update:
                return JsonResponse({"success": True, "message": "Aucune modification apportée."}, status=200)

            # Construct and execute the update query
            query = f"UPDATE auth_user SET {', '.join(fields_to_update)} WHERE id = %s"
            params.append(client_id)

            # Database connection
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    # Execute the update query
                    cursor.execute(query, params)

                connection.commit()

                # Prepare the response
                response = {"success": True, "message": "Profil mis à jour avec succès."}
                if pfp_updated:
                    response["newPfp"] = pfp

                return JsonResponse(response, status=200)
            finally:
                connection.close()

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)


@csrf_exempt
def get_client_pannier(request, idClient): 

    if request.method == "GET":
        try:
            # Connect to the database
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    # Query to fetch unpaid offers for the given client
                    cursor.execute(
                        """
                        SELECT 
                            offre.id_offre AS id, 
                            CONCAT(auth_user.first_name, ' ', auth_user.last_name) AS artisanName, 
                            demande_de_devis.titre AS title, 
                            offre.offered_price AS price
                        FROM offre
                        INNER JOIN auth_user ON offre.id_artisan = auth_user.id
                        INNER JOIN demande_de_devis ON offre.id_demande = demande_de_devis.id_demande
                        WHERE demande_de_devis.id_user = %s AND offre.id_offre NOT IN (
                            SELECT id_offre FROM travail
                        )
                        """,
                        [idClient]
                    )

                    # Format the results
                    pannier = [
                        {
                            "id": row[0],
                            "artisanName": row[1],
                            "title": row[2],
                            "price": float(row[3]),
                        }
                        for row in cursor.fetchall()
                    ]

                # Return the pannier as JSON
                return JsonResponse({"pannier": pannier}, status=200)

            finally:
                # Ensure the connection is closed
                connection.close()

        except Exception as e:
            # Handle any errors
            return JsonResponse(
                {"success": False, "message": f"Une erreur s'est produite: {str(e)}"},
                status=500,
            )

    # Handle invalid HTTP methods
    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)


@csrf_exempt
def new_demand(request): 

    if request.method == "POST":
        try:
            # Check if the request body is empty
            if not request.body:
                return JsonResponse({"success": False, "message": "Le corps de la requête est vide."}, status=400)

            # Parse JSON payload
            data = json.loads(request.body.decode("utf-8"))

            # Extract data from request
            title = data.get("title", "").strip()
            job = data.get("job", "").strip()
            description = data.get("description", "").strip()
            estimated_price = data.get("estimatedPrice", None)
            image = data.get("image", None)  # Optional

            # Validate required fields
            if not title or not job or not description or estimated_price is None:
                return JsonResponse({"success": False, "message": "Tous les champs obligatoires doivent être remplis."}, status=400)

            # Ensure the user is authenticated via session
            client_id = request.session.get('user_id')
            if not client_id:
                return JsonResponse({"success": False, "message": "Vous devez être connecté pour créer une demande."}, status=403)

            # Connect to the database
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    # Ensure the job exists in the metier table
                    cursor.execute(
                        "SELECT idMetier FROM metier WHERE Nmetier = %s",
                        [job]
                    )
                    job_row = cursor.fetchone()
                    if not job_row:
                        return JsonResponse({"success": False, "message": "Le métier spécifié est invalide."}, status=400)

                    # Insert the new demand into demande_de_devis
                    cursor.execute(
                        """
                        INSERT INTO demande_de_devis (titre, description, delai_client, fait_le, metier, id_user)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id_demande
                        """,
                        [title, description, datetime.now().date(), datetime.now().date(), job, client_id]
                    )
                    demand_id = cursor.fetchone()[0]

                    # If an image is provided, save it to the image_exemple table
                    if image:
                        cursor.execute(
                            """
                            INSERT INTO image_exemple (id_demande, image)
                            VALUES (%s, %s)
                            """,
                            [demand_id, image]
                        )

                # Commit the transaction
                connection.commit()

                # Return a success response
                return JsonResponse({"success": True, "message": "Votre demande a été créée avec succès."}, status=201)

            finally:
                connection.close()

        except Exception as e:
            # Handle any exceptions
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)

    # If the method is not POST, return a method not allowed error
    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)

@csrf_exempt
def current_demands(request, id_client):

    if request.method == "GET":
        try:
            # Connect to the database
            db_connection = get_db_connection()
            try:
                with db_connection.cursor() as cursor:
                    # Fetch demands made by the client that do not have a deal yet
                    cursor.execute(
                        """
                        SELECT dd.id_demande, dd.titre
                        FROM demande_de_devis dd
                        LEFT JOIN offre o ON dd.id_demande = o.id_demande
                        WHERE dd.id_user = %s
                        GROUP BY dd.id_demande, dd.titre
                        HAVING COUNT(o.id_offre) = 0
                        """,
                        [id_client]
                    )
                    demands = cursor.fetchall()

                    if not demands:
                        return JsonResponse(
                            {"demands": []}, 
                            status=200
                        )

                    # Structure the response
                    demands_list = []
                    for demand in demands:
                        demand_id, demand_title = demand

                        # Fetch offers related to the current demand
                        cursor.execute(
                            """
                            SELECT o.id_offre, u.first_name || ' ' || u.last_name AS artisan_name, 
                                   u.id AS artisan_id, o.offered_price
                            FROM offre o
                            INNER JOIN auth_user u ON o.id_artisan = u.id
                            WHERE o.id_demande = %s
                            """,
                            [demand_id]
                        )
                        offers = cursor.fetchall()

                        # Structure offers
                        offers_list = [
                            {
                                "idOffer": offer[0],
                                "artisanName": offer[1],
                                "artisanId": offer[2],
                                "price": float(offer[3])
                            }
                            for offer in offers
                        ]

                        # Append demand and offers to the response
                        demands_list.append(
                            {
                                "id": demand_id,
                                "title": demand_title,
                                "offers": offers_list,
                            }
                        )

                # Success response
                return JsonResponse({"demands": demands_list}, status=200)

            finally:
                db_connection.close()

        except Exception as e:
            # Handle any errors
            return JsonResponse(
                {"success": False, "message": f"Une erreur s'est produite: {str(e)}"},
                status=500,
            )

    # If not GET, return method not allowed
    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)



@csrf_exempt
def approve_offer(request, idClient, idOffer):
    if request.method == "GET":
        try:
            # Database connection
            connection = get_db_connection()
            try:
                with transaction.atomic():  # Ensure atomicity
                    with connection.cursor() as cursor:
                        # Step 1: Validate the offer belongs to the client's demand
                        cursor.execute(
                            """
                            SELECT o.id_offre, o.id_demande, o.id_artisan, o.offered_price
                            FROM offre o
                            INNER JOIN demande_de_devis d ON o.id_demande = d.id_demande
                            WHERE o.id_offre = %s AND d.id_user = %s
                            """,
                            [idOffer, idClient]
                        )
                        offer = cursor.fetchone()

                        if not offer:
                            return JsonResponse({"success": False, "message": "Offer not found or does not belong to the client's demands."}, status=404)

                        id_offre, id_demande, id_artisan, offered_price = offer

                        # Step 2: Ensure the offer has not already been approved
                        cursor.execute(
                            """
                            SELECT id_travail
                            FROM travail
                            WHERE id_offre = %s
                            """,
                            [id_offre]
                        )
                        if cursor.fetchone():
                            return JsonResponse({"success": False, "message": "This offer has already been approved."}, status=400)

                        # Step 3: Create a deal (travail entry)
                        cursor.execute(
                            """
                            INSERT INTO travail (titre, id_offre)
                            VALUES (%s, %s)
                            RETURNING id_travail
                            """,
                            [f"Deal for Demand {id_demande}", id_offre]
                        )
                        deal_id = cursor.fetchone()[0]

                        # Commit transaction
                        connection.commit()

                        return JsonResponse({"success": True, "message": "The offer has been approved and a deal has been created.", "dealId": deal_id}, status=200)
            finally:
                connection.close()

        except Exception as e:
            # Handle errors
            return JsonResponse({"success": False, "message": f"An error occurred: {str(e)}"}, status=500)

    # Method not allowed
    return JsonResponse({"success": False, "message": "Method not allowed."}, status=405)


@csrf_exempt
def get_client_deal_tasks(request, idClient, idDeal):      
    if request.method == "GET":
        try:
            # Connect to the database
            connection = get_db_connection()
            with connection.cursor() as cursor:
                # Verify the deal belongs to the client
                cursor.execute(
                    """
                    SELECT t.id_travail
                    FROM travail t
                    INNER JOIN offre o ON t.id_offre = o.id_offre
                    INNER JOIN demande_de_devis d ON o.id_demande = d.id_demande
                    WHERE d.id_user = %s AND t.id_travail = %s
                    """,
                    [idClient, idDeal]
                )
                deal_row = cursor.fetchone()

                if not deal_row:
                    return JsonResponse({"success": False, "message": "Deal not found or does not belong to the client."}, status=404)

                deal_id = deal_row[0]

                # Fetch the mini-tasks associated with the deal, categorized by their state
                cursor.execute(
                    """
                    SELECT mt.id_tache, mt.description, mt.etat, mt.dateDebut, mt.dateFin
                    FROM Mini_Tache mt
                    WHERE mt.id_travail = %s
                    """,
                    [deal_id]
                )
                tasks = cursor.fetchall()

                # Categorize tasks into "restantes," "encour," and "terminer"
                restantes = []
                encour = []
                terminer = []

                for task in tasks:
                    task_id, description, etat, date_debut, date_fin = task
                    task_data = {
                        "id": task_id,
                        "description": description,
                        "dateDebut": str(date_debut) if date_debut else None,
                        "dateFin": str(date_fin) if date_fin else None,
                    }

                    if etat == "a_faire":
                        restantes.append(task_data)
                    elif etat == "en cours":
                        encour.append(task_data)
                    elif etat == "fait":
                        terminer.append(task_data)

                # Return the response
                return JsonResponse(
                    {
                        "restantes": restantes,
                        "encour": encour,
                        "terminer": terminer,
                    },
                    status=200
                )

        except Exception as e:
            return JsonResponse({"success": False, "message": f"An error occurred: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Method not allowed."}, status=405)
@csrf_exempt
def edit_artisan_profile(request):
    if request.method == "POST":
        try:
            # Check if the request body is empty
            if not request.body:
                return JsonResponse({"success": False, "message": "Le corps de la requête est vide."}, status=400)

            # Parse the request body
            data = json.loads(request.body.decode("utf-8"))

            # Extract the artisan ID and fields to be updated
            artisan_id = data.get("id")
            first_name = data.get("firstName", "").strip()
            last_name = data.get("LastName", "").strip()
            phone_number = data.get("PhoneNumber", "").strip()
            email = data.get("email", "").strip()
            new_pfp = data.get("pfp", "").strip()  # Profile picture URL or Base64

            # Validate artisan ID
            if not artisan_id:
                return JsonResponse({"success": False, "message": "L'identifiant de l'artisan est requis."}, status=400)

            # Prepare fields for update
            fields_to_update = []
            params = []

            if first_name:
                fields_to_update.append("first_name = %s")
                params.append(first_name)
            if last_name:
                fields_to_update.append("last_name = %s")
                params.append(last_name)
            if phone_number:
                fields_to_update.append("phoneNumber = %s")
                params.append(phone_number)
            if email:
                fields_to_update.append("email = %s")
                params.append(email)
            if new_pfp:
                fields_to_update.append("pfp = %s")
                params.append(new_pfp)

            # If no fields to update, return success without changes
            if not fields_to_update:
                return JsonResponse({"success": True, "message": "Aucune modification apportée."}, status=200)

            # Build the update query
            query = f"UPDATE auth_user SET {', '.join(fields_to_update)} WHERE id = %s"
            params.append(artisan_id)

            # Execute the update query in the database
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(query, params)
                    connection.commit()

                    # If the profile picture changed, send the new URL
                    if new_pfp:
                        return JsonResponse({"success": True, "message": "Profil mis à jour avec succès.", "newPfp": new_pfp}, status=200)

                    return JsonResponse({"success": True, "message": "Profil mis à jour avec succès."}, status=200)

            finally:
                connection.close()

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)

@csrf_exempt
def edit_password(request):
    if request.method == "POST":
        try:
            # Parse the request body
            if not request.body:
                return JsonResponse({"success": False, "message": "Le corps de la requête est vide."}, status=400)

            data = json.loads(request.body.decode("utf-8"))
            old_password = data.get("oldPassword")
            new_password = data.get("newPassword")

            # Validate input
            if not old_password or not new_password:
                return JsonResponse({"success": False, "message": "Les champs 'oldPassword' et 'newPassword' sont requis."}, status=400)

            # Get user ID from the session
            artisan_id = request.session.get('user_id')
            if not artisan_id:
                return JsonResponse({"success": False, "message": "Utilisateur non trouvé dans la session."}, status=403)

            # Database connection
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    # Retrieve the artisan's current password from the database
                    cursor.execute("SELECT password FROM auth_user WHERE id = %s AND is_staff = TRUE", [artisan_id])
                    user_row = cursor.fetchone()
                    if not user_row:
                        return JsonResponse({"success": False, "message": "Artisan introuvable."}, status=404)

                    db_password = user_row[0]

                    # Verify the old password
                    if not check_password(old_password, db_password):
                        return JsonResponse({"success": False, "message": "L'ancien mot de passe est incorrect."}, status=400)

                    # Hash the new password
                    hashed_new_password = make_password(new_password)

                    # Update the artisan's password in the database
                    cursor.execute(
                        "UPDATE auth_user SET password = %s WHERE id = %s AND is_staff = TRUE",
                        [hashed_new_password, artisan_id]
                    )
                    connection.commit()

                # Return success response
                return JsonResponse({"success": True, "message": "Mot de passe modifié avec succès."}, status=200)

            finally:
                connection.close()

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)

@csrf_exempt
def get_devis_by_job(request, job):
    if request.method == "GET":
        try:
            # Database connection
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    # Query to fetch devis based on the artisan's job
                    cursor.execute(
                        """
                        SELECT 
                            dd.id_demande AS id,
                            au.first_name AS clientFirstName,
                            au.last_name AS clientLastName,
                            dd.titre AS title,
                            COALESCE(ie.image, '') AS imgLink
                        FROM demande_de_devis dd
                        INNER JOIN auth_user au ON dd.id_user = au.id
                        LEFT JOIN image_exemple ie ON dd.id_demande = ie.id_demande
                        WHERE dd.metier = %s
                        ORDER BY dd.id_demande DESC
                        """,
                        [job]
                    )

                    # Fetch results
                    rows = cursor.fetchall()

                    # Format the response
                    devis = [
                        {
                            "id": row[0],
                            "clientFirstName": row[1],
                            "clientLastName": row[2],
                            "title": row[3],
                            "imgLink": row[4]
                        }
                        for row in rows
                    ]

                # Return the data as JSON
                return JsonResponse({"devis": devis}, status=200)

            finally:
                connection.close()

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)

@csrf_exempt
def get_one_devis(request, id):
    if request.method == "GET":
        try:
            # Database connection
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    # Query to fetch details of the specified devis
                    cursor.execute(
                        """
                        SELECT 
                            dd.id_demande AS id,
                            au.first_name AS clientFirstName,
                            au.last_name AS clientLastName,
                            dd.titre AS title,
                            dd.description AS description,
                            COALESCE(pd.prix, 0) AS estimatedPrice
                        FROM 
                            demande_de_devis dd
                        INNER JOIN 
                            auth_user au ON dd.id_user = au.id
                        LEFT JOIN 
                            prix_de_demande pd ON dd.id_demande = pd.id_demande
                        WHERE 
                            dd.id_demande = %s
                        """,
                        [id]
                    )
                    devis_row = cursor.fetchone()

                    if not devis_row:
                        return JsonResponse({"success": False, "message": "Le devis spécifié est introuvable."}, status=404)

                    # Extract data for the devis
                    devis = {
                        "id": devis_row[0],
                        "clientFirstName": devis_row[1],
                        "clientLastName": devis_row[2],
                        "title": devis_row[3],
                        "description": devis_row[4],
                        "estimatedPrice": float(devis_row[5]),
                        "imgLinks": []  # Placeholder for images
                    }

                    # Fetch associated images for the devis
                    cursor.execute(
                        """
                        SELECT 
                            image 
                        FROM 
                            image_exemple 
                        WHERE 
                            id_demande = %s
                        """,
                        [id]
                    )
                    images = cursor.fetchall()
                    devis["imgLinks"] = [img[0] for img in images]

                # Return the devis details as JSON
                return JsonResponse({"devis": devis}, status=200)

            finally:
                connection.close()

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)

@csrf_exempt
def make_offer(request, id):
    if request.method == "POST":
        try:
            # Parse the request body
            if not request.body:
                return JsonResponse({"success": False, "message": "Le corps de la requête est vide."}, status=400)

            data = json.loads(request.body.decode("utf-8"))
            artisan_id = data.get("artisanId")
            price = data.get("price")

            # Validate input
            if not artisan_id or not price:
                return JsonResponse({"success": False, "message": "Les champs 'artisanId' et 'price' sont requis."}, status=400)

            # Database connection
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    # Check if the devis exists
                    cursor.execute(
                        "SELECT id_demande FROM demande_de_devis WHERE id_demande = %s",
                        [id]
                    )
                    devis_row = cursor.fetchone()
                    if not devis_row:
                        return JsonResponse({"success": False, "message": "Le devis spécifié est introuvable."}, status=404)

                    # Check if the artisan already made an offer for this devis
                    cursor.execute(
                        """
                        SELECT id_offre FROM offre
                        WHERE id_artisan = %s AND id_demande = %s
                        """,
                        [artisan_id, id]
                    )
                    if cursor.fetchone():
                        return JsonResponse({"success": False, "message": "Vous avez déjà fait une offre pour ce devis."}, status=400)

                    # Insert the offer into the `offre` table
                    cursor.execute(
                        """
                        INSERT INTO offre (offered_price, id_artisan, id_demande)
                        VALUES (%s, %s, %s)
                        """,
                        [price, artisan_id, id]
                    )
                    connection.commit()

                # Success response
                return JsonResponse({"success": True, "message": "Offre faite avec succès."}, status=201)

            finally:
                connection.close()

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)
@csrf_exempt
def get_artisan_deals(request, id):
    if request.method == "GET":
        try:
            # Database connection
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    # Query to fetch all deals assigned to the artisan
                    cursor.execute(
                        """
                        SELECT 
                            t.id_travail AS id,
                            au.first_name || ' ' || au.last_name AS clientName,
                            dd.titre AS title,
                            CASE 
                                WHEN COUNT(mt.id_tache) = 0 THEN 0
                                ELSE ROUND(100.0 * SUM(CASE WHEN mt.etat = 'fait' THEN 1 ELSE 0 END) / COUNT(mt.id_tache), 2)
                            END AS pourcentage
                        FROM 
                            travail t
                        INNER JOIN 
                            offre o ON t.id_offre = o.id_offre
                        INNER JOIN 
                            demande_de_devis dd ON o.id_demande = dd.id_demande
                        INNER JOIN 
                            auth_user au ON dd.id_user = au.id
                        LEFT JOIN 
                            Mini_Tache mt ON t.id_travail = mt.id_travail
                        WHERE 
                            o.id_artisan = %s
                        GROUP BY 
                            t.id_travail, au.first_name, au.last_name, dd.titre
                        ORDER BY 
                            t.id_travail DESC
                        """,
                        [id]
                    )

                    # Fetch results
                    rows = cursor.fetchall()

                    # Format the response
                    deals = [
                        {
                            "id": row[0],
                            "clientName": row[1],
                            "title": row[2],
                            "pourcentage": float(row[3])  # Completion percentage
                        }
                        for row in rows
                    ]

                # Return the data as JSON
                return JsonResponse({"deals": deals}, status=200)

            finally:
                connection.close()

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)

@csrf_exempt
def get_deal_tasks(request, idArtisan, idDeal):
    if request.method == "GET":
        try:
            # Database connection
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    # Verify the deal belongs to the artisan
                    cursor.execute(
                        """
                        SELECT t.id_travail
                        FROM travail t
                        INNER JOIN offre o ON t.id_offre = o.id_offre
                        WHERE t.id_travail = %s AND o.id_artisan = %s
                        """,
                        [idDeal, idArtisan]
                    )
                    deal_row = cursor.fetchone()

                    if not deal_row:
                        return JsonResponse({"success": False, "message": "Ce deal n'existe pas ou n'est pas attribué à cet artisan."}, status=404)

                    # Fetch tasks associated with the deal
                    cursor.execute(
                        """
                        SELECT 
                            mt.id_tache AS id,
                            mt.description,
                            mt.dateDebut,
                            mt.dateFin,
                            mt.etat
                        FROM 
                            Mini_Tache mt
                        WHERE 
                            mt.id_travail = %s
                        """,
                        [idDeal]
                    )

                    tasks = cursor.fetchall()

                    # Categorize tasks
                    restantes = []
                    encour = []
                    terminer = []

                    for task in tasks:
                        task_id, description, date_debut, date_fin, etat = task
                        task_data = {
                            "id": task_id,
                            "description": description,
                            "dateDebut": str(date_debut) if date_debut else None,
                            "dateFin": str(date_fin) if date_fin else None,
                        }

                        if etat == "a_faire":
                            restantes.append(task_data)
                        elif etat == "en cours":
                            encour.append(task_data)
                        elif etat == "fait":
                            terminer.append(task_data)

                # Return categorized tasks
                return JsonResponse(
                    {
                        "restantes": restantes,
                        "encour": encour,
                        "terminer": terminer,
                    },
                    status=200
                )

            finally:
                connection.close()

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)
@csrf_exempt
def edit_deal_task(request, idArtisan, idDeal):
    if request.method == "POST":
        try:
            # Parse request body
            if not request.body:
                return JsonResponse({"success": False, "message": "Le corps de la requête est vide."}, status=400)

            data = json.loads(request.body.decode("utf-8"))

            # Extract task ID and fields to update
            task_id = data.get("id")
            new_status = data.get("etat", "").strip()  # Status change (e.g., 'en cours', 'fait')
            description = data.get("description", "").strip()
            date_debut = data.get("dateDebut", "").strip()
            date_fin = data.get("dateFin", "").strip()

            if not task_id:
                return JsonResponse({"success": False, "message": "L'identifiant de la tâche est requis."}, status=400)

            # Database connection
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    # Verify the deal belongs to the artisan
                    cursor.execute(
                        """
                        SELECT t.id_travail
                        FROM travail t
                        INNER JOIN offre o ON t.id_offre = o.id_offre
                        WHERE t.id_travail = %s AND o.id_artisan = %s
                        """,
                        [idDeal, idArtisan]
                    )
                    deal_row = cursor.fetchone()

                    if not deal_row:
                        return JsonResponse({"success": False, "message": "Ce deal n'existe pas ou n'est pas attribué à cet artisan."}, status=404)

                    # Check if the task exists
                    cursor.execute(
                        "SELECT id_tache FROM Mini_Tache WHERE id_tache = %s AND id_travail = %s",
                        [task_id, idDeal]
                    )
                    existing_task = cursor.fetchone()

                    if not existing_task:
                        return JsonResponse({"success": False, "message": "La tâche spécifiée n'existe pas."}, status=404)

                    # Update the task if it exists
                    fields_to_update = []
                    params = []

                    if new_status:
                        fields_to_update.append("etat = %s")
                        params.append(new_status)
                    if description:
                        fields_to_update.append("description = %s")
                        params.append(description)
                    if date_debut:
                        fields_to_update.append("dateDebut = %s")
                        params.append(date_debut)
                    if date_fin:
                        fields_to_update.append("dateFin = %s")
                        params.append(date_fin)

                    if not fields_to_update:
                        return JsonResponse({"success": False, "message": "Aucune modification apportée."}, status=400)

                    query = f"UPDATE Mini_Tache SET {', '.join(fields_to_update)} WHERE id_tache = %s AND id_travail = %s"
                    params.extend([task_id, idDeal])

                    cursor.execute(query, params)
                    connection.commit()

                return JsonResponse({"success": True, "message": "Tâche mise à jour avec succès."}, status=200)

            finally:
                connection.close()

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)


@csrf_exempt
def admin_demandes(request):
    if request.method == "GET":
        try:
            page = int(request.GET.get("page", 1))
            demandes_per_page = 5

            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT COUNT(*) FROM auth_user WHERE is_staff = TRUE AND is_superuser = FALSE AND is_validated = FALSE"
                    )

                    number_of_demandes = cursor.fetchone()[0]

                    total_pages = ceil(number_of_demandes / demandes_per_page)
                    if total_pages == 0:
                        return JsonResponse(
                            {"success": False, "message": "Aucune demande n'est disponible."},
                            status=200,
                        )
                    if page < 1 or page > total_pages:
                        return JsonResponse(
                            {"success": False, "message": "Invalid page number."},
                            status=400,
                        )
                    offset = (page - 1) * demandes_per_page
                    cursor.execute(
                        """
                        SELECT 
                            A.first_name, 
                            A.last_name, 
                            A.id, 
                            A.isCertified, 
                            A.isAssured, 
                            CASE WHEN A.isCertified = TRUE THEN C.certificat_joint ELSE NULL END AS certificateLink,
                            CASE WHEN A.isAssured = TRUE THEN B.assurance ELSE NULL END AS assuranceLink,
                            J.Nmetier
                        FROM 
                            auth_user A
                        LEFT JOIN 
                            assurance B ON A.id = B.id_user
                        LEFT JOIN 
                            certificat C ON A.id = C.id_user
                        LEFT JOIN 
                            metier J ON A.idMetier = J.idMetier
                        WHERE 
                            A.is_staff = TRUE 
                            AND A.is_superuser = FALSE 
                            AND A.is_validated = FALSE
                        ORDER BY 
                            A.id 
                        LIMIT %s OFFSET %s
                        """,
                        [demandes_per_page, offset],
                    )

                    rows = cursor.fetchall()

                    demandes = [
                        {
                            "id": row[2], "firstName": row[0], "lastName": row[1], "is_certified": row[3], "certificateLink": row[6],
                            "is_assured": row[4],
                            "assuranceLink": row[5], "job": row[7],
                        }
                        for row in rows
                    ]

                    response_data = {
                        "demandes": demandes,
                        "pagination": {
                            "currentPage": page,
                            "totalPages": total_pages,
                            "totalDemandes": number_of_demandes,
                        }
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
def admin_demande(request, id_dem):
    if request.method == "GET":
        try:
            if id_dem:
                connection = get_db_connection()
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT id , first_name , last_name , isCertified ,  isAssured, idMetier FROM auth_user WHERE id = %s",
                                [id_dem]
                        )  
                        user_row = cursor.fetchone()

                        if not user_row:
                            return JsonResponse ({"success": False, "message":"pas de demande avec cet id"}, status=404)
                        
                        (
                            user_id, first_name, last_name, is_certified, is_assured, idMetier
                        ) = user_row

                        cursor.execute(
                            " SELECT Nmetier FROM  metier WHERE idMetier = %s ", [idMetier]
                        )

                        job = cursor.fetchone()

                        if not job:
                            return JsonResponse({"success": False, "message": "le metier n'a pas été trouver"}, status=404)
                        
                        
                        cursor.execute(
                            " SELECT assurance FROM  assurance WHERE id_user = %s ", [user_id]
                        )

                        assurance_files = cursor.fetchall()


                        if not assurance_files:
                            # If no assurance files are found
                            assurance_files = []
                        
                        
                        assurance_files_list = [row[0] for row in assurance_files]
                        
                        cursor.execute(
                            " SELECT certificat_joint FROM  certificat WHERE id_user = %s ", [user_id]
                        )

                        certificate_files = cursor.fetchall()


                        if not certificate_files:
                            # If no assurance files are found
                            assurance_files = []
                        
                        
                        certificate_files_list = [row[0] for row in certificate_files]
                    
                        response_data = {
                            "id": user_id,
                            "first_name": first_name,
                            "last_name": last_name,
                            "is_certified": is_certified,
                            "is_assured": is_assured,
                            "job": job[0],
                            "assurance_files": assurance_files_list,
                            "certificat_files": certificate_files_list,
                        }

                    return JsonResponse({"success": True, "data": response_data}, status=200)
                finally:
                    connection.close()

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)
    
    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)

@csrf_exempt
def get_job_names(request):
    if request.method == "GET":
        try:
            # Connect to the database
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    # Fetch all job names from the `metier` table
                    cursor.execute("SELECT Nmetier FROM metier")
                    jobs = cursor.fetchall()

                    # Extract job names into a list
                    job_names = [job[0] for job in jobs]

                # Return the list of job names
                return JsonResponse({"job_names": job_names}, status=200)

            finally:
                connection.close()

        except Exception as e:
            return JsonResponse({"success": False, "message": f"An error occurred: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Method not allowed."}, status=405)
@csrf_exempt
def artisan_portfolio(request, id):
    if request.method == "GET":
        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                # Fetch all posts for the artisan
                cursor.execute(
                    """
                    SELECT 
                        id AS id,
                        title,
                        picture,
                        description
                    FROM artisan_posts
                    WHERE id_artisan = %s
                    """,
                    [id]
                )
                portfolio_posts = [
                    {
                        "id": row[0],
                        "title": row[1],
                        "picture": row[2],
                        "description": row[3],
                    }
                    for row in cursor.fetchall()
                ]

                return JsonResponse({"posts": portfolio_posts}, status=200)
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Une erreur s'est produite: {str(e)}"}, status=500)
    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)
@csrf_exempt
def add_artisan_post(request, id=None):  # `id` is optional from the URL
    if request.method == "POST":
        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body.decode("utf-8"))

            # Use `id` from the URL if provided, otherwise fallback to `artisanId` in the body
            artisan_id = id or data.get("artisanId")
            title = data.get("title")
            picture = data.get("picture")
            description = data.get("description")

            # Validate required fields
            if not artisan_id:
                return JsonResponse({"success": False, "message": "Artisan ID is required."}, status=400)
            if not all([title, picture, description]):
                return JsonResponse({"success": False, "message": "All fields are required."}, status=400)

            # Insert the new post into the database
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO artisan_posts (id_artisan, title, picture, description)
                    VALUES (%s, %s, %s, %s)
                    """,
                    [artisan_id, title, picture, description]
                )
                connection.commit()

            return JsonResponse({"success": True, "message": "Post added successfully."}, status=201)

        except Exception as e:
            return JsonResponse({"success": False, "message": f"An error occurred: {str(e)}"}, status=500)
    return JsonResponse({"success": False, "message": "Method not allowed."}, status=405)

@csrf_exempt
def delete_artisan_post(request, id):
    if request.method == "POST":
        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body.decode("utf-8"))

            # Extract the post ID
            post_id = data.get("postId")

            # Validate the post ID
            if not post_id:
                return JsonResponse({"success": False, "message": "Post ID is required."}, status=400)

            # Delete the post from the database
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM artisan_posts
                    WHERE id = %s AND id_artisan = %s
                    """,
                    [post_id, id]
                )
                # Check if any row was deleted
                if cursor.rowcount == 0:
                    return JsonResponse({"success": False, "message": "Post not found or does not belong to this artisan."}, status=404)

                connection.commit()

            return JsonResponse({"success": True, "message": "Post deleted successfully."}, status=200)

        except Exception as e:
            return JsonResponse({"success": False, "message": f"An error occurred: {str(e)}"}, status=500)
    return JsonResponse({"success": False, "message": "Method not allowed."}, status=405)

@csrf_exempt
def get_admin_tasks(request):
    if request.method =="GET":
        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                # Fetch backlog tasks
                cursor.execute(
                    """
                    SELECT idTache, titre, description
                    FROM tache_admin
                    WHERE etat = 'a_faire'
                    """
                )
                backlog = [
                    {"id": row[0], "title": row[1], "description": row[2]}
                    for row in cursor.fetchall()
                ]

                # Fetch tasks in progress
                cursor.execute(
                    """
                    SELECT idTache, titre, description
                    FROM tache_admin
                    WHERE etat = 'en_cours'
                    """
                )
                encour = [
                    {"id": row[0], "title": row[1], "description": row[2]}
                    for row in cursor.fetchall()
                ]

                # Fetch completed tasks
                cursor.execute(
                    """
                    SELECT idTache, titre, description
                    FROM tache_admin
                    WHERE etat = 'fait'
                    """
                )
                terminer = [
                    {"id": row[0], "title": row[1], "description": row[2]}
                    for row in cursor.fetchall()
                ]

            return JsonResponse(
                {"backlog": backlog, "encour": encour, "terminer": terminer}, status=200
            )

        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"An error occurred: {str(e)}"}, status=500
            )
    return JsonResponse(
        {"success": False, "message": "Method not allowed."}, status=405
    )

@csrf_exempt
def add_admin_task(request):
    if request.method == "POST":
        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body.decode("utf-8"))

            # Extract fields from the body
            title = data.get("title")
            description = data.get("description")
            state = data.get("state")
            admin_id = data.get("adminId")  # Add adminId to the request

            # Validate required fields
            if not all([title, description, state, admin_id]):
                return JsonResponse({"success": False, "message": "All fields are required."}, status=400)

            # Validate the state value
            if state not in ["a_faire", "en_cours", "fait"]:
                return JsonResponse({"success": False, "message": "Invalid state. Must be 'a_faire', 'en_cours', or 'fait'."}, status=400)

            # Insert the new task into the database
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO tache_admin (titre, description, etat, id_admin)
                    VALUES (%s, %s, %s, %s)
                    RETURNING idTache
                    """,
                    [title, description, state, admin_id]
                )
                task_id = cursor.fetchone()[0]
                connection.commit()

            return JsonResponse({"id": task_id}, status=201)

        except Exception as e:
            return JsonResponse({"success": False, "message": f"An error occurred: {str(e)}"}, status=500)
    return JsonResponse({"success": False, "message": "Method not allowed."}, status=405)
@csrf_exempt
def delete_admin_task(request, id):
    if request.method == "POST":
        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body.decode("utf-8"))

            # Extract the task ID from the request
            task_id = data.get("id")

            if not task_id:
                return JsonResponse({"success": False, "message": "Task ID is required."}, status=400)

            # Connect to the database
            connection = get_db_connection()
            with connection.cursor() as cursor:
                # Check if the task exists
                cursor.execute(
                    """
                    SELECT idTache FROM tache_admin WHERE idTache = %s
                    """,
                    [task_id]
                )
                task = cursor.fetchone()

                if not task:
                    return JsonResponse({"success": False, "message": "Task not found."}, status=404)

                # Delete the task
                cursor.execute(
                    """
                    DELETE FROM tache_admin
                    WHERE idTache = %s
                    """,
                    [task_id]
                )
                connection.commit()

            return JsonResponse({"success": True, "message": "Task deleted successfully."}, status=200)

        except Exception as e:
            return JsonResponse({"success": False, "message": f"An error occurred: {str(e)}"}, status=500)
    return JsonResponse({"success": False, "message": "Method not allowed."}, status=405)


import stripe
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os

# Set your Stripe secret key and initialize logger
stripe.api_key = os.getenv("sk_test_51OyyMrP5lheqX2jkqL5s8zN6G82jGPSh9AhCEFJeof9aFnHdol5ESPOEk0RWoLvlmEVU0qiCoX1rWkL2Ku0jRkZV005fddGOig")
webhook_secret = os.getenv("whsec_pQzxEF42taSLjhgnXJU0n7R5bdt2V7hC")
logger = logging.getLogger(__name__)

@csrf_exempt
def create_stripe_session_for_travail(request):
    if request.method == "POST":
        try:
            # Parse the request body
            data = json.loads(request.body)
            travail_id = data.get("id_travail")
            service_title = data.get("titre", "Service Payment")
            service_price = data.get("price")
            currency = data.get("currency", "usd")

            if not travail_id or not service_price:
                return JsonResponse({"error": "Missing required fields: id_travail or price"}, status=400)

            # Verify the price in the database
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT id_travail, titre, price FROM travail WHERE id_travail = %s", [travail_id])
                result = cursor.fetchone()
                if not result or float(service_price) != float(result[2]):
                    return JsonResponse({"error": "Invalid travail ID or service price mismatch"}, status=400)

            amount_in_cents = int(float(service_price) * 100)

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": currency,
                            "product_data": {"name": service_title},
                            "unit_amount": amount_in_cents,
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=f"https://onecs-project.onrender.com/payment/success/?id_travail={travail_id}",
                cancel_url="https://onecs-project.onrender.com/payment/cancel/",
                metadata={"id_travail": travail_id},
            )

            return JsonResponse({"url": session.url}, status=200)
        except Exception as e:
            logger.error(f"Error creating Stripe session: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def payment_success(request):
    try:
        travail_id = request.GET.get("id_travail")
        if not travail_id:
            return JsonResponse({"error": "Missing travail ID"}, status=400)

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE travail SET payment_status = 'paid' WHERE id_travail = %s", [travail_id]
            )
        connection.commit()

        return JsonResponse({"success": True, "message": "Payment succeeded!"}, status=200)
    except Exception as e:
        logger.error(f"Error in payment success: {e}")
        return JsonResponse({"error": str(e)}, status=500)

def payment_cancel(request):
    return JsonResponse({"success": False, "message": "Payment canceled."}, status=200)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        logger.error("Invalid payload")
        return JsonResponse({"error": "Invalid payload"}, status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature")
        return JsonResponse({"error": "Invalid signature"}, status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        travail_id = session["metadata"].get("id_travail")

        if travail_id:
            try:
                connection = get_db_connection()
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE travail SET payment_status = 'paid' WHERE id_travail = %s", [travail_id]
                    )
                connection.commit()
            except Exception as e:
                logger.error(f"Error updating payment status: {e}")
                return JsonResponse({"error": str(e)}, status=500)

    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        travail_id = payment_intent["metadata"].get("id_travail")

        if travail_id:
            try:
                connection = get_db_connection()
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE travail SET payment_status = 'failed' WHERE id_travail = %s", [travail_id]
                    )
                connection.commit()
            except Exception as e:
                logger.error(f"Error updating payment status for failure: {e}")
                return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"success": True, "message": "Webhook handled successfully"}, status=200)