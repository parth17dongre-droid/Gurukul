# Gurukul/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Login/Logout logic
    path('login/', auth_views.LoginView.as_view(template_name='home/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # This line triggered the error, but now it will work because home/urls.py exists!
    path('', include('home.urls')), 
]