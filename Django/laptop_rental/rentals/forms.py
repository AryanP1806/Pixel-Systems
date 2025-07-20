from django import forms
from .models import Customer, Rental, ProductAsset, ProductConfiguration, PendingProduct, PendingCustomer, PendingRental, PendingProductConfiguration, Supplier, Repair,AssetType, HDDOption, RAMOption, GraphicsOption, DisplaySizeOption,CPUOption
from django_select2.forms import Select2Widget
from .models import Rental
from django.db.models import Q
from django.utils.timezone import now
from django.core.exceptions import ValidationError


class CPUOptionForm(forms.ModelForm):
    class Meta:
        model = CPUOption
        fields = ['name', 'order']

class HDDOptionForm(forms.ModelForm):
    class Meta:
        model = HDDOption
        fields = ['name', 'order']

class RAMOptionForm(forms.ModelForm):
    class Meta:
        model = RAMOption
        fields = ['name', 'order']

class DisplaySizeOptionForm(forms.ModelForm):
    class Meta:
        model = DisplaySizeOption
        fields = ['name', 'order']

class GraphicsOptionForm(forms.ModelForm):
    class Meta:
        model = GraphicsOption
        fields = ['name', 'order']

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'name', 'email',
            'phone_number_primary', 'phone_number_secondary',
            'address_primary', 'address_secondary',
            'reference_name','is_permanent', 'is_bni_member', 
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
             'reference_name','is_permanent', 'is_bni_member',
        ]
        widgets = {
            'is_permanent': forms.CheckboxInput(),
            'is_bni_member': forms.CheckboxInput(),
        }


class AssetTypeForm(forms.ModelForm):
    class Meta:
        model = AssetType
        fields = ['name', 'display_order']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Asset Type Name'}),
            'display_order': forms.NumberInput(attrs={'min': 0}),
        }

class ProductAssetForm(forms.ModelForm):
    class Meta:
        model = ProductAsset
        fields = '__all__'
        exclude = ['edited_by', 'edited_at']
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'under_warranty': forms.CheckboxInput(),
            'sale_date': forms.DateInput(attrs={'type': 'date'}),
            'purchased_from': forms.Select(attrs={'class': 'autocomplete'}),
            'type_of_asset': forms.Select(attrs={'class': 'form-control'}),
            'date_marked_dead': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['type_of_asset'].queryset = AssetType.objects.all()


    def clean_asset_number(self):
        asset_number = self.cleaned_data.get('asset_number')
        qs = ProductAsset.objects.filter(asset_id=asset_number)
        
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
            return asset_number
        if asset_number:
            exists_main = ProductAsset.objects.filter(asset_number=asset_number).exists()
            exists_pending = PendingProduct.objects.filter(asset_number=asset_number).exists()
            if exists_main or exists_pending:
                raise forms.ValidationError("Asset id already exists. Please enter a unique number.")
        return asset_number

    def clean_asset_id(self):
        asset_id = self.cleaned_data.get('asset_id')
        qs = ProductAsset.objects.filter(asset_id=asset_id)
        # Skip check if empty, let save() generate it
        if not asset_id:
            return asset_id

        # Check in both ProductAsset and PendingProduct
        exists_in_main = ProductAsset.objects.filter(asset_id=asset_id).exists()
        exists_in_pending = PendingProduct.objects.filter(asset_id=asset_id).exists()

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
            return asset_id
        if exists_in_main or exists_in_pending:
            raise ValidationError("Asset ID already exists. Please choose a unique one.")
        return asset_id

    def clean_serial_no(self):
        serial_no = self.cleaned_data.get('serial_no')
        qs = ProductAsset.objects.filter(serial_no=serial_no)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError("Serial number already exists.")

        return serial_no


    def clean(self):
        cleaned = super().clean()
        condition = cleaned.get("condition_status")

        if condition == "sold":
            if not cleaned.get("sold_to"):
                self.add_error('sold_to', "This field is required for sold items.")
            if not cleaned.get("sale_price"):
                self.add_error('sale_price', "Sale price required.")
            if not cleaned.get("sale_date"):
                self.add_error('sale_date', "Sale date required.")

        elif condition == "damaged":
            if not cleaned.get("date_marked_dead"):
                self.add_error('date_marked_dead', "Damage date is required.")
            if not cleaned.get("damage_narration"):
                self.add_error('damage_narration', "Please provide damage narration.")

        return cleaned
    
    

class PendingProductForm(forms.ModelForm):
    class Meta:
        model = PendingProduct
        fields = '__all__'
        exclude = ['edited_by', 'edited_at']
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'under_warranty': forms.CheckboxInput(),
            'sale_date': forms.DateInput(attrs={'type': 'date'}),
            'purchased_from': forms.Select(attrs={'class': 'autocomplete'}),
            'type_of_asset': forms.Select(attrs={'class': 'form-control'}),
            'date_marked_dead': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_asset_number(self):
        asset_number = self.cleaned_data.get('asset_number')
        qs = ProductAsset.objects.filter(asset_id=asset_number)
        
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
            return asset_number
        if asset_number:
            exists_main = ProductAsset.objects.filter(asset_number=asset_number).exists()
            exists_pending = PendingProduct.objects.filter(asset_number=asset_number).exists()
            if exists_main or exists_pending:
                raise forms.ValidationError("Asset id already exists. Please enter a unique number.")
        return asset_number

    def clean_asset_id(self):
        asset_id = self.cleaned_data.get('asset_id')
        qs = ProductAsset.objects.filter(asset_id=asset_id)
        # Skip check if empty, let save() generate it
        if not asset_id:
            return asset_id

        # Check in both ProductAsset and PendingProduct
        exists_in_main = ProductAsset.objects.filter(asset_id=asset_id).exists()
        exists_in_pending = PendingProduct.objects.filter(asset_id=asset_id).exists()

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
            return asset_id
        if exists_in_main or exists_in_pending:
            raise ValidationError("Asset ID already exists. Please choose a unique one.")
        return asset_id

    def clean_serial_no(self):
        serial_no = self.cleaned_data.get('serial_no')
        qs = ProductAsset.objects.filter(serial_no=serial_no)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError("Serial number already exists.")

        return serial_no


    def clean(self):
        cleaned = super().clean()
        condition = cleaned.get("condition_status")

        if condition == "sold":
            if not cleaned.get("sold_to"):
                self.add_error('sold_to', "This field is required for sold items.")
            if not cleaned.get("sale_price"):
                self.add_error('sale_price', "Sale price required.")
            if not cleaned.get("sale_date"):
                self.add_error('sale_date', "Sale date required.")

        elif condition == "damaged":
            if not cleaned.get("date_marked_dead"):
                self.add_error('date_marked_dead', "Damage date is required.")
            if not cleaned.get("damage_narration"):
                self.add_error('damage_narration', "Please provide damage narration.")

        return cleaned

    def save(self, *args, **kwargs):
        if not self.asset_id:
            year = self.purchase_date.year if self.purchase_date else now().year
            prefix = f"Pixel/{year}/"
            existing_ids = list(
                ProductAsset.objects.filter(asset_id__startswith=prefix).values_list('asset_id', flat=True)
            ) + list(
                PendingProduct.objects.filter(asset_id__startswith=prefix).values_list('asset_id', flat=True)
            )

            number = 1
            while True:
                suffix = str(number).zfill(3)
                new_id = prefix + suffix
                if new_id not in existing_ids:
                    self.asset_id = new_id
                    break
                number += 1

        super().save(*args, **kwargs)





# class ProductConfigurationForm(forms.ModelForm):
#     class Meta:
#         model = ProductConfiguration
#         fields = ['date_of_config', 'ram', 'hdd', 'ssd', 'graphics', 'display_size', 'power_supply', 'detailed_config']

#         widgets = {
#             'date_of_config': forms.DateInput(attrs={'type': 'date'}),
#         }

class ProductConfigurationForm(forms.ModelForm):
    class Meta:
        model = ProductConfiguration
        fields = '__all__'
        exclude = ['asset', 'edited_by', 'edited_at']
        widgets = {
            'date_of_config': forms.DateInput(attrs={'type': 'date'}),
            # 'asset': forms.HiddenInput()
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['asset'].widget = Select2Widget(attrs={'class': 'autocomplete'})
        self.fields['cpu'].queryset = CPUOption.objects.all().order_by('order')
        self.fields['hdd'].queryset = HDDOption.objects.all().order_by('order')
        self.fields['ram'].queryset = RAMOption.objects.all().order_by('order')
        self.fields['display_size'].queryset = DisplaySizeOption.objects.all().order_by('order')
        self.fields['graphics'].queryset = GraphicsOption.objects.all().order_by('order')


class PendingProductConfigurationForm(forms.ModelForm):
    class Meta:
        model = PendingProductConfiguration
        exclude = ['asset', 'submitted_by', 'submitted_at']
        widgets = {
            'date_of_config': forms.DateInput(attrs={'type': 'date'}),
            'asset': forms.HiddenInput()
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['asset'].widget = Select2Widget(attrs={'class': 'autocomplete'})
        self.fields['cpu'].queryset = CPUOption.objects.all().order_by('order')
        self.fields['hdd'].queryset = HDDOption.objects.all().order_by('order')
        self.fields['ram'].queryset = RAMOption.objects.all().order_by('order')
        self.fields['display_size'].queryset = DisplaySizeOption.objects.all().order_by('order')
        self.fields['graphics'].queryset = GraphicsOption.objects.all().order_by('order')


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
            'contract_number',
            'status',
            'billing_day'
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
                    Q(condition_status='working') & ~Q(id__in=rented_ids)
                )
            )
        else:
            self.fields['asset'].queryset = ProductAsset.objects.filter(
                condition_status='working'
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
                    Q(condition_status='working') & ~Q(id__in=rented_ids)
                )
            )
        else:
            self.fields['asset'].queryset = ProductAsset.objects.filter(
                condition_status='working'
            ).exclude(id__in=rented_ids)




class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = '__all__'

# class SellProductForm(forms.ModelForm):
#     class Meta:
#         model = ProductAsset
#         fields = ['sold_to', 'sale_price', 'sale_date']
#         widgets = {
#             'sale_date': forms.DateInput(attrs={'type': 'date'})
#         }


class RepairForm(forms.ModelForm):
    class Meta:
        model = Repair
        fields = ['product', 'name', 'date', 'cost']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: Only show assets that are not sold or missing
        self.fields['product'].queryset = ProductAsset.objects.exclude(condition_status='missing').order_by('asset_id')
