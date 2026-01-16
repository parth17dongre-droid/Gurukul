from django.urls import path
from . import views

urlpatterns = [
    # The name must match the function name in views.py
    path('', views.index, name='index'),
    
    # ⚠️ Check this line carefully! 
    # It must be 'views.login_view', NOT 'views.login'
    path('login/', views.login_view, name='login'),
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),

    # ... existing paths ...
    path('signup/', views.signup_view, name='signup'),

]