# shop/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.shop_view, name='shop'),
    path('product/<int:product_id>/', views.product_detail_view, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('create-order/', views.create_order, name='create_order'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('track/', views.track_order, name='track_order'),
    path('track/api/', views.track_api, name='track_api'),
    path('order/tracking/<str:tracking_code>/', views.order_tracking_view, name='order_tracking'),
]