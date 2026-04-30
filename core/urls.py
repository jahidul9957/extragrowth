from django.urls import path
from . import views

urlpatterns = [
    # ==========================================
    # 🌍 PUBLIC & BLOG PAGES
       # 🌍 PUBLIC & BLOG PAGES
    path('', views.index_view, name='index'),
    
    # 💰 ADSENSE VERIFICATION (dhyan rakhein, aage '/' nahi lagana hai)
    path('ads.txt', views.ads_txt_view, name='ads_txt'),
    # ==========================================
    path('', views.index_view, name='index'),
    path('about/', views.about_view, name='about'),
    path('support/', views.support_view, name='support'),
    path('guide/', views.guide_view, name='guide'),
    path('faq/', views.faq_view, name='faq'),
    path('ads.txt', views.ads_txt_view, name='ads_txt'),

    # ==========================================
    # 🔐 AUTHENTICATION
    # ==========================================
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('api/telegram-auth/', views.telegram_auth_api, name='telegram_auth_api'),

    # ==========================================
    # 📱 CUSTOMER DASHBOARD
    # ==========================================
    path('dashboard/', views.home_view, name='home'),
    path('dashboard/services/', views.services_view, name='services'),
    path('dashboard/new-order/', views.new_order_view, name='new_order'),
    path('dashboard/orders/', views.orders_view, name='orders'),
    path('dashboard/add-funds/', views.add_funds_view, name='add_funds'),
    path('dashboard/account/', views.account_view, name='account'),
    path('dashboard/team/', views.team_and_rewards, name='team_rewards'),
    
    # ==========================================
    # 👑 SUPER ADMIN COMMAND CENTER
    # ==========================================
    path('panel/', views.custom_admin_dashboard, name='custom_admin'),
    path('panel/users/', views.admin_users, name='admin_users'),
    path('panel/user-action/', views.admin_user_action, name='admin_user_action'),
    path('panel/services/', views.admin_services, name='admin_services'),
    path('panel/payments/', views.admin_payments, name='admin_payments'),
    path('panel/bots/', views.admin_bots, name='admin_bots'),
    path('panel/settings/', views.admin_settings_view, name='admin_settings'),
        path('panel/service-action/', views.admin_service_action, name='admin_service_action'),
    path('panel/payment-action/', views.admin_payment_action, name='admin_payment_action'),
    path('panel/bot-action/', views.admin_bot_action, name='admin_bot_action'),
    path('panel/task-action/', views.admin_task_action, name='admin_task_action'),

    # 👇 YAHAN HAIN WO DONO NAYE URLs JINKE BINA ERROR AA RAHA HAI 👇
    path('panel/tasks/', views.admin_tasks, name='admin_tasks'),
    path('panel/logs/', views.admin_logs_view, name='admin_logs'), 
]
