from django.urls import path
from . import views

urlpatterns = [
    # 🌟 Basic Pages
    path('', views.home, name='home'),
    path('services/', views.services, name='services'),
    
    # 🔐 Authentication System (Naye Links)
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # 🚀 SMM Core Features
    path('add-funds/', views.add_funds, name='add_funds'),
    path('new-order/', views.new_order, name='new_order'),
    path('orders/', views.orders, name='orders'),
    
    # Extra pages (Agar aapne banaye hain)
    path('team/', views.team, name='team'),
    path('profile/', views.profile, name='profile'),
]
