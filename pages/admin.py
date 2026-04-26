# pages/admin.py
from django.contrib import admin
from .models import ContractAgreement, PaymentMethod

@admin.register(ContractAgreement)
class ContractAgreementAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'get_payment_methods', 'contract_duration', 'created_at']
    list_filter = ['created_at', 'agree_to_promote', 'payment_methods']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    readonly_fields = ['created_at', 'ip_address']
    filter_horizontal = ['payment_methods']  # This gives a nice widget for ManyToMany
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Address Information', {
            'fields': ('street_address', 'address_line2', 'city', 'state_region', 'postal_code', 'country')
        }),
        ('Contract Details', {
            'fields': ('contract_duration', 'payment_methods', 'bank_name')
        }),
        ('Agreement Terms', {
            'fields': ('agree_to_promote', 'agree_to_post_twice')
        }),
        ('Signature & Metadata', {
            'fields': ('signature', 'created_at', 'ip_address')
        }),
    )
    
    def get_payment_methods(self, obj):
        """Display selected payment methods as a comma-separated list"""
        return ", ".join([method.name for method in obj.payment_methods.all()])
    get_payment_methods.short_description = 'Payment Methods'

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']