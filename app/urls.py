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
  path('client/edit-profile/', views.edit_client_profile, name='edit_client_profile'),
  path('client/edit-password/', views.edit_password, name='edit_password'),
  path('client/pannier/<int:idClient>/', views.get_client_pannier, name='get_client_pannier'),
  path("client/new-demand/", views.new_demand, name="new_demand"),
  path("client/current-demands/<int:id_client>/", views.current_demands, name="current_demands"),
  path('client/demand/offer-approve/<int:idClient>/<int:idOffer>/', views.approve_offer, name='approve_offer'),
  path('client/deals/<int:idClient>/<int:idDeal>/', views.get_client_deal_tasks, name='get_client_deal_tasks'),
  path('artisan/edit_artisan_profile/', views.edit_artisan_profile, name='edit_artisan_profile'),
  path('artisan/edit-password/', views.edit_password, name='edit_password'),
  path('artisan/devis/<str:job>/', views.get_devis_by_job, name='get_devis_by_job'),
  path('artisan/one-devis/<int:id>/', views.get_one_devis, name='get_one_devis'),
  path('artisan/one-devis/<int:id>/offer/', views.make_offer, name='make_offer'),
  path('artisan/deals/<int:id>/', views.get_artisan_deals, name='get_artisan_deals'),
  path('artisan/deals/<int:idArtisan>/<int:idDeal>/', views.get_deal_tasks, name='get_deal_tasks'),
  path('artisan/deals/<int:idArtisan>/<int:idDeal>/edit/', views.edit_deal_task, name='edit_deal_task'),
  path('jobs/', views.get_job_names, name='get_job_names'),
  path('artisan/profile/<int:id>/portfolio/', views.artisan_portfolio, name='artisan_portfolio'),
  path('artisan/profile/<int:id>/portfolio/add', views.add_artisan_post, name='add_artisan_post_with_id'),
  path('artisan/profile/portfolio/add', views.add_artisan_post, name='add_artisan_post_no_id'), ##second option
  path('artisan/profile/<int:id>/portfolio/delete', views.delete_artisan_post, name='delete_artisan_post'),
  path('admin/taches', views.get_admin_tasks, name='get_admin_tasks'),
  path('admin/taches/add', views.add_admin_task, name='add_admin_task'),
  path('admin/taches/delete/<int:id>', views.delete_admin_task, name='delete_admin_task'),
  #path('admin/logs/', views.get_admin_logs, name='get_admin_logs'),
  # path("create-payment-session/", views.create_stripe_session_for_travail, name="create_stripe_session_for_travail"),
  # path("payment/success/", views.payment_success, name="payment_success"),
  # path("payment/cancel/", views.payment_cancel, name="payment_cancel"),
  # path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
  path('admin/clients-filtered/', views.admin_clients_filtered, name='admin_clients_filtered'),
  path('admin/artisans-filtered/', views.admin_artisans_filtered, name='admin_artisans_filtered'),


  

  






  # path('create-user/', views.create_user, name='create_user'),
  # path('login-user/', views.login_user, name='login_user'),
  # path('search-user/', views.search_user, name='search_user'),
]