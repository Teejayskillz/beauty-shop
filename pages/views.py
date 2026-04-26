from shop.models import Product
import random
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContractAgreementForm
from .models import ContractAgreement


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
            messages.success(request, 'Your contract agreement has been submitted successfully!')
            return redirect('contract_success')
    else:
        form = ContractAgreementForm()
    
    return render(request, 'pages/contract_agreement.html', {'form': form})

def contract_success_view(request):
    return render(request, 'pages/contract_success.html')