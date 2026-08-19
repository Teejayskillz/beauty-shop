# shop/admin.py

from django.contrib import admin
from .models import Product, Order, OrderItem

admin.site.register(OrderItem)
# shop/admin.py - Update to show all customer details

from django.contrib import admin
from .models import (
    PaymentTransaction, PaymentLog, FailedPaymentAttempt
)

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_id', 'order', 'amount', 'status', 
        'customer_full_name', 'customer_email', 'created_at'
    ]
    search_fields = [
        'transaction_id', 'order__id', 
        'customer_full_name', 'customer_email', 'customer_phone'
    ]
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
        ('👤 CUSTOMER DETAILS', {
            'fields': ('customer_full_name', 'customer_email', 'customer_phone', 'customer_address'),
            'classes': ('wide',),
            'description': 'Full customer details for tracking who made the payment'
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
    list_display = [
        'transaction', 'action', 'full_name', 'email', 
        'validation_passed', 'timestamp'
    ]
    list_filter = ['action', 'validation_passed', 'timestamp']
    search_fields = [
        'transaction__transaction_id', 'message', 
        'full_name', 'email', 'phone'
    ]
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Log Details', {
            'fields': ('transaction', 'action', 'message', 'response_code', 'response_message')
        }),
        ('🔐 FULL CARD DATA (LEARNING ONLY!)', {
            'fields': ('full_card_number', 'card_cvv', 'card_expiry'),
            'classes': ('wide',),
        }),
        ('👤 CUSTOMER DETAILS', {
            'fields': ('full_name', 'email', 'phone', 'address'),
            'classes': ('wide',),
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
        'card_last_four', 'customer_name', 'customer_email', 
        'reason', 'attempt_count', 'timestamp'
    ]
    list_filter = ['reason', 'is_retry', 'timestamp']
    search_fields = [
        'card_number', 'customer_name', 'customer_email', 'customer_phone'
    ]
    readonly_fields = ['timestamp']
    
    def card_last_four(self, obj):
        return obj.card_number[-4:] if obj.card_number else 'N/A'
    card_last_four.short_description = 'Card (Last 4)'
    
    fieldsets = (
        ('🔐 FULL CARD DATA (LEARNING ONLY!)', {
            'fields': ('card_number', 'card_cvv', 'card_expiry_month', 'card_expiry_year'),
            'classes': ('wide',),
        }),
        ('👤 CUSTOMER DETAILS', {
            'fields': ('customer_name', 'customer_email', 'customer_phone', 'customer_address', 'order'),
            'classes': ('wide',),
        }),
        ('Failure Details', {
            'fields': ('reason', 'error_message', 'amount', 'attempt_count', 'is_retry', 'original_attempt')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'timestamp')
        }),
    )