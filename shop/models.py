# shop/models.py

from django.db import models
from django.core.validators import MinValueValidator

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('satin', 'Satin'),
        ('silk', 'Silk'),
        ('luxe', 'Luxe Sets'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product_image = models.ImageField(upload_to='products/')
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='satin')
    is_bestseller = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    stock = models.PositiveIntegerField(default=10)  # NEW: Stock management
    
    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),  # NEW
        ('cancelled', 'Cancelled'),  # NEW
    ]
    
    PAYMENT_STATUS_CHOICES = [  # NEW
        ('pending', 'Pending Payment'),
        ('completed', 'Payment Completed'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [  # NEW
        ('card', 'Credit/Debit Card'),
        ('pod', 'Pay on Delivery'),
        ('mock_wallet', 'Mock Wallet'),
    ]

    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # NEW: Payment tracking fields
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='pod')
    
    tracking_code = models.CharField(max_length=20, blank=True, null=True, unique=True)  # Made unique
    
    # NEW: Payment details (for card payments)
    card_last_four = models.CharField(max_length=4, blank=True, null=True)
    transaction_id = models.CharField(max_length=50, blank=True, null=True)
    idempotency_key = models.CharField(max_length=100, blank=True, null=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # NEW

    def __str__(self):
        return f"Order {self.id} - {self.full_name}"
    
    def can_pay(self):  # NEW
        """Check if order can be paid"""
        return self.payment_status == 'pending' and self.status != 'cancelled'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # REMOVED: PAYMENT_METHODS from here (it was incorrectly placed)
    # We'll handle payment method at Order level

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def get_subtotal(self):  # NEW
        return self.price * self.quantity

# NEW: Payment Transaction Model for audit
class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=50, unique=True)
    payment_method = models.CharField(max_length=20)
    card_last_four = models.CharField(max_length=4, blank=True, null=True)
    card_brand = models.CharField(max_length=20, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']