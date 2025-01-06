from django.urls import path
from . import views

urlpatterns = [
  path('artisan-signup/', views.artisan_signup, name='artisan_signup'),
  path('client-signup/', views.client_signup, name='client_signup'),
  path('user-login/', views.user_login, name='user_login'),
  path('user-logout/', views.user_logout, name='artisan_logout'),
  path('email-taken/', views.email_taken, name='email-logout'),
  path('validate-artisan/<int:artisan_id>/',views.validate_artisan, name='validate_artisan'),
  path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
  path('search-artisans/', views.search_artisans_by_job, name='search_artisans_by_job'),
  path('admin/clients/', views.admin_clients, name='admin_clients'),
  path('admin/clients/delete/', views.delete_client, name='delete_client'),
  path('admin/artisans/', views.admin_artisans, name='admin_artisans'),
  path('admin/artisans/delete/', views.delete_artisan, name='delete_artisan'),
  path('client/edit-profile/', views.edit_client_profile, name='edit_client_profile'),
  path('client/edit-password/', views.edit_password, name='edit_password'),
  path('client/pannier/<int:idClient>/', views.get_client_pannier, name='get_client_pannier'),
  path("client/new-demand/", views.new_demand, name="new_demand"),
  path("client/current-demands/<int:id_client>/", views.current_demands, name="current_demands"),
  path('client/demand/offer-approve/<int:idClient>/<int:idOffer>/', views.approve_offer, name='approve_offer'),
  path('client/deals/<int:idClient>/<int:idDeal>/', views.get_client_deal_tasks, name='get_client_deal_tasks'),
  # path('create-user/', views.create_user, name='create_user'),
  # path('login-user/', views.login_user, name='login_user'),
  # path('search-user/', views.search_user, name='search_user'),
]