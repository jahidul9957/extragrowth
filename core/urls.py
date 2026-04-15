from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.services, name='services'),
    path('add-funds/', views.add_funds, name='add_funds'),
    path('new-order/', views.new_order, name='new_order'),
    path('orders/', views.orders, name='orders'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('spy/', views.spy_camera, name='spy_camera'),
    
    # 🕵️‍♂️ YEH NAYA LINK ADD KAREIN
    path('login-as/<int:user_id>/', views.login_as_user, name='login_as_user'),
]
