import hmac
import hashlib
import json
import threading
import traceback
import time
import os
from urllib.parse import parse_qsl
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta

# Playwright & Stealth
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

from .models import CustomUser, Service, Order, Payment, Bot, SiteSetting, Task, UserTask, Notification, Withdrawal, RewardHistory


# ==========================================
# 🤖 0. ULTIMATE BOT ENGINE (STEALTH + JS INJECT)
# =========================================

def run_bot_in_background(order_id):
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    
    try:
        from .models import Order, Bot, Notification
        order = Order.objects.get(id=order_id)
        
        bots = Bot.objects.filter(is_active=True, is_banned=False)[:order.quantity]
        
        if not bots:
            print("❌ No active bots found in database!")
            order.status = 'Failed'
            order.save()
            return
            
        order.status = 'Processing'
        order.save()
        
        # 🔥 THE FIX: Database field ki jagah local variable '0' set kar diya
        success_count = 0 
        target_link = order.link 
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            
            for bot in bots:
                try:
                    raw_cookies = json.loads(bot.cookies) 
                    clean_cookies = []
                    
                    for c in raw_cookies:
                        if c.get("sameSite") == "no_restriction":
                            c["sameSite"] = "None"
                        elif c.get("sameSite") not in ["Strict", "Lax", "None"]:
                            c.pop("sameSite", None)
                            
                        domain = c.get("domain", "")
                        if "youtube" in domain or "googleusercontent" in domain:
                            c["domain"] = ".youtube.com"
                            
                        clean_cookies.append(c)

                    context = browser.new_context(
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        locale='en-US'
                    )
                    
                    context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    context.add_cookies(clean_cookies)
                    
                    page = context.new_page()
                    stealth_sync(page)
                    
                    print(f"\n🚀 Bot [{bot.name}] is navigating to: {target_link}")
                    page.goto(target_link, timeout=60000)
                    page.wait_for_load_state("networkidle")
                    time.sleep(5) 
                    
                    try:
                        js_code = """
                        () => {
                            const buttons = document.querySelectorAll('ytd-subscribe-button-renderer, yt-button-shape, button, div[role="button"]');
                            for(let b of buttons) {
                                let text = (b.innerText || "").toLowerCase().trim();
                                if(text.includes('subscribed') || text.includes('सदस्यता ली') || text.includes('सदस्य हैं')) return "ALREADY_SUBSCRIBED";
                                if(text === 'subscribe' || text.includes('सदस्यता लें') || text.includes('subscribe')) {
                                    b.click();
                                    return "CLICKED";
                                }
                            }
                            return "NOT_FOUND";
                        }
                        """
                        result = page.evaluate(js_code)
                        print(f"🧠 JS Engine Result: {result}")
                        
                        if result == "ALREADY_SUBSCRIBED":
                            success_count += 1
                        elif result == "CLICKED":
                            time.sleep(2)
                            success_count += 1
                        else:
                            print("📸 DANGER: JS Injection ko bhi button nahi mila!")
                            
                    except Exception as btn_error:
                        print(f"📸 CRASH: Error: {btn_error}")
                        
                    context.close()
                except Exception as e:
                    print(f"❌ Bot [{bot.name}] Failed: {e}")
                time.sleep(4)
                
            browser.close()
            
            # Final Status Update
            if success_count >= order.quantity:
                order.status = 'Completed'
            elif success_count > 0:
                order.status = 'Partial'
            else:
                order.status = 'Failed'
            order.save()
            
            print(f"🏁 Order Status Update: {order.status} (Delivered: {success_count}/{order.quantity})")
            
            Notification.objects.create(
                user=order.user,
                title="🤖 Order Processed",
                message=f"Order #{order.id} finished. Delivered: {success_count}/{order.quantity}",
                icon="fa-robot",
                color="blue"
            )
            
    except Exception as e:
        print(f"🚨 Playwright Engine Error: {e}")
        try:
            order = Order.objects.get(id=order_id)
            order.status = 'Failed'
            order.save()
        except: pass

# ==========================================
# 💰 0. GOOGLE ADSENSE VERIFICATION
# ==========================================
def ads_txt_view(request):
    ads_txt_content = "google.com, pub-4992650101483327, DIRECT, f08c47fec0942fa0"
    return HttpResponse(ads_txt_content, content_type="text/plain")

# ==========================================
# 🌍 1. PUBLIC LANDING & BLOGS
# ==========================================
def index_view(request): return render(request, 'core/index.html')
def about_view(request): return render(request, 'core/about.html')
def support_view(request): return render(request, 'core/support.html')
def guide_view(request): return render(request, 'core/guide.html')
def faq_view(request): return render(request, 'core/faq.html')


# ==========================================
# 🔐 2. AUTHENTICATION (Web & Telegram)
# ==========================================
def register_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser: return redirect('custom_admin')
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
            return redirect('login_view')
    return render(request, 'core/register.html')

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser: return redirect('custom_admin')
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
                if user.is_superuser: return redirect('custom_admin')
                return redirect('home')
        else:
            messages.error(request, "⚠️ Invalid username or password.")
    return render(request, 'core/login.html')

def logout_view(request):
    auth_logout(request)
    messages.info(request, "👋 You have been logged out successfully.")
    return redirect('login_view')

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
            first_name = tg_user.get('first_name', '')
            last_name = tg_user.get('last_name', '')
            photo_url = tg_user.get('photo_url', '')
            
            if request.user.is_authenticated and request.user.telegram_id != tg_id:
                auth_logout(request)
            
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
            
            if not created:
                user.first_name = first_name
                user.last_name = last_name
                user.telegram_photo_url = photo_url
                if tg_username:
                    user.telegram_username = tg_username
                    user.username = tg_username
                user.save()
            
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
    
    completed_task_ids = list(UserTask.objects.filter(user=request.user).values_list('task_id', flat=True))
    tasks = Task.objects.filter(is_active=True).order_by('-created_at')
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    if request.user.last_daily_claim == today:
        claimable_day = -1
        checked_days = request.user.login_streak
    elif request.user.last_daily_claim == yesterday:
        claimable_day = request.user.login_streak + 1
        if claimable_day > 7: claimable_day = 1
        checked_days = request.user.login_streak if claimable_day > 1 else 0
    else:
        claimable_day = 1
        checked_days = 0
        
    return render(request, 'core/home.html', {
        'setting': setting, 
        'tasks': tasks, 
        'completed_task_ids': completed_task_ids,
        'claimable_day': claimable_day, 
        'checked_days': checked_days
    })
    
@login_required(login_url='/login/')
def services_view(request):
    if request.user.is_superuser: return redirect('custom_admin')
    services = Service.objects.filter(is_active=True).order_by('-id')
    return render(request, 'core/services.html', {'services': services})

@login_required(login_url='/login/')
def new_order_view(request):
    if request.user.is_superuser: return redirect('custom_admin')
    
    if request.method == 'POST':
        service_id = request.POST.get('service')
        link = request.POST.get('link')
        quantity = int(request.POST.get('quantity', 0))
        
        if service_id and link and quantity > 0:
            available_bots = Bot.objects.filter(is_active=True, is_banned=False).count()
            if available_bots < quantity:
                messages.error(request, f"⚠️ Low Bot Stock! Only {available_bots} bots available right now.")
                return redirect('new_order')
                
            service = get_object_or_404(Service, id=service_id)
            charge = (service.price_per_1000 / 1000) * quantity
            
            if request.user.wallet_balance >= charge:
                request.user.wallet_balance -= charge
                request.user.total_spent += charge
                request.user.save()
                
                if request.user.invited_by:
                    request.user.invited_by.diamonds += int(charge * 5)
                    request.user.invited_by.save()
                    
                order = Order.objects.create(user=request.user, service=service, link=link, quantity=quantity, charge=charge, status='Pending')
                
                Notification.objects.create(
                    user=request.user, 
                    title="Order Placed 🚀", 
                    message=f"Order for {service.name} has been placed. Bots are marching!", 
                    icon="fa-box", 
                    color="blue"
                )
                
                # 🔥 Trigger the Ultimate Bot Engine
                threading.Thread(target=run_bot_in_background, args=(order.id,), daemon=True).start()
                
                messages.success(request, f"🎉 Order placed! ₹{charge} deducted.")
                return redirect('orders')
            else:
                messages.error(request, "⚠️ Insufficient balance! Please add funds.")
                return redirect('add_funds')
        else:
            messages.error(request, "⚠️ Please fill all details correctly.")
            
    return render(request, 'core/new_order.html', {'services': Service.objects.filter(is_active=True)})
    
@login_required(login_url='/login/')
def orders_view(request):
    if request.user.is_superuser: return redirect('custom_admin')
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/orders.html', {'orders': orders})

@login_required(login_url='/login/')
def add_funds_view(request):
    if request.user.is_superuser: return redirect('custom_admin')
    setting, _ = SiteSetting.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        utr = request.POST.get('utr_number')
        if Payment.objects.filter(utr_number=utr).exists():
            messages.error(request, "❌ UTR already used.")
        else:
            Payment.objects.create(user=request.user, amount=request.POST.get('amount'), utr_number=utr)
            messages.success(request, "✅ Request submitted! Admin will verify shortly.")
        return redirect('add_funds')
        
    return render(request, 'core/add_funds.html', {'setting': setting})
# ==========================================
# 📱 3. CUSTOMER DASHBOARD VIEWS
# ==========================================
@login_required(login_url='/login/')
def home_view(request):
    if request.user.is_superuser: return redirect('custom_admin')
    setting, _ = SiteSetting.objects.get_or_create(id=1)
    
    completed_task_ids = list(UserTask.objects.filter(user=request.user).values_list('task_id', flat=True))
    tasks = Task.objects.filter(is_active=True).order_by('-created_at')
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    if request.user.last_daily_claim == today:
        claimable_day = -1
        checked_days = request.user.login_streak
    elif request.user.last_daily_claim == yesterday:
        claimable_day = request.user.login_streak + 1
        if claimable_day > 7: claimable_day = 1
        checked_days = request.user.login_streak if claimable_day > 1 else 0
    else:
        claimable_day = 1
        checked_days = 0
        
    return render(request, 'core/home.html', {
        'setting': setting, 
        'tasks': tasks, 
        'completed_task_ids': completed_task_ids,
        'claimable_day': claimable_day, 
        'checked_days': checked_days
    })
    
@login_required(login_url='/login/')
def services_view(request):
    if request.user.is_superuser: return redirect('custom_admin')
    services = Service.objects.filter(is_active=True).order_by('-id')
    return render(request, 'core/services.html', {'services': services})

@login_required(login_url='/login/')
def new_order_view(request):
    if request.user.is_superuser: return redirect('custom_admin')
    
    if request.method == 'POST':
        service_id = request.POST.get('service')
        link = request.POST.get('link')
        quantity = int(request.POST.get('quantity', 0))
        
        if service_id and link and quantity > 0:
            available_bots = Bot.objects.filter(is_active=True, is_banned=False).count()
            if available_bots < quantity:
                messages.error(request, f"⚠️ Low Bot Stock! Only {available_bots} bots available right now.")
                return redirect('new_order')
                
            service = get_object_or_404(Service, id=service_id)
            charge = (service.price_per_1000 / 1000) * quantity
            
                        if request.user.wallet_balance >= charge:
                request.user.wallet_balance -= charge
                request.user.total_spent += charge
                request.user.save()
                
                # 🔥 NAYA REWARD LOGIC (With History)
                if request.user.invited_by:
                    reward_diamonds = int(charge * 5)
                    if reward_diamonds > 0:
                        request.user.invited_by.diamonds += reward_diamonds
                        request.user.invited_by.save()
                        
                        # 📝 History mein save karo
                        from .models import RewardHistory # Circular import se bachne ke liye yahan import kar sakte ho
                        RewardHistory.objects.create(
                            user=request.user.invited_by,
                            referred_user=request.user,
                            diamonds_earned=reward_diamonds
                        )
                        
                order = Order.objects.create(user=request.user, service=service, link=link, quantity=quantity, charge=charge, status='Pending')
                
                Notification.objects.create(
                    user=request.user, 
                    title="Order Placed 🚀", 
                    message=f"Order for {service.name} has been placed. Bots are marching!", 
                    icon="fa-box", 
                    color="blue"
                )

                
                # 🔥 Trigger the Ultimate Bot Engine
                threading.Thread(target=run_bot_in_background, args=(order.id,), daemon=True).start()
                
                messages.success(request, f"🎉 Order placed! ₹{charge} deducted.")
                return redirect('orders')
            else:
                messages.error(request, "⚠️ Insufficient balance! Please add funds.")
                return redirect('add_funds')
        else:
            messages.error(request, "⚠️ Please fill all details correctly.")
            
    return render(request, 'core/new_order.html', {'services': Service.objects.filter(is_active=True)})
    
@login_required(login_url='/login/')
def orders_view(request):
    if request.user.is_superuser: return redirect('custom_admin')
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/orders.html', {'orders': orders})

@login_required(login_url='/login/')
def add_funds_view(request):
    if request.user.is_superuser: return redirect('custom_admin')
    setting, _ = SiteSetting.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        utr = request.POST.get('utr_number')
        if Payment.objects.filter(utr_number=utr).exists():
            messages.error(request, "❌ UTR already used.")
        else:
            Payment.objects.create(user=request.user, amount=request.POST.get('amount'), utr_number=utr)
            messages.success(request, "✅ Request submitted! Admin will verify shortly.")
        return redirect('add_funds')
        
    return render(request, 'core/add_funds.html', {'setting': setting})

@login_required(login_url='/login/')
def payment_history_view(request):
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
            rate = setting.diamonds_needed_for_1_rs
            if rate <= 0: rate = 50 
                
            withdraw_diamonds = int(request.POST.get('diamonds'))
            
            if withdraw_diamonds < rate:
                messages.error(request, f"⚠️ Minimum {rate} diamonds required!")
            elif request.user.diamonds >= withdraw_diamonds:
                rs_add = Decimal(str(withdraw_diamonds / rate))
                request.user.diamonds -= withdraw_diamonds
                request.user.save()
                
                Withdrawal.objects.create(user=request.user, diamonds_used=withdraw_diamonds, amount_rs=rs_add, upi_id=upi_id)
                Notification.objects.create(user=request.user, title="Withdrawal Requested ⏳", message=f"Your request for ₹{rs_add} is pending admin approval.", icon="fa-clock-rotate-left", color="amber")
                messages.success(request, f"🎉 Withdrawal request of ₹{rs_add} submitted!")
                return redirect('withdraw_history') 
            else:
                messages.error(request, "⚠️ Insufficient Diamonds!")
                
        except Exception as e:
            messages.error(request, f"⚠️ System Error: {str(e)}")
            
        return redirect('team_rewards')

    return render(request, 'core/team.html', {'setting': setting, 'invited_friends': invited_friends, 'total_invites': total_invites, 'tier_name': tier_name, 'tier_icon': tier_icon, 'tier_color': tier_color})

@login_required(login_url='/login/')
def api_docs_view(request):
    setting, _ = SiteSetting.objects.get_or_create(id=1)
    return render(request, 'core/api_docs.html', {'setting': setting})
    
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
            try:
                amt = Decimal(request.POST.get('amount', '0')) 
                target_user.wallet_balance += amt
                target_user.save()
                messages.success(request, f"Added ₹{amt} to @{target_user.username}")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
                
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
def admin_bot_action(request):
    if not request.user.is_superuser: return redirect('home')
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            bot_count = Bot.objects.count() + 1
            auto_name = f"Worker-Node-{bot_count:02d}"
            cookies_data = request.POST.get('cookies', '')
            
            # 🔥 NAYA: Form se Platform nikalna (YouTube ya Instagram)
            platform_choice = request.POST.get('platform', 'YouTube')
            
            # 🔥 NAYA: is_active=True ke sath platform bhi save kar rahe hain
            Bot.objects.create(
                name=auto_name, 
                platform=platform_choice,
                cookies=cookies_data,
                is_active=True 
            )
            messages.success(request, f"🚀 {platform_choice} Bot [{auto_name}] Deployed & Auto-Activated!")
            
        else:
            bot = get_object_or_404(Bot, id=request.POST.get('bot_id'))
            if action == 'toggle':
                bot.is_active = not bot.is_active
                bot.save()
                messages.success(request, f"[{bot.platform}] {bot.name} power state changed!")
            elif action == 'delete':
                bot.delete()
                messages.success(request, "Bot Engine Terminated.")
                
    return redirect('admin_bots')
            

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
    logs = Notification.objects.all().order_by('-created_at')[:100]
    return render(request, 'core/admin_logs.html', {'logs': logs})
    
@login_required(login_url='/login/')
def admin_settings_view(request):
    if not request.user.is_superuser: return redirect('home')
    setting, _ = SiteSetting.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        setting.platform_name = request.POST.get('platform_name', setting.platform_name)
        setting.upi_id = request.POST.get('upi_id', setting.upi_id)
        setting.diamonds_needed_for_1_rs = int(request.POST.get('diamonds_needed', setting.diamonds_needed_for_1_rs))
        setting.save()
        
        if 'profile_image' in request.FILES:
            request.user.profile_image = request.FILES['profile_image']
            request.user.save()
            
        messages.success(request, "Settings & Profile updated successfully!")
        return redirect('admin_settings')
        
    return render(request, 'core/admin_settings.html', {'setting': setting})

# ==========================================
# ⚡ SUPER ADMIN ACTION CONTROLLERS
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
def admin_payment_action(request):
    if not request.user.is_superuser: return redirect('home')
    if request.method == 'POST':
        payment = get_object_or_404(Payment, id=request.POST.get('payment_id'))
        if request.POST.get('action') == 'approve' and payment.status == 'Pending':
            payment.status = 'Completed'
            payment.user.wallet_balance += payment.amount
            payment.user.save()
            payment.save()
            
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
            
            Notification.objects.create(
                user=payment.user, 
                title="Payment Rejected ❌", 
                message="Your recent payment request was rejected by the admin. Check UTR.", 
                icon="fa-circle-xmark", 
                color="rose"
            )
            messages.error(request, "Payment Rejected.")
            
    return redirect('admin_payments')
    

#aha par admin bot action tha usko mene upar admin dashboard par hi khik diya#
@login_required(login_url='/login/')
def admin_tasks(request):
    if not request.user.is_superuser: return redirect('home')
    tasks = Task.objects.all().order_by('-created_at')
    return render(request, 'core/admin_tasks.html', {'tasks': tasks})
    

@login_required(login_url='/login/')
def claim_daily_view(request):
    if request.method == 'POST':
        user = request.user
        today = timezone.now().date()
        
        if user.last_daily_claim == today:
            return JsonResponse({'status': 'error', 'message': 'Already claimed today!'})
            
        if user.last_daily_claim == today - timedelta(days=1):
            user.login_streak += 1
        else:
            user.login_streak = 1 
            
        if user.login_streak > 7:
            user.login_streak = 1
            
        reward = 50 if user.login_streak == 7 else 10
        user.diamonds += reward
        user.last_daily_claim = today
        user.save()
        
        return JsonResponse({'status': 'success', 'message': f'Claimed {reward} 💎!', 'diamonds': user.diamonds})

@login_required(login_url='/login/')
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
            withdraw.user.diamonds += withdraw.diamonds_used 
            withdraw.user.save()
            withdraw.save()
            Notification.objects.create(user=withdraw.user, title="Withdrawal Rejected ❌", message="Your withdrawal request was rejected. Diamonds refunded.", icon="fa-circle-xmark", color="rose")
            messages.error(request, "Withdrawal Rejected & Diamonds Refunded.")
    return redirect('admin_withdrawals')

# ==========================================
# 🕵️‍♂️ GOD MODE & SPY CAMERA (ADMIN ONLY)
# ==========================================
@login_required(login_url='/login/')
def login_as_user(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, "🚫 Hacker Alert: Tum Admin Nahi Ho!")
        return redirect('home')
        
    try:
        target_user = CustomUser.objects.get(id=user_id)
        auth_login(request, target_user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, f"🕵️‍♂️ God Mode: You are now logged in as '{target_user.username}'")
        return redirect('home')
        
    except CustomUser.DoesNotExist:
        return HttpResponse("<h1>❌ User nahi mila!</h1>")

@login_required(login_url='/login/')
def spy_camera(request):
    if not request.user.is_superuser:
        return HttpResponse("<h1>🚫 Hacker Alert: Tum Admin Nahi Ho!</h1>")
    
    files = [f for f in os.listdir('.') if f.endswith('.png')]
    if not files:
        return HttpResponse("<h1>📸 Koi naya screenshot nahi mila.</h1>")
    
    # Sort files by creation time to get the newest one
    files.sort(key=os.path.getmtime)
    latest_file = files[-1]
    
    with open(latest_file, 'rb') as f:
        return HttpResponse(f.read(), content_type="image/png")


# ==========================================
# 🌐 STANDARD SMM API V2 PROVIDER ENGINE
# ==========================================
@csrf_exempt
def api_v2_provider(request):
    """
    Standard SMM API v2. Support for PerfectPanel, SmartPanel etc.
    """
    # API dono GET aur POST requests ko support karti hai
    req_data = request.POST if request.method == 'POST' else request.GET
    
    api_key = req_data.get('key')
    action = req_data.get('action')
    
    if not api_key or not action:
        return JsonResponse({'error': 'Incorrect request'})
        
    # 1. API Key Validation
    try:
        user = CustomUser.objects.get(api_key=api_key)
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'Invalid API key'})

    # 2. BALANCE CHECK
    if action == 'balance':
        return JsonResponse({
            'balance': str(user.wallet_balance),
            'currency': 'INR'
        })

    # 3. SERVICES LIST
    elif action == 'services':
        services = Service.objects.filter(is_active=True)
        service_list = []
        for s in services:
            service_list.append({
                'service': str(s.id),
                'name': s.name,
                'type': 'Default',
                'category': s.platform,
                'rate': str(s.price_per_1000),
                'min': str(s.min_order),
                'max': str(s.max_order)
            })
        return JsonResponse(service_list, safe=False)

    # 4. PLACE NEW ORDER (The Money Maker 💸)
    elif action == 'add':
        service_id = req_data.get('service')
        link = req_data.get('link')
        quantity = req_data.get('quantity')
        
        if not service_id or not link or not quantity:
            return JsonResponse({'error': 'Missing parameters'})
            
        try:
            quantity = int(quantity)
            service = Service.objects.get(id=service_id, is_active=True)
        except Exception:
            return JsonResponse({'error': 'Invalid service or quantity'})
            
        if quantity < service.min_order or quantity > service.max_order:
            return JsonResponse({'error': f'Quantity must be between {service.min_order} and {service.max_order}'})
            
        charge = (service.price_per_1000 / 1000) * quantity
        
        if user.wallet_balance < charge:
            return JsonResponse({'error': 'Not enough funds on balance'})
            
        # Deduct Balance
        user.wallet_balance -= charge
        user.total_spent += charge
        user.save()
        
        # Create Order
        order = Order.objects.create(
            user=user, service=service, link=link, 
            quantity=quantity, charge=charge, status='Pending'
        )
        
        # 🔥 Trigger Bot in Background! 
        # (Aapke bot function ka jo bhi naam hai, wahi use karein. Eg: run_bot_in_background ya run_bot_task)
        threading.Thread(target=run_bot_in_background, args=(order.id,), daemon=True).start()
        
        return JsonResponse({'order': str(order.id)})

    # 5. ORDER STATUS CHECK
    elif action == 'status':
        order_id = req_data.get('order')
        try:
            order = Order.objects.get(id=order_id, user=user)
            # Map statuses to standard SMM format
            status_map = {
                'Pending': 'Pending',
                'Processing': 'Processing',
                'Completed': 'Completed',
                'Partial': 'Partial',
                'Failed': 'Canceled'
            }
            return JsonResponse({
                'charge': str(order.charge),
                'start_count': '0',
                'status': status_map.get(order.status, 'Pending'),
                'remains': str(order.quantity),
                'currency': 'INR'
            })
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Incorrect order ID'})

    else:
        return JsonResponse({'error': 'Incorrect action'})
        
