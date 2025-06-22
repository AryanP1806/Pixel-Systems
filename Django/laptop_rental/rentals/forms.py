from django import forms
from .models import Customer, Rental, ProductAsset, ProductConfiguration
from django_select2.forms import Select2Widget
from .models import Rental
from django.db.models import Q



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

     
class RentalForm(forms.ModelForm):
    # Custom fields not part of the Rental model
    payment_amount = forms.DecimalField(max_digits=10, decimal_places=2, required=True)
    payment_status = forms.ChoiceField(choices=[('pending', 'Pending'), ('paid', 'Paid')])
    payment_method = forms.ChoiceField(
        choices=[('cash', 'Cash'), ('upi', 'UPI'), ('bank', 'Bank Transfer'), ('card', 'Card')],
        required=True
    )

    class Meta:
        model = Rental
        fields = [
            'customer',
            'asset',
            'rental_start_date',
            'duration_days',
            'contract_number',
            'made_by',
            'status'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'autocomplete'}),
            'asset': forms.Select(attrs={'class': 'autocomplete'}),
            'rental_start_date': forms.DateInput(attrs={'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # ✅ call this first

        current_instance = kwargs.get('instance', None)

        from rentals.models import Rental, ProductAsset
        from django.db.models import Q

        # Get all assets currently in ongoing rentals
        ongoing_asset_ids = Rental.objects.filter(status='ongoing').values_list('asset_id', flat=True)

        if current_instance:
            self.fields['asset'].queryset = ProductAsset.objects.filter(
                Q(id=current_instance.asset_id) | ~Q(id__in=ongoing_asset_ids)
            )
        else:
            self.fields['asset'].queryset = ProductAsset.objects.exclude(id__in=ongoing_asset_ids)
