import hmac
import hashlib
import json
from urllib.parse import parse_qsl
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from .models import UserTask # Upar imports me ise add zaroor karein
from .models import CustomUser, Service, Order, Payment, Bot, SiteSetting, Task, UserTask, Notification, Withdrawal


# ==========================================
# 💰 0. GOOGLE ADSENSE VERIFICATION
# ==========================================
def ads_txt_view(request):
    ads_txt_content = "google.com, pub-4992650101483327, DIRECT, f08c47fec0942fa0"
    return HttpResponse(ads_txt_content, content_type="text/plain")

# ==========================================
# 🌍 1. PUBLIC LANDING & BLOGS
# ==========================================
def index_view(request):
    return render(request, 'core/index.html')

def about_view(request): return render(request, 'core/about.html')
def support_view(request): return render(request, 'core/support.html')
def guide_view(request): return render(request, 'core/guide.html')
def faq_view(request): return render(request, 'core/faq.html')


# ==========================================
# 🔐 2. AUTHENTICATION (Web & Telegram)
# ==========================================
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser: 
            return redirect('custom_admin')
        return redirect('home')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        next_url = request.POST.get('next')
        
        user = authenticate(request, username=u, password=p)
        if user is not None:
            auth_login(request, user)
            if next_url: return redirect(next_url)
            if user.is_superuser: return redirect('custom_admin')
            return redirect('home')
        else:
            messages.error(request, "❌ Invalid Username or Password")
            
    return render(request, 'core/login.html')

def register_view(request):
    if request.user.is_authenticated: return redirect('home')
    return render(request, 'core/register.html')

def logout_view(request):
    logout(request)
    return redirect('login_view')

# -- TELEGRAM AUTH ENGINE --
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
                return JsonResponse({'status': 'error', 'message': 'Invalid Signature!'}, status=403)
                
            tg_id = str(tg_user.get('id'))
            tg_username = tg_user.get('username', f"user_{tg_id}")
            
            # 📸 Telegram se asli data nikalo
            first_name = tg_user.get('first_name', '')
            last_name = tg_user.get('last_name', '')
            photo_url = tg_user.get('photo_url', '')
            
            # 🚨 AUTO LOGOUT SECURITY: Agar purana user session me hai toh usko nikal do
            if request.user.is_authenticated and request.user.telegram_id != tg_id:
                logout(request)
            
            # 👤 User Create ya Fetch karo
            user, created = CustomUser.objects.get_or_create(
                telegram_id=tg_id,
                defaults={
                    'username': tg_username, 
                    'telegram_username': tg_username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'telegram_photo_url': photo_url
                }
            )
            
            # 🔄 Agar user pehle se hai, toh uski details update kardo (kya pata usne photo change ki ho)
            if not created:
                user.first_name = first_name
                user.last_name = last_name
                user.telegram_photo_url = photo_url
                if tg_username:
                    user.telegram_username = tg_username
                    user.username = tg_username
                user.save()
            
            # 🎁 Invite Logic
            if created and start_param and start_param.startswith('invite_'):
                invite_code = start_param.replace('invite_', '')
                inviter = CustomUser.objects.filter(invite_code=invite_code).first()
                if inviter:
                    user.invited_by = inviter
                    user.save()

            if user.is_banned:
                return JsonResponse({'status': 'error', 'message': 'Account banned.'}, status=403)
                
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return JsonResponse({'status': 'success', 'redirect_url': '/dashboard/'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'POST only'})
            

# ==========================================
# 📱 3. CUSTOMER DASHBOARD VIEWS
# ==========================================
@login_required(login_url='/login/')
def home_view(request):
    if request.user.is_superuser: return redirect('custom_admin')
    setting, _ = SiteSetting.objects.get_or_create(id=1)
    
    # 1. Saare active tasks bhejenge, aur jo complete ho gaye unki ID alag se bhejenge
    completed_task_ids = list(UserTask.objects.filter(user=request.user).values_list('task_id', flat=True))
    
    # 🔥 Yahan se '.exclude()' hata diya hai taaki koi task gayab na ho
    tasks = Task.objects.filter(is_active=True).order_by('-created_at')
    
    # 2. Daily Calendar Logic
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    if request.user.last_daily_claim == today:
        claimable_day = -1 # Aaj ka claim ho chuka hai
        checked_days = request.user.login_streak
    elif request.user.last_daily_claim == yesterday:
        claimable_day = request.user.login_streak + 1
        if claimable_day > 7: claimable_day = 1
        checked_days = request.user.login_streak if claimable_day > 1 else 0
    else:
        claimable_day = 1 # Streak toot gayi, wapas Day 1
        checked_days = 0
        
    return render(request, 'core/home.html', {
        'setting': setting, 
        'tasks': tasks, 
        'completed_task_ids': completed_task_ids, # 🔥 Ise naya add kiya hai
        'claimable_day': claimable_day, 
        'checked_days': checked_days
    })
    
    
@login_required(login_url='/login/')
def services_view(request):
    services = Service.objects.filter(is_active=True).order_by('-id')
    return render(request, 'core/services.html', {'services': services})

@login_required(login_url='/login/')
def new_order_view(request):
    if request.method == 'POST':
        service = get_object_or_404(Service, id=request.POST.get('service'))
        quantity = int(request.POST.get('quantity'))
        charge = (service.price_per_1000 / 1000) * quantity
        
        if request.user.wallet_balance >= charge:
            request.user.wallet_balance -= charge
            request.user.total_spent += charge
            request.user.save()
            
            if request.user.invited_by:
                request.user.invited_by.diamonds += int(charge * 5)
                request.user.invited_by.save()
                
            Order.objects.create(user=request.user, service=service, link=request.POST.get('link'), quantity=quantity, charge=charge)
            
            # 🔥 YAHAN JAYEGA NOTIFICATION 🔥
            Notification.objects.create(
                user=request.user, 
                title="Order Placed 🚀", 
                message=f"Order for {service.name} has been placed. Charge: ₹{charge}", 
                icon="fa-box", 
                color="blue"
            )
            
            messages.success(request, f"🎉 Order placed! ₹{charge} deducted.")
            return redirect('orders')
        else:
            messages.error(request, "⚠️ Insufficient balance!")
            return redirect('add_funds')
            
    return render(request, 'core/new_order.html', {'services': Service.objects.filter(is_active=True)})
    

@login_required(login_url='/login/')
def orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/orders.html', {'orders': orders})

@login_required(login_url='/login/')
def add_funds_view(request):
    setting, _ = SiteSetting.objects.get_or_create(id=1) # 👈 Yeh line add karein
    
    if request.method == 'POST':
        utr = request.POST.get('utr_number')
        if Payment.objects.filter(utr_number=utr).exists():
            messages.error(request, "❌ UTR already used.")
        else:
            Payment.objects.create(user=request.user, amount=request.POST.get('amount'), utr_number=utr)
            messages.success(request, "✅ Request submitted! Admin will verify shortly.")
        return redirect('add_funds')
        
    return render(request, 'core/add_funds.html', {'setting': setting}) # 👈 Yahan 'setting' pass karein

@login_required(login_url='/login/')
def payment_history_view(request):
    # User ki saari payments nikaal kar template me bhejenge
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/payment_history.html', {'payments': payments})
    

@login_required(login_url='/login/')
def account_view(request):
    user_orders_count = Order.objects.filter(user=request.user).count()
    return render(request, 'core/account.html', {'user_orders_count': user_orders_count})

@login_required(login_url='/login/')
def team_and_rewards(request):
    setting, _ = SiteSetting.objects.get_or_create(id=1)
    invited_friends = request.user.referrals.all().order_by('-date_joined')
    total_invites = invited_friends.count()
    
    if total_invites >= 50: tier_name, tier_icon, tier_color = "Gold", "🥇", "text-yellow-500"
    elif total_invites >= 10: tier_name, tier_icon, tier_color = "Silver", "🥈", "text-slate-400"
    else: tier_name, tier_icon, tier_color = "Bronze", "🥉", "text-orange-500"

    if request.method == 'POST' and request.POST.get('action') == 'withdraw':
        upi_id = request.POST.get('upi_id')
        try:
            withdraw_diamonds = int(request.POST.get('diamonds'))
            if withdraw_diamonds < setting.diamonds_needed_for_1_rs:
                messages.error(request, f"⚠️ Minimum {setting.diamonds_needed_for_1_rs} diamonds required!")
            elif request.user.diamonds >= withdraw_diamonds:
                rs_add = Decimal(str(withdraw_diamonds / setting.diamonds_needed_for_1_rs))
                request.user.diamonds -= withdraw_diamonds
                request.user.save()
                
                Withdrawal.objects.create(user=request.user, diamonds_used=withdraw_diamonds, amount_rs=rs_add, upi_id=upi_id)
                Notification.objects.create(user=request.user, title="Withdrawal Requested ⏳", message=f"Your request for ₹{rs_add} is pending admin approval.", icon="fa-clock-rotate-left", color="amber")
                messages.success(request, f"🎉 Withdrawal request of ₹{rs_add} submitted!")
            else:
                messages.error(request, "⚠️ Insufficient Diamonds!")
        except:
            messages.error(request, "⚠️ Invalid Input!")
        return redirect('team_rewards')

    return render(request, 'core/team.html', {'setting': setting, 'invited_friends': invited_friends, 'total_invites': total_invites, 'tier_name': tier_name, 'tier_icon': tier_icon, 'tier_color': tier_color})
        

# ==========================================
# 👑 4. SUPER ADMIN COMMAND CENTER
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
def admin_users(request):
    if not request.user.is_superuser: return redirect('home')
    platform_users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'core/admin_users.html', {'platform_users': platform_users})

@login_required(login_url='/login/')
def admin_user_action(request):
    if not request.user.is_superuser: return redirect('home')
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        target_user = get_object_or_404(CustomUser, id=user_id)
        
        if action == 'add_balance':
            amt = float(request.POST.get('amount', 0))
            target_user.wallet_balance += amt
            target_user.save()
            messages.success(request, f"Added ₹{amt} to @{target_user.username}")
        elif action == 'add_diamonds':
            amt = int(request.POST.get('amount', 0))
            target_user.diamonds += amt
            target_user.save()
            messages.success(request, f"Added {amt} Diamonds to @{target_user.username}")
        elif action == 'toggle_ban':
            target_user.is_banned = not target_user.is_banned
            target_user.save()
            status = "Banned" if target_user.is_banned else "Unbanned"
            messages.success(request, f"User @{target_user.username} is now {status}")
    return redirect('admin_users')

@login_required(login_url='/login/')
def admin_services(request):
    if not request.user.is_superuser: return redirect('home')
    platform_services = Service.objects.all().order_by('-id')
    return render(request, 'core/admin_services.html', {'platform_services': platform_services})

@login_required(login_url='/login/')
def admin_payments(request):
    if not request.user.is_superuser: return redirect('home')
    context = {
        'platform_payments': Payment.objects.all().order_by('-created_at'),
        'pending_count': Payment.objects.filter(status='Pending').count(),
    }
    return render(request, 'core/admin_payments.html', context)

@login_required(login_url='/login/')
def admin_bots(request):
    if not request.user.is_superuser: return redirect('home')
    context = {
        'platform_bots': Bot.objects.all().order_by('-id'),
        'active_bots_count': Bot.objects.filter(is_active=True, is_banned=False).count(),
    }
    return render(request, 'core/admin_bots.html', context)

@login_required(login_url='/login/')
def admin_task_action(request):
    if not request.user.is_superuser: return redirect('home')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            Task.objects.create(
                title=request.POST.get('title'),
                task_type=request.POST.get('task_type', 'custom'),
                icon_class=request.POST.get('icon_class', 'fa-solid fa-star'),
                link=request.POST.get('link', ''),
                reward_diamonds=int(request.POST.get('reward_diamonds', 0))
            )
            messages.success(request, "New Reward Task Created!")
            
        else:
            task = get_object_or_404(Task, id=request.POST.get('task_id'))
            if action == 'toggle':
                task.is_active = not task.is_active
                task.save()
                messages.success(request, "Task status updated!")
            elif action == 'delete':
                task.delete()
                messages.success(request, "Task deleted permanently!")
                
    return redirect('admin_tasks')

@login_required(login_url='/login/')
def admin_logs_view(request):
    if not request.user.is_superuser: return redirect('home')
    # Admin ko pure system ke notifications/logs dikhenge
    logs = Notification.objects.all().order_by('-created_at')[:100]
    return render(request, 'core/admin_logs.html', {'logs': logs})
    
@login_required(login_url='/login/')
def admin_settings_view(request):
    if not request.user.is_superuser: return redirect('home')
    setting, _ = SiteSetting.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        setting.platform_name = request.POST.get('platform_name', setting.platform_name)
        setting.upi_id = request.POST.get('upi_id', setting.upi_id)
        setting.qr_image_url = request.POST.get('qr_image_url', setting.qr_image_url)
        setting.support_telegram = request.POST.get('support_telegram', setting.support_telegram)
        setting.telegram_channel = request.POST.get('telegram_channel', setting.telegram_channel)
        setting.min_deposit = request.POST.get('min_deposit', setting.min_deposit)
        setting.diamonds_per_rupee = request.POST.get('diamonds_per_rupee', setting.diamonds_per_rupee)
        setting.diamonds_needed_for_1_rs = request.POST.get('diamonds_needed_for_1_rs', setting.diamonds_needed_for_1_rs)
        
        setting.maintenance_mode = 'maintenance_mode' in request.POST
        setting.save()

        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.email = request.POST.get('email', request.user.email)
        
        if 'profile_image' in request.FILES:
            request.user.profile_image = request.FILES['profile_image']
            
        request.user.save()

        messages.success(request, "System settings and profile updated successfully!")
        return redirect('admin_settings')

    return render(request, 'core/admin_settings.html', {'setting': setting})
        
# ==========================================
# ⚡ SUPER ADMIN ACTION CONTROLLERS (Functional Logic)
# ==========================================

@login_required(login_url='/login/')
def admin_service_action(request):
    if not request.user.is_superuser: return redirect('home')
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            Service.objects.create(
                name=request.POST.get('name'),
                platform=request.POST.get('platform'),
                price_per_1000=request.POST.get('price_per_1000'),
                min_order=request.POST.get('min_order', 10),
                max_order=request.POST.get('max_order', 10000)
            )
            messages.success(request, "New Service added successfully!")
            
        else:
            svc = get_object_or_404(Service, id=request.POST.get('service_id'))
            if action == 'toggle':
                svc.is_active = not svc.is_active
                svc.save()
                messages.success(request, "Service status updated!")
            elif action == 'delete':
                svc.delete()
                messages.success(request, "Service deleted permanently!")
                
    return redirect('admin_services')


@login_required(login_url='/login/')

@login_required(login_url='/login/')
def admin_payment_action(request):
    if not request.user.is_superuser: return redirect('home')
    if request.method == 'POST':
        payment = get_object_or_404(Payment, id=request.POST.get('payment_id'))
        if request.POST.get('action') == 'approve' and payment.status == 'Pending':
            payment.status = 'Completed'
            payment.user.wallet_balance += payment.amount
            payment.user.save()
            payment.save()
            
            # 🔥 SUCCESS NOTIFICATION 🔥
            Notification.objects.create(
                user=payment.user, 
                title="Payment Approved 💸", 
                message=f"₹{payment.amount} has been successfully added to your wallet.", 
                icon="fa-money-bill-trend-up", 
                color="emerald"
            )
            messages.success(request, f"Approved! ₹{payment.amount} added.")
            
        elif request.POST.get('action') == 'reject':
            payment.status = 'Rejected'
            payment.save()
            
            # 🔥 REJECT NOTIFICATION 🔥
            Notification.objects.create(
                user=payment.user, 
                title="Payment Rejected ❌", 
                message="Your recent payment request was rejected by the admin. Check UTR.", 
                icon="fa-circle-xmark", 
                color="rose"
            )
            messages.error(request, "Payment Rejected.")
            
    return redirect('admin_payments')
    

@login_required(login_url='/login/')
def admin_bot_action(request):
    if not request.user.is_superuser: return redirect('home')
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            # 🤖 Auto-Generate Bot Name (jaise Node-01, Node-02)
            bot_count = Bot.objects.count() + 1
            auto_name = f"Worker-Node-{bot_count:02d}"
            
            # Cookies input se lena
            cookies_data = request.POST.get('cookies', '')
            
            Bot.objects.create(name=auto_name, cookies=cookies_data)
            messages.success(request, f"🚀 {auto_name} Deployed Successfully with Cookies!")
            
        else:
            bot = get_object_or_404(Bot, id=request.POST.get('bot_id'))
            if action == 'toggle':
                bot.is_active = not bot.is_active
                bot.save()
                messages.success(request, f"{bot.name} power state changed!")
            elif action == 'delete':
                bot.delete()
                messages.success(request, "Bot Engine Terminated.")
                
    return redirect('admin_bots')
                
# 👇 YEH FUNCTION MISSING THA 👇
@login_required(login_url='/login/')
def admin_tasks(request):
    if not request.user.is_superuser: return redirect('home')
    # Aapke model ke hisaab se order by '-created_at' rakha hai
    tasks = Task.objects.all().order_by('-created_at')
    return render(request, 'core/admin_tasks.html', {'tasks': tasks})
    

@login_required
def claim_daily_view(request):
    if request.method == 'POST':
        user = request.user
        today = timezone.now().date()
        
        if user.last_daily_claim == today:
            return JsonResponse({'status': 'error', 'message': 'Already claimed today!'})
            
        if user.last_daily_claim == today - timedelta(days=1):
            user.login_streak += 1
        else:
            user.login_streak = 1 # Reset if streak broken
            
        if user.login_streak > 7:
            user.login_streak = 1
            
        reward = 50 if user.login_streak == 7 else 10
        user.diamonds += reward
        user.last_daily_claim = today
        user.save()
        
        return JsonResponse({'status': 'success', 'message': f'Claimed {reward} 💎!', 'diamonds': user.diamonds})

@login_required
def claim_task_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        task = get_object_or_404(Task, id=data.get('task_id'))
        
        if UserTask.objects.filter(user=request.user, task=task).exists():
            return JsonResponse({'status': 'error', 'message': 'Task already claimed!'})
            
        UserTask.objects.create(user=request.user, task=task)
        request.user.diamonds += task.reward_diamonds
        request.user.save()
        
        return JsonResponse({'status': 'success', 'message': f'Task Complete! +{task.reward_diamonds} 💎', 'diamonds': request.user.diamonds})
    
@login_required(login_url='/login/')
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    # Page open hote hi sabhi ko 'Read' mark kar do
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, 'core/notifications.html', {'notifications': notifs})
    
@login_required(login_url='/login/')
def withdraw_history_view(request):
    withdrawals = Withdrawal.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/withdraw_history.html', {'withdrawals': withdrawals})

@login_required(login_url='/login/')
def admin_withdrawals(request):
    if not request.user.is_superuser: return redirect('home')
    withdrawals = Withdrawal.objects.all().order_by('-created_at')
    return render(request, 'core/admin_withdrawals.html', {'platform_withdrawals': withdrawals, 'pending_count': withdrawals.filter(status='Pending').count()})

@login_required(login_url='/login/')
def admin_withdrawal_action(request):
    if not request.user.is_superuser: return redirect('home')
    if request.method == 'POST':
        withdraw = get_object_or_404(Withdrawal, id=request.POST.get('withdraw_id'))
        if request.POST.get('action') == 'approve' and withdraw.status == 'Pending':
            withdraw.status = 'Completed'
            withdraw.save()
            Notification.objects.create(user=withdraw.user, title="Withdrawal Approved 💸", message=f"₹{withdraw.amount_rs} has been sent to your UPI.", icon="fa-money-bill-wave", color="emerald")
            messages.success(request, f"Approved! (Please manually send ₹{withdraw.amount_rs} to {withdraw.upi_id})")
        elif request.POST.get('action') == 'reject' and withdraw.status == 'Pending':
            withdraw.status = 'Rejected'
            withdraw.user.diamonds += withdraw.diamonds_used # Refund diamonds
            withdraw.user.save()
            withdraw.save()
            Notification.objects.create(user=withdraw.user, title="Withdrawal Rejected ❌", message="Your withdrawal request was rejected. Diamonds refunded.", icon="fa-circle-xmark", color="rose")
            messages.error(request, "Withdrawal Rejected & Diamonds Refunded.")
    return redirect('admin_withdrawals')
        
