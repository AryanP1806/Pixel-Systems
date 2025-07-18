from django import forms
from .models import Customer, Rental, ProductAsset, ProductConfiguration, PendingProduct, PendingCustomer, PendingRental, PendingProductConfiguration
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



class PendingCustomerForm(forms.ModelForm):
    class Meta:
        model = PendingCustomer
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
        # fields = {
        #     'asset_id','type_of_asset', 'brand', 'model_no', 'serial_no',
        #     'purchase_price', 'current_value', 'purchase_date','under_warranty','warranty_duration_months',
        #     'purchased_from'
        # }
        fields = '__all__'
        exclude = ['edited_by']
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'under_warranty': forms.CheckboxInput(),
            'sale_date': forms.DateInput(attrs={'type': 'date'})
        }




class PendingProductForm(forms.ModelForm):
    class Meta:
        model = PendingProduct
        fields = '__all__'
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
        }



class ProductConfigurationForm(forms.ModelForm):
    class Meta:
        model = ProductConfiguration
        fields = ['date_of_config', 'ram', 'hdd', 'ssd', 'graphics', 'display_size', 'power_supply', 'detailed_config', 'repair_cost']

        widgets = {
            'date_of_config': forms.DateInput(attrs={'type': 'date'}),
        }



class PendingProductConfigurationForm(forms.ModelForm):
    class Meta:
        model = PendingProductConfiguration
        exclude = ['asset', 'submitted_by', 'submitted_at']


# class RentalForm(forms.ModelForm):
#     class Meta:
#         model = Rental
#         fields = '__all__'

     
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
            'status'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'autocomplete'}),
            'asset': forms.Select(attrs={'class': 'autocomplete'}),
            'rental_start_date': forms.DateInput(attrs={'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        current_instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        rented_ids = Rental.objects.filter(
            status__in=['ongoing', 'overdue'],
            asset__isnull=False
        ).values_list('asset_id', flat=True)

        if current_instance and current_instance.asset:
            # Allow the already selected asset to remain in the dropdown
            self.fields['asset'].queryset = ProductAsset.objects.filter(
                Q(id=current_instance.asset.id) | (
                    Q(condition_status='working', is_sold=False) & ~Q(id__in=rented_ids)
                )
            )
        else:
            self.fields['asset'].queryset = ProductAsset.objects.filter(
                condition_status='working',
                is_sold=False
            ).exclude(id__in=rented_ids)



class PendingRentalForm(forms.ModelForm):
    payment_amount = forms.DecimalField(max_digits=10, decimal_places=2, required=True)
    payment_status = forms.ChoiceField(choices=[('pending', 'Pending'), ('paid', 'Paid')])
    payment_method = forms.ChoiceField(
        choices=[('cash', 'Cash'), ('upi', 'UPI'), ('bank', 'Bank Transfer'), ('card', 'Card')],
        required=True
    )

    class Meta:
        model = PendingRental
        exclude = ['submitted_by', 'submitted_at']
        widgets = {
            'customer': forms.Select(attrs={'class': 'autocomplete'}),
            'asset': forms.Select(attrs={'class': 'autocomplete'}),
            'rental_start_date': forms.DateInput(attrs={'type': 'date'})
        }
    
    def __init__(self, *args, **kwargs):
        current_instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        rented_ids = Rental.objects.filter(
            status__in=['ongoing', 'overdue'],
            asset__isnull=False
        ).values_list('asset_id', flat=True)

        if current_instance and current_instance.asset:
            # Allow the already selected asset to remain in the dropdown
            self.fields['asset'].queryset = ProductAsset.objects.filter(
                Q(id=current_instance.asset.id) | (
                    Q(condition_status='working', is_sold=False) & ~Q(id__in=rented_ids)
                )
            )
        else:
            self.fields['asset'].queryset = ProductAsset.objects.filter(
                condition_status='working',
                is_sold=False
            ).exclude(id__in=rented_ids)




# class SellProductForm(forms.ModelForm):
#     class Meta:
#         model = ProductAsset
#         fields = ['sold_to', 'sale_price', 'sale_date']
#         widgets = {
#             'sale_date': forms.DateInput(attrs={'type': 'date'})
#         }
