import threading
import time
import json
import os  
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync  # 🥷 STEALTH MODE IMPORT
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Payment, Service, Order, CustomUser, Bot

# ==========================================
# 🔐 USER AUTHENTICATION SYSTEM (WITH BOUNCER)
# ==========================================
def register_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('/admin/')
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
        if request.user.is_superuser:
            return redirect('/admin/')
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
                if user.is_superuser:
                    return redirect('/admin/')
                else:
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
# 🌟 BASIC PAGES (WITH ADMIN BOUNCER)
# ==========================================
def home(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('/admin/')
        
    total_platform_users = CustomUser.objects.count() + 2500
    total_platform_orders = Order.objects.count() + 15400
    context = {
        'total_platform_users': total_platform_users,
        'total_platform_orders': total_platform_orders,
    }
    if request.user.is_authenticated:
        context['user_orders_count'] = Order.objects.filter(user=request.user).count()
        context['user_pending_orders'] = Order.objects.filter(user=request.user, status='Pending').count()
    return render(request, 'core/home.html', context)

def services(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('/admin/')
        
    services_list = Service.objects.all()
    return render(request, 'core/services.html', {'services': services_list})

# ==========================================
# 🤖 PLAYWRIGHT ENGINE (STEALTH + BULLETPROOF HUNTER 🎯)
# ==========================================
def run_bot_task(order_id):
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    
    order = Order.objects.get(id=order_id)
    bots = Bot.objects.filter(is_active=True, is_banned=False)[:order.quantity]
    
    order.status = 'Processing'
    order.save()
    success_count = order.delivered_quantity
    target_link = order.link 
    
    try:
        with sync_playwright() as p:
            # 🥷 STEALTH MODE
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            
            for bot in bots:
                try:
                    raw_cookies = json.loads(bot.cookies_json)
                    clean_cookies = []
                    
                    # 🧹 SMART COOKIE CLEANER
                    for c in raw_cookies:
                        if c.get("sameSite") == "no_restriction":
                            c["sameSite"] = "None"
                        elif c.get("sameSite") not in ["Strict", "Lax", "None"]:
                            c.pop("sameSite", None)
                            
                        # Domain Fixer for YouTube
                        if "youtube" in c.get("domain", "") or "googleusercontent" in c.get("domain", ""):
                            c["domain"] = ".youtube.com"
                            
                        clean_cookies.append(c)

                    context = browser.new_context(
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        locale='en-US'
                    )
                    
                    context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    context.add_cookies(clean_cookies)
                    
                    page = context.new_page()
                    stealth_sync(page) # 🥷 Magic Wand
                    
                    print(f"\n🚀 Bot [{bot.name}] is navigating to: {target_link}")
                    page.goto(target_link, timeout=60000)
                    page.wait_for_load_state("networkidle")
                    time.sleep(5) 
                    
                    print(f"👀 Page Title: {page.title()}")
                    
                    try:
                        # 🎯 THE BULLETPROOF VISIBLE BUTTON HUNTER
                        buttons = page.locator(
                            "ytd-subscribe-button-renderer button, "
                            "#subscribe-button-shape button, "
                            "#subscribe-button button, "
                            "button[aria-label*='Subscribe'], "
                            "button[aria-label*='subscribe'], "
                            "button[aria-label*='सदस्यता लें']"
                        )
                        
                        btn_found_and_clicked = False
                        
                        for i in range(buttons.count()):
                            btn = buttons.nth(i)
                            if btn.is_visible():  
                                btn_text = btn.inner_text().lower()
                                print(f"🔍 Visible Button {i+1} par likha hai: '{btn_text}'")
                                
                                if "subscribed" in btn_text or "सदस्यता ली" in btn_text or "सदस्य हैं" in btn_text:
                                    print(f"✅ Bot [{bot.name}]: Pehle se hi Subscribed hai!")
                                    success_count += 1
                                    btn_found_and_clicked = True
                                    break  
                                else:
                                    btn.click()
                                    print(f"✅ Bot [{bot.name}]: Successfully Clicked Subscribe! 🎉")
                                    time.sleep(2)
                                    success_count += 1
                                    btn_found_and_clicked = True
                                    break  
                        
                        if btn_found_and_clicked:
                            order.delivered_quantity = success_count
                            order.save() 
                        else:
                            ss_name = f"error_no_btn_{bot.name.replace(' ', '_')}.png"
                            page.screenshot(path=ss_name)
                            print(f"📸 DANGER: Button nahi mila! Screenshot saved as: {ss_name}")
                            
                    except Exception as btn_error:
                        ss_name = f"error_crash_{bot.name.replace(' ', '_')}.png"
                        page.screenshot(path=ss_name)
                        print(f"📸 CRASH: Screenshot saved! Error: {btn_error}")
                        
                    context.close()
                    
                except Exception as e:
                    print(f"❌ Bot [{bot.name}] Failed: {e}")
                    
                time.sleep(4) 
                
            browser.close()
            
    except Exception as e:
        print(f"🚨 Playwright Engine Error: {e}")
        
    order.status = 'Completed' if success_count >= order.quantity else 'Processing'
    order.save()
    print(f"🏁 Order Status Update: {order.status} (Delivered: {success_count}/{order.quantity})")

# ==========================================
# 🚀 SMM CORE FEATURES (WITH ADMIN BOUNCER)
# ==========================================
@login_required(login_url='/login/')
def add_funds(request):
    if request.user.is_superuser:
        return redirect('/admin/')
        
    if request.method == 'POST':
        amount = request.POST.get('amount')
        utr_number = request.POST.get('utr_number')
        if amount and utr_number:
            Payment.objects.create(user=request.user, amount=amount, utr_number=utr_number, status='Pending')
            messages.success(request, f"₹{amount} payment request sent successfully!")
        else:
            messages.error(request, "Please enter both Amount and UTR Number.")
    return render(request, 'core/add_funds.html')

@login_required(login_url='/login/')
def new_order(request):
    if request.user.is_superuser:
        return redirect('/admin/')
        
    services_list = Service.objects.all()
    if request.method == 'POST':
        service_id = request.POST.get('service')
        link = request.POST.get('link')
        quantity = int(request.POST.get('quantity', 0))
        
        if service_id and link and quantity > 0:
            available_bots = Bot.objects.filter(is_active=True, is_banned=False).count()
            if available_bots < quantity:
                messages.error(request, f"⚠️ Low Bot Stock! Only {available_bots} bots available.")
                return redirect('new_order')

            service = Service.objects.get(id=service_id)
            charge = (service.price_per_1000 / 1000) * quantity
            
            if request.user.wallet_balance >= charge:
                request.user.wallet_balance -= charge
                request.user.total_spent += charge
                request.user.save()
                
                order = Order.objects.create(
                    user=request.user, service=service, link=link, 
                    quantity=quantity, charge=charge, status='Pending'
                )
                
                threading.Thread(target=run_bot_task, args=(order.id,)).start()
                messages.success(request, f"🎉 Order placed! Bots are checking the target...")
                return redirect('orders')
            else:
                messages.error(request, "⚠️ Insufficient balance! Please add funds.")
        else:
            messages.error(request, "⚠️ Please fill details correctly.")
    return render(request, 'core/new_order.html', {'services': services_list})

@login_required(login_url='/login/')
def orders(request):
    if request.user.is_superuser:
        return redirect('/admin/')
        
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/orders.html', {'orders': user_orders})

# ==========================================
# 🕵️‍♂️ GOD MODE & SPY CAMERA
# ==========================================
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

def spy_camera(request):
    if not request.user.is_superuser:
        return HttpResponse("<h1>🚫 Hacker Alert: Tum Admin Nahi Ho!</h1>")
    
    files = [f for f in os.listdir('.') if f.endswith('.png')]
    if not files:
        return HttpResponse("<h1>📸 Koi naya screenshot nahi mila.</h1>")
    
    latest_file = files[-1]
    with open(latest_file, 'rb') as f:
        return HttpResponse(f.read(), content_type="image/png")
        
