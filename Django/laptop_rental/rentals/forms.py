from django import forms
from .models import Customer, Rental, ProductAsset, ProductConfiguration

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'name', 'email',
            'phone_number_primary', 'phone_number_secondary',
            'address_primary', 'address_secondary',
            'is_permanent', 'is_bni_member'
        ]
        widgets = {
            'is_permanent': forms.CheckboxInput(),
            'is_bni_member': forms.CheckboxInput(),
        }

class ProductAssetForm(forms.ModelForm):
    class Meta:
        model = ProductAsset
        fields = '__all__'

class ProductConfigurationForm(forms.ModelForm):
    class Meta:
        model = ProductConfiguration
        exclude = ['asset'] 

class RentalForm(forms.ModelForm):
    class Meta:
        model = Rental
        fields = '__all__'
