from shop.models import Product
import random
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .forms import ContractAgreementForm
from datetime import datetime
from .email_utils import send_contract_notification
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from .models import ContractAgreement, PaymentMethod


def home_view(request):
    # Get all products and shuffle them randomly
    all_products = list(Product.objects.all())
    random.shuffle(all_products)  # Randomize order
    products = all_products[:12]  # Limit to 12 products
    
    # Get products by category for the different sections
    satin_products = Product.objects.filter(category='satin')[:3]
    silk_products = Product.objects.filter(category='silk')[:3]
    luxe_products = Product.objects.filter(category='luxe')[:3]
    
    # Get random bestsellers (if any products marked as bestseller)
    bestsellers = Product.objects.filter(is_bestseller=True)[:3]
    if len(bestsellers) < 3:
        # If not enough bestsellers, add random products
        additional = Product.objects.exclude(id__in=[p.id for p in bestsellers])[:3-len(bestsellers)]
        bestsellers = list(bestsellers) + list(additional)
    
    context = {
        'products': products,
        'satin_products': satin_products,
        'silk_products': silk_products,
        'luxe_products': luxe_products,
        'bestsellers': bestsellers,
    }
    return render(request, 'home.html', context)

def agreement_view(request):
    return render(request, "pages/agreement.html")

def agreements_view(request):
    return render(request, "pages/agreements.html")

def contract_agreement_view(request):
    if request.method == 'POST':
        form = ContractAgreementForm(request.POST)
        if form.is_valid():
            contract = form.save(commit=False)
            
            # Get client IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                contract.ip_address = x_forwarded_for.split(',')[0]
            else:
                contract.ip_address = request.META.get('REMOTE_ADDR')
            
            contract.save()
            form.save_m2m()  # Save payment_methods ManyToMany
            
            # Send email notification
            send_contract_notification(contract)
            
            messages.success(request, 'Your contract agreement has been submitted successfully!')
            return redirect('contract_success')
    else:
        form = ContractAgreementForm()
    
    return render(request, 'pages/contract_agreement.html', {'form': form})

def contract_success_view(request):
    return render(request, 'pages/contract_success.html')


def contract_list_view(request):
    """View all submitted contracts - requires password"""
    # Check if password is already in session
    if request.session.get('contract_view_authorized'):
        contracts = ContractAgreement.objects.all().order_by('-created_at')
        return render(request, 'pages/contract_list.html', {'contracts': contracts})
    
    # Check if password was submitted
    if request.method == 'POST':
        entered_password = request.POST.get('password')
        if entered_password == settings.CONTRACT_VIEW_PASSWORD:
            request.session['contract_view_authorized'] = True
            request.session.set_expiry(3600)  # Expire after 1 hour
            contracts = ContractAgreement.objects.all().order_by('-created_at')
            return render(request, 'pages/contract_list.html', {'contracts': contracts})
        else:
            messages.error(request, 'Invalid password. Please try again.')
    
    return render(request, 'pages/contract_password.html')

def contract_detail_view(request, contract_id):
    """View individual contract details"""
    # Check if authorized
    if not request.session.get('contract_view_authorized'):
        return redirect('contract_list')
    
    contract = get_object_or_404(ContractAgreement, id=contract_id)
    return render(request, 'pages/contract_detail.html', {'contract': contract})

def contract_logout_view(request):
    """Logout from contract view"""
    request.session.pop('contract_view_authorized', None)
    messages.success(request, 'You have been logged out.')
    return redirect('contract_list')    