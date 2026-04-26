# pages/forms.py
from django import forms
from .models import ContractAgreement

class ContractAgreementForm(forms.ModelForm):
    contract_duration = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'month',  # This shows month/year picker instead of full date
            'class': 'date-picker',
            'placeholder': 'Select contract start month',
            'onclick': 'this.showPicker()',
        }),
        help_text="Select the start month of your contract"
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
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        bank_name = cleaned_data.get('bank_name')
        
        if payment_method == 'echeck' and not bank_name:
            self.add_error('bank_name', 'Bank name is required for E-check payment')
        
        return cleaned_data