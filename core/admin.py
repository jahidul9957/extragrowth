from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Bot, Payment, Service, Order

# 1. User Management (Wallet aur Ban System ke sath)
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'wallet_balance', 'is_active', 'is_banned')
    list_filter = ('is_banned', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'ip_address', 'invite_code')
    # Naye fields ko admin form mein dikhane ke liye
    fieldsets = UserAdmin.fieldsets + (
        ('SMM Panel Details', {'fields': ('wallet_balance', 'total_spent', 'ip_address', 'invite_code', 'team_code', 'is_banned')}),
    )

# 2. Bot Management
@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'is_banned', 'created_at')
    list_filter = ('is_active', 'is_banned')
    search_fields = ('name',)
    list_editable = ('is_active', 'is_banned') # Ek click mein on/off karein

# 3. Payment System (1-Click Approve)
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'utr_number', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('utr_number', 'user__username')
    list_editable = ('status',) # Admin panel se direct Approve/Reject karein

# 4. Service Management
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price_per_1000', 'min_order', 'max_order')
    list_filter = ('category',) # Category ke hisaab se filter karne ke liye
    search_fields = ('name', 'category')
    list_editable = ('price_per_1000', 'category') # Bahar se hi price aur category badalne ke liye
    

# 5. Order Management
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service', 'quantity', 'charge', 'status', 'created_at')
    list_filter = ('status', 'service')
    search_fields = ('user__username', 'link')
    list_editable = ('status',) # Order status direct change karein
    
