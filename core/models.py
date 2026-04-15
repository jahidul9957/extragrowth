from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_banned = models.BooleanField(default=False)

class Service(models.Model):
    name = models.CharField(max_length=200)
    price_per_1000 = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    link = models.URLField()
    quantity = models.IntegerField()
    charge = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='Pending')
    
    # 🌟 YEH NAYA FIELD HAI (Progress Bar Aur Automation ke liye)
    delivered_quantity = models.IntegerField(default=0) 
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"

class Payment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    utr_number = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

class Bot(models.Model):
    name = models.CharField(max_length=100)
    cookies_json = models.TextField(help_text='Format: [{"name": "...", "value": "..."}]')
    is_active = models.BooleanField(default=True)
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return self.name
