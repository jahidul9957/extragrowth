from django.db import models
from django.contrib.auth.models import AbstractUser
import random
import string

# 1. Advanced User Model
class CustomUser(AbstractUser):
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Referral System
    invite_code = models.CharField(max_length=10, unique=True, blank=True)
    team_code = models.CharField(max_length=10, null=True, blank=True)
    
    # Security
    is_banned = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        # Auto-generate unique invite code for new users
        if not self.invite_code:
            self.invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

# 2. Bot Management System
class Bot(models.fields.Model):
    name = models.CharField(max_length=100)
    cookies_json = models.TextField(help_text="Paste JSON cookies here")
    is_active = models.BooleanField(default=True)
    is_banned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {'Active' if self.is_active else 'Inactive'}"

# 3. Payment & UTR System
class Payment(models.fields.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    utr_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - ₹{self.amount} ({self.status})"

# 4. Service & Order Models (Aapke purane models thode upgrade ke sath)
class Service(models.fields.Model):
    category = models.CharField(max_length=100, default="General", help_text="Example: YouTube Subscribers, IG Followers")
    name = models.CharField(max_length=255, help_text="Example: Real Active Subscribers")
    price_per_1000 = models.DecimalField(max_digits=10, decimal_places=2)
    min_order = models.IntegerField(default=100)
    max_order = models.IntegerField(default=10000)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"[{self.category}] {self.name}"
        

class Order(models.fields.Model):
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
    
