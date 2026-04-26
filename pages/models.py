# pages/models.py
from django.db import models

class ContractAgreement(models.Model):
    PAYMENT_METHODS = [
        ('echeck', 'E-check'),
        ('credit_card', 'Credit card'),
    ]
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    # Address Information
    street_address = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state_region = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    
    # Contract Details
    contract_duration = models.DateField(help_text="Select contract start date")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    bank_name = models.CharField(max_length=255, blank=True, null=True, help_text="Required for E-check")
    
    # Agreement Terms
    agree_to_promote = models.BooleanField(default=False)
    agree_to_post_twice = models.BooleanField(default=False)
    
    # Signature
    signature = models.TextField(help_text="Electronic signature")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.contract_duration.strftime('%b %Y')}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_address(self):
        address = self.street_address
        if self.address_line2:
            address += f", {self.address_line2}"
        address += f", {self.city}, {self.state_region} {self.postal_code}, {self.country}"
        return address
    
    @property
    def contract_duration_display(self):
        return self.contract_duration.strftime('%B %Y')