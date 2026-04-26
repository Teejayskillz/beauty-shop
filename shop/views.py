# shop/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import random
from .models import Product, Order, OrderItem

def shop_view(request):
    products = Product.objects.all()
    #print(f"Number of products: {products.count()}")
    #for product in products:
    #    print(f"Product: {product.name}, Description: {product.description}")
    
    context = {
        'products': products,
    }
    return render(request, 'shop/shop.html', context)

def product_detail_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'product_detail.html', context)

def cart_view(request):
    return render(request, 'shop/cart.html')

def generate_tracking_code():
    while True:
        code = f"VB-{random.randint(10000, 99999)}"
        if not Order.objects.filter(tracking_code=code).exists():
            return code

def track_api(request):
    code = request.GET.get("code")
    try:
        order = Order.objects.get(tracking_code=code)
        return JsonResponse({
            "status": order.status
        })
    except Order.DoesNotExist:
        return JsonResponse({"error": "Not found"})

def track_order(request):
    return render(request, "shop/track.html")


def checkout_view(request):
    """Display checkout page"""
    return render(request, 'checkout.html')

@csrf_exempt
@require_http_methods(["POST"])
def create_order(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("Received data:", data)  # Debug print
            
            cart = data.get("cart", [])
            
            if not cart:
                return JsonResponse({"success": False, "error": "Cart is empty"}, status=400)
            
            total = 0
            
            # Create the order
            order = Order.objects.create(
                full_name=data.get("name", ""),
                email=data.get("email", ""),
                phone=data.get("phone", ""),
                address=data.get("address", ""),
                total_amount=0,
                status="pending",
                tracking_code=generate_tracking_code()
            )
            
            # Create order items
            for item in cart:
                try:
                    product = Product.objects.get(id=item["id"])
                    item_total = float(product.price) * int(item["qty"])
                    total += item_total
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item["qty"],
                        price=product.price
                    )
                except Product.DoesNotExist:
                    return JsonResponse({"success": False, "error": f"Product with id {item['id']} not found"}, status=400)
            
            order.total_amount = total
            order.save()
            
            return JsonResponse({
                "success": True,
                "message": "Order placed successfully!",
                "tracking_code": order.tracking_code,
                "order_id": order.id
            })
            
        except json.JSONDecodeError as e:
            return JsonResponse({"success": False, "error": "Invalid JSON data"}, status=400)
        except Exception as e:
            print("Error creating order:", str(e))  # Debug print
            return JsonResponse({"success": False, "error": str(e)}, status=400)

def order_tracking_view(request, tracking_code):
    print("TRACKING CODE:", tracking_code)  # 👈 add this
    return render(request, 'order_tracking.html', {
        'tracking_code': tracking_code
    })