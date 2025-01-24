from django.urls import path
from . import views

urlpatterns = [
  path('artisan-signup/', views.artisan_signup, name='artisan_signup'),
  path('client-signup/', views.client_signup, name='client_signup'),
  path('user-login/', views.user_login, name='user_login'),
  path('user-logout/', views.user_logout, name='artisan_logout'),
  path('email-taken/', views.email_taken, name='email-logout'),
  path('validate-artisan/<int:artisan_id>/',views.validate_artisan, name='validate_artisan'),
  path('refuser-artisan/<int:artisan_id>/',views.refuser_artisan, name='refuser_artisan'),
  path('admin/demande/<int:id_dem>/',views.admin_demande, name='admin_demande'),
  path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
  path('search-artisans/', views.search_artisans_by_job, name='search_artisans_by_job'),
  path('admin/clients/', views.admin_clients, name='admin_clients'),
  path('admin/demandes/', views.admin_demandes, name='admin_demandes'),
  path('admin/clients/delete/', views.delete_client, name='delete_client'),
  path('admin/artisans/', views.admin_artisans, name='admin_artisans'),
  path('admin/artisans/delete/', views.delete_artisan, name='delete_artisan'),
  # path('create-user/', views.create_user, name='create_user'),
  # path('login-user/', views.login_user, name='login_user'),
  # path('search-user/', views.search_user, name='search_user'),
]