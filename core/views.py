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
    
  from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Payment

@login_required(login_url='/admin/login/') # Agar login nahi hai, toh login par bheje
def add_funds(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        utr_number = request.POST.get('utr_number')
        
        # Check karein ki details khali na hon
        if amount and utr_number:
            # Payment database mein save karein
            Payment.objects.create(
                user=request.user,
                amount=amount,
                utr_number=utr_number,
                status='Pending'
            )
            messages.success(request, f"₹{amount} payment request sent successfully! Please wait for admin approval.")
        else:
            messages.error(request, "Please enter both Amount and UTR Number.")
            
    return render(request, 'core/add_funds.html')
from .models import Service, Order

@login_required(login_url='/admin/login/')
def new_order(request):
    services = Service.objects.all() # Database se saari services nikalna
    
    if request.method == 'POST':
        service_id = request.POST.get('service')
        link = request.POST.get('link')
        quantity = int(request.POST.get('quantity', 0))
        
        if service_id and link and quantity > 0:
            try:
                service = Service.objects.get(id=service_id)
                charge = (service.price_per_1000 / 1000) * quantity
                
                # Check karein ki user ke paas paise hain ya nahi
                if request.user.wallet_balance >= charge:
                    # Paise kaato aur order lagao
                    request.user.wallet_balance -= charge
                    request.user.total_spent += charge
                    request.user.save()
                    
                    Order.objects.create(
                        user=request.user,
                        service=service,
                        link=link,
                        quantity=quantity,
                        charge=charge,
                        status='Pending'
                    )
                    messages.success(request, f"🎉 Order placed successfully! Charge: ₹{charge}")
                else:
                    messages.error(request, "⚠️ Insufficient balance! Please add funds.")
            except:
                messages.error(request, "⚠️ Something went wrong.")
        else:
            messages.error(request, "⚠️ Please fill all details correctly.")
            
    return render(request, 'core/new_order.html', {'services': services})
        
