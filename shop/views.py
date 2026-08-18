# shop/views.py

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import random
from decimal import Decimal
from .models import Product, Order, OrderItem
from .payment_service import PaymentService

def shop_view(request):
    products = Product.objects.all()
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
            "status": order.status,
            "payment_status": order.payment_status,  # Added
            "tracking_code": order.tracking_code
        })
    except Order.DoesNotExist:
        return JsonResponse({"error": "Not found"})

def track_order(request):
    return render(request, "shop/track.html")

def checkout_view(request):
    """Display checkout page"""
    return render(request, 'shop/checkout.html')

@csrf_exempt
@require_http_methods(["POST"])
def create_order(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("Received data:", data)
            
            cart = data.get("cart", [])
            payment_method = data.get("payment_method", "pod")  # NEW
            
            if not cart:
                return JsonResponse({"success": False, "error": "Cart is empty"}, status=400)
            
            total = Decimal('0')  # Changed to Decimal
            
            # Create the order
            order = Order.objects.create(
                full_name=data.get("name", ""),
                email=data.get("email", ""),
                phone=data.get("phone", ""),
                address=data.get("address", ""),
                total_amount=0,
                status="pending",
                payment_status="pending",  # NEW
                payment_method=payment_method,  # NEW
                tracking_code=generate_tracking_code()
            )
            
            # Create order items
            for item in cart:
                try:
                    product = Product.objects.get(id=item["id"])
                    item_total = Decimal(str(product.price)) * int(item["qty"])
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
            
            # If Pay on Delivery, mark as paid immediately
            if payment_method == "pod":
                order.payment_status = 'completed'
                order.status = 'processing'
                order.save()
            
            return JsonResponse({
                "success": True,
                "message": "Order placed successfully!",
                "tracking_code": order.tracking_code,
                "order_id": order.id,
                "payment_method": payment_method,
                "requires_payment": payment_method != "pod"
            })
            
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data"}, status=400)
        except Exception as e:
            print("Error creating order:", str(e))
            return JsonResponse({"success": False, "error": str(e)}, status=400)

# NEW: Process payment endpoint
@csrf_exempt
@require_http_methods(["POST"])
def process_payment(request):
    """Process payment for an order"""
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        card_details = data.get('card_details', {})
        idempotency_key = data.get('idempotency_key')
        
        if not order_id:
            return JsonResponse({
                'success': False,
                'error': 'Order ID is required'
            }, status=400)
        
        # Process payment
        result = PaymentService.process_order_payment(
            order_id=order_id,
            card_details=card_details,
            idempotency_key=idempotency_key
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': result.get('message', 'Payment successful!'),
                'transaction_id': result.get('transaction_id'),
                'order_id': order_id
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Payment failed'),
                'errors': result.get('errors', []),
                'transaction_id': result.get('transaction_id')
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print("Payment processing error:", str(e))
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# NEW: Payment success view
def payment_success_view(request, order_id):
    """Show payment success page"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'shop/payment_success.html', {'order': order})

# NEW: Payment failed view
def payment_failed_view(request, order_id):
    """Show payment failed page"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'shop/payment_failed.html', {'order': order})

# NEW: Order detail view
def order_detail_view(request, order_id):
    """View order details"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'shop/order_detail.html', {'order': order})

# Keep existing order_tracking_view
def order_tracking_view(request, tracking_code):
    print("TRACKING CODE:", tracking_code)
    return render(request, 'order_tracking.html', {
        'tracking_code': tracking_code
    })