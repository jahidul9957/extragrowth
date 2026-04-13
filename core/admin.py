from django.contrib import admin
from .models import CustomUser, Service, Order

# Admin panel ko sundar banane ke liye customization
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'mobile_number', 'wallet_balance', 'referral_code', 'total_commission')
    search_fields = ('username', 'mobile_number')

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'price_inr', 'is_active')
    list_editable = ('price_inr', 'is_active')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    list_editable = ('status',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Order, OrderAdmin)
