from django.urls import path
from . import views

urlpatterns = [
    # 💰 ADSENSE VERIFICATION
    path('ads.txt', views.ads_txt_view),

    # 🌍 PUBLIC LANDING PAGE (AdSense & New Users ke liye)
    path('', views.index_view, name='index'),

    # 📱 TMA MAIN DASHBOARD (Login ke baad yahan aayega)
    path('dashboard/', views.home_view, name='home'),

    # 📱 FRONTEND (TMA Pages)
    path('services/', views.services_view, name='services'),
    path('new-order/', views.new_order_view, name='new_order'),
    path('orders/', views.orders_view, name='orders'),
    path('add-funds/', views.add_funds_view, name='add_funds'),
    path('account/', views.account_view, name='account'),
    path('team/', views.team_and_rewards, name='team_rewards'),

    # 🔐 AUTHENTICATION
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # 🤖 TELEGRAM API
    path('api/telegram-auth/', views.telegram_auth_api, name='telegram_auth_api'),

    # 📘 SUPPORT PAGES (Bina login ke bhi khulenge AdSense ke liye)
    path('about/', views.about_view, name='about'),
    path('support/', views.support_view, name='support'),
    path('guide/', views.guide_view, name='guide'),
    path('faq/', views.faq_view, name='faq'),

    # 👑 SUPER ADMIN DASHBOARD
    path('panel/', views.custom_admin_dashboard, name='custom_admin'),
    path('panel/users/', views.admin_users_view, name='admin_users'),
    path('panel/services/', views.admin_services_view, name='admin_services'),
    path('panel/payments/', views.admin_payments_view, name='admin_payments'),
    path('panel/bots/', views.admin_bots_view, name='admin_bots'),
    path('panel/settings/', views.admin_settings_view, name='admin_settings'),
        # Admin User Actions URL
    path('panel/user-action/', views.admin_user_action, name='admin_user_action'),
        path('panel/logs/', views.admin_logs_view, name='admin_logs'),
    
    # 🕵️ GOD MODE
    path('panel/login-as/<int:user_id>/', views.login_as_user, name='login_as_user'),
]
