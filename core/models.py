from django.db import models
from django.contrib.auth.models import AbstractUser
import random
import string

class CustomUser(AbstractUser):
    mobile_number = models.CharField(max_length=15, unique=True)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    referral_code = models.CharField(max_length=10, unique=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='team_members')
    total_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username or self.mobile_number

class Service(models.Model):
    name = models.CharField(max_length=255)
    quantity = models.IntegerField(help_text="Example: 50")
    price_inr = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - ₹{self.price_inr}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    target_link = models.URLField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.mobile_number}"
  
