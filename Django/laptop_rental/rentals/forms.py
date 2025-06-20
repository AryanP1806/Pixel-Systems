from django import forms
from .models import Customer, ProductUnit, Rental

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

class ProductForm(forms.ModelForm):
    class Meta:
        model = ProductUnit
        fields = '__all__'

class RentalForm(forms.ModelForm):
    class Meta:
        model = Rental
        fields = '__all__'
