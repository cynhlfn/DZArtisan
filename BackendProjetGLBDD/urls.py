"""
URL configuration for prjtBDDGL project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views
from chat.views import *
from django.conf import settings
from django.conf.urls.static import static

# from django.conf import settings
# from django.contrib.staticfiles.urls import static
# from chat.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('userauthArtisan/', include('userauthArtisan.urls')), 
    # path('', include('accounts.urls')), 
    #     path('', views.index, name='index'),
    # Ckeditor
    path("hotel/ckeditor5/", include('django_ckeditor_5.urls')),
    # path('userauths/', include('userauths.urls')),
    path('app/',include('app.urls')),
    

    path("", user_login, name="login"),
    path("signup/", client_signup, name="signup"),
    path("logout/", user_logout, name="logout"),
    path("user/", HomePage, name="home"),
    path("edit/", EditProfile, name="edit"),
    path("user/<str:username>/", userprofile, name="username"),
    path("add_friend/", add_friend, name="add_friend"),
    path("accept_request/", accept_request, name="accept_request"),
    path("delete_friend/", delete_friend, name="delete_friend"),
    path("search/", search, name="search"),
    # re_path(r"^.*/$", RedirectView.as_view(pattern_name="login", permanent=False)),
    path("chat/<str:username>/", chat, name="chat"),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)