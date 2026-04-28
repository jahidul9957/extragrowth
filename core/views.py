import hmac
import hashlib
import json
from urllib.parse import parse_qsl
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Sum

# Apne models import kar rahe hain
from .models import CustomUser, Service, Order, Payment, Bot

# ==========================================
# 🚀 1. TELEGRAM SILENT AUTH ENGINE (TMA)
# ==========================================
TELEGRAM_BOT_TOKEN = "8691081519:AAEVWnllssUWpRvYOAUcA9hgwKZs0oKV3Hc"

def verify_telegram_data(init_data):
    try:
        parsed_data = dict(parse_qsl(init_data))
        hash_val = parsed_data.pop('hash', None)
        if not hash_val: return False, None, None
            
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(parsed_data.items())])
        secret_key = hmac.new(b"WebAppData", TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256).digest()
        calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if calc_hash == hash_val:
            user_data = json.loads(parsed_data.get('user', '{}'))
            start_param = parsed_data.get('start_param', None) 
            return True, user_data, start_param
    except Exception as e:
        print(f"Auth Error: {e}")
    return False, None, None

@csrf_exempt
def telegram_auth_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            init_data = data.get('initData')
            is_valid, tg_user, start_param = verify_telegram_data(init_data)
            
            if not is_valid or not tg_user:
                return JsonResponse({'status': 'error', 'message': 'Invalid Signature! Hacker Alert 🚨'}, status=403)
                
            tg_id = tg_user.get('id')
            tg_username = tg_user.get('username', f"user_{tg_id}")
            
            user, created = CustomUser.objects.get_or_create(
                telegram_id=tg_id,
                defaults={'username': tg_username, 'telegram_username': tg_username}
            )
            
            # Apply Invite/Referral Logic for New Users
            if created and start_param and start_param.startswith('invite_'):
                invite_code = start_param.replace('invite_', '')
                inviter = CustomUser.objects.filter(invite_code=invite_code).first()
                if inviter:
                    user.invited_by = inviter
                    user.save()

            if user.is_banned:
                return JsonResponse({'status': 'error', 'message': 'Account banned.'}, status=403)
                
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return JsonResponse({'status': 'success', 'redirect_url': '/'}) # Seedha Home par bhejo
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'POST only'})


# ==========================================
# 📱 2. FRONTEND VIEWS (Customer App)
# ==========================================
@login_required(login_url='/login/')
def home_view(request):
    return render(request, 'core/home.html')

@login_required(login_url='/login/')
def services_view(request):
    services = Service.objects.filter(is_active=True).order_by('-id')
    return render(request, 'core/services.html', {'services': services})

@login_required(login_url='/login/')
def new_order_view(request):
    if request.method == 'POST':
        service_id = request.POST.get('service')
        link = request.POST.get('link')
        quantity = int(request.POST.get('quantity'))
        
        service = get_object_or_404(Service, id=service_id)
        charge = (service.price_per_1000 / 1000) * quantity
        
        if request.user.wallet_balance >= charge:
            # Pese kaato
            request.user.wallet_balance -= charge
            request.user.total_spent += charge
            request.user.save()
            
            # 💎 DIAMOND REWARD SYSTEM (Give diamonds to Inviter)
            if request.user.invited_by:
                earned_diamonds = int(charge * 5) # Formula: ₹1 spent = 5 Diamonds
                inviter = request.user.invited_by
                inviter.diamonds += earned_diamonds
                inviter.save()
            
            Order.objects.create(user=request.user, service=service, link=link, quantity=quantity, charge=charge)
            messages.success(request, f"🎉 Order placed successfully! ₹{charge} deducted.")
            return redirect('orders')
        else:
            messages.error(request, "⚠️ Insufficient balance! Please add funds.")
            return redirect('add_funds')
            
    services = Service.objects.filter(is_active=True)
    return render(request, 'core/new_order.html', {'services': services})

@login_required(login_url='/login/')
def orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/orders.html', {'orders': orders})

@login_required(login_url='/login/')
def add_funds_view(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        utr_number = request.POST.get('utr_number')
        
        if Payment.objects.filter(utr_number=utr_number).exists():
            messages.error(request, "❌ This UTR number has already been used.")
        else:
            Payment.objects.create(user=request.user, amount=amount, utr_number=utr_number)
            messages.success(request, "✅ Payment request submitted! Admin will verify it shortly.")
        return redirect('add_funds')
    return render(request, 'core/add_funds.html')

@login_required(login_url='/login/')
def account_view(request):
    user_orders_count = Order.objects.filter(user=request.user).count()
    return render(request, 'core/account.html', {'user_orders_count': user_orders_count})

@login_required(login_url='/login/')
def team_and_rewards(request):
    invited_friends = request.user.referrals.all().order_by('-date_joined')
    total_invites = invited_friends.count()
    active_invites = invited_friends.filter(total_spent__gt=0).count()
    
    # 🏆 Level System
    if total_invites >= 50:
        tier_name, tier_icon, tier_color = "Gold", "🥇", "text-yellow-500"
    elif total_invites >= 10:
        tier_name, tier_icon, tier_color = "Silver", "🥈", "text-slate-400"
    else:
        tier_name, tier_icon, tier_color = "Bronze", "🥉", "text-orange-500"

    # Redeem Logic (50 Diamonds = ₹1)
    if request.method == 'POST' and request.POST.get('action') == 'redeem':
        if request.user.diamonds >= 50:
            rs_to_add = request.user.diamonds / 50
            request.user.wallet_balance += rs_to_add
            request.user.diamonds = 0  # Baad me ise remainder logic (diamonds % 50) se update kar sakte hain
            request.user.save()
            messages.success(request, f"🎉 Success! ₹{rs_to_add} added to your wallet.")
        else:
            messages.error(request, "⚠️ Minimum 50 Diamonds required to redeem!")
        return redirect('team_rewards')

    context = {
        'invited_friends': invited_friends, 'total_invites': total_invites,
        'active_invites': active_invites, 'tier_name': tier_name,
        'tier_icon': tier_icon, 'tier_color': tier_color,
    }
    return render(request, 'core/team.html', context)


# ==========================================
# 📘 3. SUPPORT & INFO PAGES (Premium UI)
# ==========================================
@login_required(login_url='/login/')
def about_view(request):
    return render(request, 'core/about.html')

@login_required(login_url='/login/')
def support_view(request):
    return render(request, 'core/support.html')

@login_required(login_url='/login/')
def guide_view(request):
    return render(request, 'core/guide.html')

@login_required(login_url='/login/')
def faq_view(request):
    return render(request, 'core/faq.html')


# ==========================================
# 👑 4. SUPER ADMIN VIEWS (The Hacker Dashboard)
# ==========================================
@login_required(login_url='/login/')
def custom_admin_dashboard(request):
    if not request.user.is_superuser: return redirect('home')
    
    context = {
        'total_users': CustomUser.objects.count(),
        'active_bots': Bot.objects.filter(is_active=True).count(),
        'orders_today': Order.objects.filter(created_at__date=timezone.now().date()).count(),
        'total_revenue': Order.objects.filter(status='Completed').aggregate(total=Sum('charge'))['total'] or 0.00,
        'recent_orders': Order.objects.all().order_by('-created_at')[:5],
    }
    return render(request, 'core/admin_dashboard.html', context)

@login_required(login_url='/login/')
def admin_users_view(request):
    if not request.user.is_superuser: return redirect('home')
    platform_users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'core/admin_users.html', {'platform_users': platform_users})

@login_required(login_url='/login/')
def admin_services_view(request):
    if not request.user.is_superuser: return redirect('home')
    platform_services = Service.objects.all().order_by('-id')
    return render(request, 'core/admin_services.html', {'platform_services': platform_services})

@login_required(login_url='/login/')
def admin_payments_view(request):
    if not request.user.is_superuser: return redirect('home')
    context = {
        'platform_payments': Payment.objects.all().order_by('-created_at'),
        'pending_count': Payment.objects.filter(status='Pending').count(),
    }
    return render(request, 'core/admin_payments.html', context)

@login_required(login_url='/login/')
def admin_bots_view(request):
    if not request.user.is_superuser: return redirect('home')
    context = {
        'platform_bots': Bot.objects.all().order_by('-id'),
        'active_bots_count': Bot.objects.filter(is_active=True, is_banned=False).count(),
    }
    return render(request, 'core/admin_bots.html', context)

@login_required(login_url='/login/')
def login_as_user(request, user_id):
    if not request.user.is_superuser: return redirect('home')
    target_user = get_object_or_404(CustomUser, id=user_id)
    auth_login(request, target_user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect('home')


# ==========================================
# 🔐 5. NORMAL WEB AUTH (Fallback)
# ==========================================
def login_view(request):
    if request.user.is_authenticated: return redirect('home')
    # Yahan humne JS lagayi thi jo automatically Telegram se login karegi
    return render(request, 'core/login.html')

def register_view(request):
    if request.user.is_authenticated: return redirect('home')
    return render(request, 'core/register.html')

def logout_view(request):
    logout(request)
    return redirect('login')
        
