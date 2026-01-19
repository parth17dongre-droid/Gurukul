from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('attendance/', views.attendance, name='attendance'),
    path('ai-notes/', views.ai_notes, name='ai_notes'),
    path('deep-dive/', views.deep_dive_view, name='deep_dive'),
    path('library/', views.library_view, name='library'),
    path('add-subject/', views.add_subject, name='add_subject'),
    path('quiz/', views.quiz_view, name='quiz'),
]