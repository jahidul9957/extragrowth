import threading
import time
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Payment, Service, Order, CustomUser, Bot

# 🤖 BACKGROUND BOT WORKER
def run_bot_task(order_id):
    order = Order.objects.get(id=order_id)
    # Jitni quantity chahiye, utne active bots nikal lo
    bots = Bot.objects.filter(is_active=True, is_banned=False)[:order.quantity]
    
    order.status = 'Processing'
    order.save()
    
    success_count = 0
    for bot in bots:
        try:
            # 🚀 YAHAN APNA ASLI REQUESTS CODE LAGA SAKTE HAIN:
            # cookies = json.loads(bot.cookies_json)
            # requests.post("youtube_subscribe_url", cookies=cookies)
            
            time.sleep(2) # Fake processing time (2 seconds per bot)
            success_count += 1
            
            # Database mein progress update karein
            order.delivered_quantity = success_count
            order.save()
        except Exception as e:
            bot.is_active = False # Agar bot fail hua toh use inactive kar do
            bot.save()
            
    order.status = 'Completed' if success_count == order.quantity else 'Processing'
    order.save()


@login_required(login_url='/login/')
def new_order(request):
    services_list = Service.objects.all()
    if request.method == 'POST':
        service_id = request.POST.get('service')
        link = request.POST.get('link')
        quantity = int(request.POST.get('quantity', 0))
        
        if service_id and link and quantity > 0:
            # 1. Check Bot Stock
            available_bots = Bot.objects.filter(is_active=True, is_banned=False).count()
            if available_bots < quantity:
                messages.error(request, f"⚠️ Low Bot Stock! Only {available_bots} bots available right now.")
                return redirect('new_order')

            service = Service.objects.get(id=service_id)
            charge = (service.price_per_1000 / 1000) * quantity
            
            # 2. Check Balance
            if request.user.wallet_balance >= charge:
                request.user.wallet_balance -= charge
                request.user.total_spent += charge
                request.user.save()
                
                # 3. Create Order
                order = Order.objects.create(
                    user=request.user, service=service, link=link, 
                    quantity=quantity, charge=charge, status='Pending'
                )
                
                # 4. START AUTO-BOT IN BACKGROUND 🚀
                threading.Thread(target=run_bot_task, args=(order.id,)).start()
                
                messages.success(request, f"🎉 Order placed successfully! Bots are starting their work.")
                return redirect('orders')
            else:
                messages.error(request, "⚠️ Insufficient balance! Please add funds.")
        else:
            messages.error(request, "⚠️ Please fill details correctly.")
            
    return render(request, 'core/new_order.html', {'services': services_list})
    
