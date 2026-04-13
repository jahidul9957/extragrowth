from django.shortcuts import render, redirect
from .models import Service, Order

def home(request):
    return render(request, 'core/home.html')

def login_view(request):
    # Registration aur OTP ka logic hum aage yahan add karenge
    return render(request, 'core/login.html')

def services(request):
    # Database se saari active services nikal kar page par bhejna
    services_list = Service.objects.filter(is_active=True)
    return render(request, 'core/services.html', {'services': services_list})

def team(request):
    return render(request, 'core/team.html')

def profile(request):
    return render(request, 'core/profile.html')
  
