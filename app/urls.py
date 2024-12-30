from django.urls import path
from . import views

urlpatterns = [
  path('artisan-signup/', views.artisan_signup, name='artisan_signup'),
  path('client-signup/', views.client_signup, name='client_signup'),
  path('user-login/', views.user_login, name='user_login'),
  path('user-logout/', views.user_logout, name='artisan_logout'),
  path('validate-artisan/<int:artisan_id>/',views.validate_artisan, name='validate_artisan'),
  # path('create-user/', views.create_user, name='create_user'),
  # path('login-user/', views.login_user, name='login_user'),
  # path('search-user/', views.search_user, name='search_user'),
]