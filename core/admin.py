from django.contrib import admin
from .models import CustomUser, Service, Order, Payment, Bot

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    # Sirf wahi fields jo CustomUser model mein hain
    list_display = ['username', 'email', 'wallet_balance', 'total_spent', 'is_banned']
    list_editable = ['wallet_balance', 'is_banned']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    # 'category', 'min_order', 'max_order' ko hata diya gaya hai
    list_display = ['id', 'name', 'price_per_1000']
    list_editable = ['name', 'price_per_1000']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'service', 'quantity', 'status', 'delivered_quantity', 'created_at']
    list_filter = ['status', 'created_at']
    list_editable = ['status']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'utr_number', 'status', 'created_at']
    list_filter = ['status']
    list_editable = ['status']

@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    # 'created_at' ko hata diya gaya hai kyunki model mein nahi hai
    list_display = ['id', 'name', 'is_active', 'is_banned']
    list_editable = ['is_active', 'is_banned']
