# pages/admin.py
from django.contrib import admin
from .models import ContractAgreement

@admin.register(ContractAgreement)
class ContractAgreementAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'contract_duration', 'payment_method', 'created_at']
    search_fields = ['first_name', 'last_name', 'email']
    list_filter = ['payment_method', 'created_at']