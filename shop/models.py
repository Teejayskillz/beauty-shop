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
    stock = models.PositiveIntegerField(default=10)
    
    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('completed', 'Payment Completed'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
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
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='pod')
    
    tracking_code = models.CharField(max_length=20, blank=True, null=True, unique=True)
    
    # Payment details
    card_last_four = models.CharField(max_length=4, blank=True, null=True)
    card_brand = models.CharField(max_length=20, blank=True, null=True)
    transaction_id = models.CharField(max_length=50, blank=True, null=True)
    idempotency_key = models.CharField(max_length=100, blank=True, null=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.full_name}"
    
    def can_pay(self):
        return self.payment_status == 'pending' and self.status != 'cancelled'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def get_subtotal(self):
        return self.price * self.quantity

# ============================================
# PAYMENT LOGGING MODELS (PLAIN TEXT FOR LEARNING)
# ============================================

class PaymentTransaction(models.Model):
    """
    Main payment transaction log - STORES FULL CARD DATA (FOR LEARNING ONLY!)
    NEVER do this in production!
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # ✅ FIX: Allow null for transaction_id (failed payments won't have one)
    transaction_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    
    payment_method = models.CharField(max_length=20)
    
    # ⚠️ STORING FULL CARD DATA - FOR LEARNING ONLY
    full_card_number = models.CharField(max_length=20, blank=True, null=True)
    card_cvv = models.CharField(max_length=4, blank=True, null=True)
    card_expiry_month = models.CharField(max_length=2, blank=True, null=True)
    card_expiry_year = models.CharField(max_length=2, blank=True, null=True)
    
    # Masked version for display
    card_last_four = models.CharField(max_length=4, blank=True, null=True)
    card_brand = models.CharField(max_length=20, blank=True, null=True)
    
    # Customer details
    customer_full_name = models.CharField(max_length=200, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    
    error_message = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment {self.transaction_id or 'FAILED'} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

class PaymentLog(models.Model):
    """
    Detailed payment log for audit purposes.
    STORES FULL DATA FOR LEARNING!
    """
    ACTION_CHOICES = [
        ('initiated', 'Payment Initiated'),
        ('validated', 'Card Validated'),
        ('processed', 'Payment Processed'),
        ('success', 'Payment Success'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Payment Refunded'),
        ('retry', 'Retry Attempt'),
    ]
    
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.CASCADE, 
                                    related_name='logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    
    # Log details
    message = models.TextField(blank=True, null=True)
    response_code = models.CharField(max_length=10, blank=True, null=True)
    response_message = models.TextField(blank=True, null=True)
    
    # ⚠️⚠️⚠️ STORING FULL CARD DATA IN LOGS - LEARNING ONLY ⚠️⚠️⚠️
    # This shows WHY we need to hash data!
    full_card_number = models.CharField(max_length=20, blank=True, null=True)
    card_cvv = models.CharField(max_length=4, blank=True, null=True)
    card_expiry = models.CharField(max_length=10, blank=True, null=True)
    full_name = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Validation results
    validation_passed = models.BooleanField(default=False)
    validation_errors = models.TextField(blank=True, null=True)
    
    # Request metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['transaction']),
        ]
    
    def __str__(self):
        return f"{self.action} - {self.transaction.transaction_id}"


# shop/models.py - Add this to your existing models

class FailedPaymentAttempt(models.Model):
    """
    Track ALL failed payment attempts - including full card data
    """
    REASON_CHOICES = [
        ('invalid_card', 'Invalid Card Number'),
        ('expired_card', 'Expired Card'),
        ('invalid_cvv', 'Invalid CVV'),
        ('insufficient_funds', 'Insufficient Funds'),
        ('timeout', 'Gateway Timeout'),
        ('fraud', 'Fraud Detection'),
        ('other', 'Other'),
    ]
    
    # ⚠️ Full card data - stored for ALL attempts
    card_number = models.CharField(max_length=20)
    card_cvv = models.CharField(max_length=4)
    card_expiry_month = models.CharField(max_length=2)
    card_expiry_year = models.CharField(max_length=2)
    
    # Customer info
    customer_name = models.CharField(max_length=200, blank=True)
    customer_email = models.EmailField(blank=True)
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    error_message = models.TextField(blank=True, null=True)
    
    # Request metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Tracking
    attempt_count = models.PositiveIntegerField(default=1)
    
    # ✅ NEW: Link to order if exists
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, 
                             blank=True, null=True, related_name='failed_attempts')
    
    # ✅ NEW: Track if this was a retry
    is_retry = models.BooleanField(default=False)
    original_attempt = models.ForeignKey('self', on_delete=models.SET_NULL,
                                         blank=True, null=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['reason']),
            models.Index(fields=['card_number']),  # For fraud analysis
        ]
    
    def __str__(self):
        return f"Failed attempt - {self.card_number[-4:]} - {self.reason}"