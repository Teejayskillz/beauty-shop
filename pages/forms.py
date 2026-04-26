# pages/forms.py
from django import forms
from .models import ContractAgreement

class ContractAgreementForm(forms.ModelForm):
    contract_duration = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'month',
            'class': 'date-picker',
            'placeholder': 'Select contract duration',
        }),
        help_text="Select contract duration"
    )
    
    class Meta:
        model = ContractAgreement
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'street_address', 'address_line2', 'city', 'state_region', 
            'postal_code', 'country', 'contract_duration', 'payment_method',
            'bank_name', 'agree_to_promote', 'agree_to_post_twice', 'signature'
        ]
        widgets = {
            'signature': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your full name as electronic signature...'}),
            'address_line2': forms.TextInput(attrs={'placeholder': 'Apartment, suite, unit, etc. (optional)'}),
        }
    
    def clean_contract_duration(self):
        contract_duration = self.cleaned_data.get('contract_duration')
        if contract_duration:
            # If it's a string in YYYY-MM format, convert to date
            if isinstance(contract_duration, str):
                from datetime import datetime
                try:
                    # Parse the month string and set to first day of month
                    contract_duration = datetime.strptime(contract_duration, '%Y-%m').date()
                except ValueError:
                    raise forms.ValidationError('Please select a valid month and year.')
        return contract_duration
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        bank_name = cleaned_data.get('bank_name')
        
        if payment_method == 'echeck' and not bank_name:
            self.add_error('bank_name', 'Bank name is required for E-check payment')
        
        return cleaned_data