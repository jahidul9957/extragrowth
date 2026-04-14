from django.urls import path
from . import views

urlpatterns = [
    path('add-funds/', views.add_funds, name='add_funds'),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('services/', views.services, name='services'),
    path('team/', views.team, name='team'),
    path('profile/', views.profile, name='profile'),
]
