# shop/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Existing routes (unchanged)
    path('', views.shop_view, name='shop'),
    path('product/<int:product_id>/', views.product_detail_view, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('track/', views.track_order, name='track_order'),
    path('track/api/', views.track_api, name='track_api'),
    
    # Order routes (updated)
    path('create-order/', views.create_order, name='create_order'),
    path('order/<int:order_id>/', views.order_detail_view, name='order_detail'),  # NEW
    path('order/tracking/<str:tracking_code>/', views.order_tracking_view, name='order_tracking'),
    
    # NEW: Payment routes
    path('payment/process/', views.process_payment, name='process_payment'),
    path('payment/success/<int:order_id>/', views.payment_success_view, name='payment_success'),
    path('payment/failed/<int:order_id>/', views.payment_failed_view, name='payment_failed'),
]