# shop/admin.py

from django.contrib import admin
from .models import Product, Order, OrderItem

admin.site.register(OrderItem)

from django.contrib import admin
from .models import ( 
    PaymentTransaction, PaymentLog, FailedPaymentAttempt
)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'is_bestseller', 'stock']
    search_fields = ['name', 'description']
    list_filter = ['category', 'is_bestseller']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'email', 'total_amount', 'status', 'payment_status', 'created_at']
    search_fields = ['full_name', 'email', 'tracking_code', 'transaction_id']
    list_filter = ['status', 'payment_status', 'payment_method']
    readonly_fields = ['created_at', 'updated_at']
    
    # ✅ Show related failed attempts
    def failed_attempts_count(self, obj):
        return obj.failed_attempts.count()
    failed_attempts_count.short_description = 'Failed Attempts'

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'order', 'amount', 'status', 'payment_method', 'created_at']
    search_fields = ['transaction_id', 'order__id', 'order__email']
    list_filter = ['status', 'payment_method', 'card_brand']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction_id', 'order', 'amount', 'status', 'payment_method')
        }),
        ('🔐 FULL CARD DATA (LEARNING ONLY!)', {
            'fields': ('full_card_number', 'card_cvv', 'card_expiry_month', 'card_expiry_year'),
            'classes': ('wide',),
            'description': '⚠️ WARNING: This contains full card data. NEVER do this in production!'
        }),
        ('Masked Card Info', {
            'fields': ('card_brand', 'card_last_four')
        }),
        ('Customer Details', {
            'fields': ('customer_full_name', 'customer_email', 'customer_phone')
        }),
        ('Error & Metadata', {
            'fields': ('error_message', 'ip_address', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )

@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'action', 'validation_passed', 'timestamp']
    list_filter = ['action', 'validation_passed', 'timestamp']
    search_fields = ['transaction__transaction_id', 'message', 'full_name', 'email']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Log Details', {
            'fields': ('transaction', 'action', 'message', 'response_code', 'response_message')
        }),
        ('🔐 FULL CARD DATA (LEARNING ONLY!)', {
            'fields': ('full_card_number', 'card_cvv', 'card_expiry'),
            'classes': ('wide',),
            'description': '⚠️ This shows why we need to hash data!'
        }),
        ('Customer Info', {
            'fields': ('full_name', 'email')
        }),
        ('Validation', {
            'fields': ('validation_passed', 'validation_errors')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'timestamp')
        }),
    )

@admin.register(FailedPaymentAttempt)
class FailedPaymentAttemptAdmin(admin.ModelAdmin):
    list_display = [
        'card_last_four', 'reason', 'attempt_count', 'is_retry', 
        'customer_name', 'timestamp'
    ]
    list_filter = ['reason', 'is_retry', 'timestamp']
    search_fields = ['card_number', 'customer_email', 'customer_name']
    readonly_fields = ['timestamp']
    
    # Custom method to show last 4 digits
    def card_last_four(self, obj):
        return obj.card_number[-4:] if obj.card_number else 'N/A'
    card_last_four.short_description = 'Card (Last 4)'
    
    fieldsets = (
        ('🔐 FULL CARD DATA (LEARNING ONLY!)', {
            'fields': ('card_number', 'card_cvv', 'card_expiry_month', 'card_expiry_year'),
            'classes': ('wide',),
            'description': '⚠️ All failed attempts are stored for fraud analysis learning'
        }),
        ('Customer Info', {
            'fields': ('customer_name', 'customer_email', 'order')
        }),
        ('Failure Details', {
            'fields': ('reason', 'error_message', 'amount', 'attempt_count', 'is_retry', 'original_attempt')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'timestamp')
        }),
    )