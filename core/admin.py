from django.contrib import admin
from django.utils.html import format_html # Naya import
from .models import CustomUser, Order, Bot, Service, Payment

# Baaki sab waisa hi rahega...

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    # 'login_as_button' ko list me add kiya
    list_display = ('username', 'email', 'wallet_balance', 'total_spent', 'login_as_button')
    search_fields = ('username', 'email')

    # 🪄 Naya Jaadui Button
    def login_as_button(self, obj):
        return format_html(
            '<a class="button" style="background-color:#417690; color:white; padding:5px 10px; border-radius:4px; font-weight:bold; text-decoration:none;" href="/login-as/{}/">🕵️‍♂️ Login as User</a>', 
            obj.id
        )
    login_as_button.short_description = 'Impersonate (God Mode)'


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
