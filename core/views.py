from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Payment, Service, Order, CustomUser

# ==========================================
# 🔐 USER AUTHENTICATION SYSTEM
# ==========================================

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        u = request.POST.get('username')
        e = request.POST.get('email')
        p = request.POST.get('password')
        
        if CustomUser.objects.filter(username=u).exists():
            messages.error(request, "⚠️ Username already taken! Choose another.")
        else:
            user = CustomUser.objects.create_user(username=u, email=e, password=p)
            user.save()
            messages.success(request, "🎉 Account created successfully! Please login.")
            return redirect('login')
            
    return render(request, 'core/register.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        
        if user is not None:
            if user.is_banned:
                messages.error(request, "🚫 Your account has been banned by the Admin.")
            else:
                auth_login(request, user)
                messages.success(request, f"Welcome back, {u}! 🚀")
                return redirect('home')
        else:
            messages.error(request, "⚠️ Invalid username or password.")
            
    return render(request, 'core/login.html')

def logout_view(request):
    auth_logout(request)
    messages.info(request, "👋 You have been logged out successfully.")
    return redirect('login')

# ==========================================
# 🌟 BASIC PAGES (Home, Services)
# ==========================================

def home(request):
    # Platform ke Global Stats
    total_platform_users = CustomUser.objects.count() + 2500
    total_platform_orders = Order.objects.count() + 15400

    context = {
        'total_platform_users': total_platform_users,
        'total_platform_orders': total_platform_orders,
    }

    # Agar user login hai, toh personal stats bhejein
    if request.user.is_authenticated:
        context['user_orders_count'] = Order.objects.filter(user=request.user).count()
        context['user_pending_orders'] = Order.objects.filter(user=request.user, status='Pending').count()

    return render(request, 'core/home.html', context)

def services(request):
    services_list = Service.objects.all()
    return render(request, 'core/services.html', {'services': services_list})

# ==========================================
# 🚀 NEXTGEN AI DEV - CORE SMM FEATURES
# ==========================================

@login_required(login_url='/login/')
def add_funds(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        utr_number = request.POST.get('utr_number')
        
        if amount and utr_number:
            Payment.objects.create(user=request.user, amount=amount, utr_number=utr_number, status='Pending')
            messages.success(request, f"₹{amount} payment request sent successfully! Wait for approval.")
        else:
            messages.error(request, "Please enter both Amount and UTR Number.")
    return render(request, 'core/add_funds.html')

@login_required(login_url='/login/')
def new_order(request):
    services_list = Service.objects.all()
    if request.method == 'POST':
        service_id = request.POST.get('service')
        link = request.POST.get('link')
        quantity = int(request.POST.get('quantity', 0))
        
        if service_id and link and quantity > 0:
            try:
                service = Service.objects.get(id=service_id)
                charge = (service.price_per_1000 / 1000) * quantity
                
                if request.user.wallet_balance >= charge:
                    request.user.wallet_balance -= charge
                    request.user.total_spent += charge
                    request.user.save()
                    
                    Order.objects.create(user=request.user, service=service, link=link, quantity=quantity, charge=charge, status='Pending')
                    messages.success(request, f"🎉 Order placed successfully! Charge: ₹{charge}")
                else:
                    messages.error(request, "⚠️ Insufficient balance! Please add funds.")
            except Exception as e:
                messages.error(request, "⚠️ Error processing order.")
        else:
            messages.error(request, "⚠️ Please fill details correctly.")
    return render(request, 'core/new_order.html', {'services': services_list})

@login_required(login_url='/login/')
def orders(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/orders.html', {'orders': user_orders})
        
