# pages/forms.py
from django import forms
from .models import ContractAgreement, PaymentMethod

class ContractAgreementForm(forms.ModelForm):
    contract_duration = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'month',
            'class': 'date-picker',
            'placeholder': 'Select contract duration',
        }),
        help_text="Select contract duration"
    )
    
    # Override payment_methods to use checkboxes
    payment_methods = forms.ModelMultipleChoiceField(
        queryset=PaymentMethod.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'payment-checkbox-group'}),
        required=False,
        label="Payment Method"
    )
    
    class Meta:
        model = ContractAgreement
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'street_address', 'address_line2', 'city', 'state_region', 
            'postal_code', 'country', 'contract_duration', 'payment_methods',
            'bank_name', 'agree_to_promote', 'agree_to_post_twice', 'signature'
        ]
        widgets = {
            'signature': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your full name as electronic signature...'}),
            'address_line2': forms.TextInput(attrs={'placeholder': 'Apartment, suite, unit, etc. (optional)'}),
        }
    
    def clean_contract_duration(self):
        contract_duration = self.cleaned_data.get('contract_duration')
        if contract_duration:
            if isinstance(contract_duration, str):
                from datetime import datetime
                try:
                    contract_duration = datetime.strptime(contract_duration, '%Y-%m').date()
                except ValueError:
                    raise forms.ValidationError('Please select a valid month and year.')
        return contract_duration
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create default payment methods if none exist
        if PaymentMethod.objects.count() == 0:
            PaymentMethod.objects.create(name='E-check', code='echeck')
            PaymentMethod.objects.create(name='Credit card', code='credit_card')