from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.crypto import get_random_string

# ==========================================
# 1. USER MODEL (Customized for TMA & Admin)
# ==========================================
class CustomUser(AbstractUser):
    # Telegram Authentication Data
    telegram_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    telegram_username = models.CharField(max_length=100, null=True, blank=True)
    telegram_photo_url = models.URLField(max_length=500, blank=True, null=True)
        # (Existing CustomUser code ke andar ye add karein)
    login_streak = models.IntegerField(default=0)
    last_daily_claim = models.DateField(null=True, blank=True)
    
    # Financials & Rewards
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    diamonds = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Referral System
    invite_code = models.CharField(max_length=20, unique=True, blank=True)
    invited_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    
    # Admin & Profile Enhancements
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, default="India")
    
    # Security
    is_banned = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Auto-generate invite code on account creation
        if not self.invite_code:
            self.invite_code = get_random_string(8).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"@{self.username}"


# ==========================================
# 2. TASK MODEL (For Earning Diamonds)
# ==========================================
class Task(models.Model):
    TASK_TYPES = (
        ('telegram', 'Telegram'),
        ('youtube', 'YouTube'),
        ('daily', 'Daily Login'),
        ('custom', 'Custom Task'),
    )
    title = models.CharField(max_length=200)
    reward_diamonds = models.IntegerField(default=50)
    link = models.URLField(max_length=500, blank=True, null=True)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, default='telegram')
    icon_class = models.CharField(max_length=100, default="fa-brands fa-telegram") # FontAwesome Class
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} (+{self.reward_diamonds} Diamonds)"


# ==========================================
# 3. SERVICE MODEL (YouTube, IG, etc.)
# ==========================================
class Service(models.Model):
    PLATFORM_CHOICES = (
        ('youtube', 'YouTube'),
        ('instagram', 'Instagram'),
        ('telegram', 'Telegram'),
        ('facebook', 'Facebook'),
    )
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES, default='instagram')
    name = models.CharField(max_length=255)
    price_per_1000 = models.DecimalField(max_digits=8, decimal_places=2)
    min_order = models.IntegerField(default=10)
    max_order = models.IntegerField(default=10000)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.platform.upper()} - {self.name}"


# ==========================================
# 4. ORDER MODEL (User purchases)
# ==========================================
class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders')
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)
    link = models.URLField(max_length=500)
    quantity = models.IntegerField()
    charge = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"


# ==========================================
# 5. PAYMENT MODEL (Add Funds via UTR)
# ==========================================
class Payment(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Rejected', 'Rejected'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    utr_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Rs.{self.amount} by {self.user.username} ({self.status})"


# ==========================================
# 6. BOT ENGINE MODEL (Playwright automation)
# ==========================================
class Bot(models.Model):
    name = models.CharField(max_length=100)
    # 👇 Yeh nayi line add karein Cookies save karne ke liye
    cookies = models.TextField(blank=True, null=True) 
    
    is_active = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
        


# ==========================================
# 7. SYSTEM SETTINGS MODEL (For Settings Page)
# ==========================================
class SiteSetting(models.Model):
    # Basic Info
    platform_name = models.CharField(max_length=100, default="NextGen SMM")
    maintenance_mode = models.BooleanField(default=False)
    
    # Support & Links
    support_telegram = models.CharField(max_length=100, default="@NextGenSupportBot")
    telegram_channel = models.URLField(default="https://t.me/nextgen_updates")
    
    # Payment Settings
    upi_id = models.CharField(max_length=100, default="admin@ybl")
    qr_image_url = models.URLField(blank=True, null=True)
    min_deposit = models.IntegerField(default=10)
    
    # Referral Rules
    diamonds_per_rupee = models.IntegerField(default=5)
    diamonds_needed_for_1_rs = models.IntegerField(default=50)

    def __str__(self):
        return "Platform Global Settings"
    
class UserTask(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'task') # Ek user 1 task ko 1 hi baar karega
    
