import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. THE USER MODEL (Includes TMA & Diamond System)
class CustomUser(AbstractUser):
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_banned = models.BooleanField(default=False)
    
    # Telegram Mini App Features
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    telegram_username = models.CharField(max_length=100, null=True, blank=True)
    
    # Invite System & Diamonds
    invite_code = models.CharField(max_length=10, unique=True, null=True, blank=True)
    invited_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    diamonds = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = str(uuid.uuid4().hex)[:8].lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

# 2. SERVICES MODEL
class Service(models.Model):
    name = models.CharField(max_length=255)
    platform = models.CharField(max_length=50, default="YouTube") # YouTube, Instagram, FreeFire
    price_per_1000 = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.id} - {self.name}"

# 3. ORDERS MODEL
class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Completed', 'Completed'),
        ('Canceled', 'Canceled'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    link = models.URLField()
    quantity = models.IntegerField()
    charge = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

# 4. PAYMENTS (Add Funds) MODEL
class Payment(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Rejected', 'Rejected'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    utr_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id} - {self.user.username} - ₹{self.amount}"

# 5. BOTS (Playwright Engines) MODEL
class Bot(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_banned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
