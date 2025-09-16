from django import forms
from .models import Customer, Rental, ProductAsset, ProductConfiguration, PendingProduct, PendingCustomer, PendingRental, PendingProductConfiguration, Supplier, Repair,AssetType, HDDOption, RAMOption, GraphicsOption, DisplaySizeOption,CPUOption
from django_select2.forms import Select2Widget
# from .models import Rental
from django.db.models import Q
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from dal import autocomplete

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

from django import forms
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from .models import ProductAsset, PendingProduct

class ProductAssetForm(forms.ModelForm):
    class Meta:
        model = ProductAsset
        fields = '__all__'
        exclude = ['edited_by', 'edited_at', 'revenue']
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
        self.original_instance = kwargs.get('instance', None)

    # -------------------------------
    # Asset ID Validation
    # -------------------------------
    def clean_asset_id(self):
        asset_id = self.cleaned_data.get('asset_id')
        if asset_id:
            if ProductAsset.objects.exclude(pk=getattr(self.original_instance, 'pk', None)).filter(asset_id=asset_id).exists():
                raise ValidationError("⚠️ Asset ID already exists. Please choose a unique one.")
        return asset_id

    # -------------------------------
    # Asset Number Validation
    # -------------------------------
    def clean_asset_number(self):
        asset_number = self.cleaned_data.get('asset_number')
        asset_suffix = self.cleaned_data.get('asset_suffix', '')

        # If still missing, try to derive it from asset_id
        if not asset_number:
            asset_id = self.cleaned_data.get('asset_id')
            if asset_id:
                try:
                    asset_number = int(asset_id.split('/')[-1].split()[0])
                except (ValueError, IndexError):
                    asset_number = None

        # Validate uniqueness if we have a valid number
        if asset_number is not None:
            conflict_products = ProductAsset.objects.filter(
                asset_number=asset_number,
                asset_suffix=asset_suffix
            ).exclude(pk=self.instance.pk)

            conflict_pending = PendingProduct.objects.filter(
                asset_number=asset_number,
                asset_suffix=asset_suffix
            )

            if conflict_products.exists() or conflict_pending.exists():
                raise ValidationError("⚠️ This Asset Number + Suffix combination already exists.")

        return asset_number

    # -------------------------------
    # Global Clean Method
    # -------------------------------
    def clean(self):
        cleaned = super().clean()

        # 1️⃣ Handle asset_id generation only if missing
        if not cleaned.get('asset_id'):
            year = cleaned['purchase_date'].year if cleaned.get('purchase_date') else now().year
            prefix = f"Pixel/{year}/"

            # Gather existing IDs from both ProductAsset and PendingProduct
            existing_ids = list(ProductAsset.objects.filter(asset_id__startswith=prefix).values_list('asset_id', flat=True)) + \
                           list(PendingProduct.objects.filter(asset_id__startswith=prefix).values_list('asset_id', flat=True))

            # Check if user manually entered asset_number
            manual_number = cleaned.get('asset_number')

            if manual_number:  # ✅ Use provided asset_number directly
                suffix = str(manual_number).zfill(3)
                new_id = f"{prefix}{suffix}"

                if new_id in existing_ids:
                    self.add_error('asset_number', "⚠️ This Asset Number already exists for the selected year.")
                else:
                    cleaned['asset_id'] = new_id
                    self.instance.asset_id = new_id
                    self.instance.asset_number = manual_number
            else:
                # Auto-generate asset_number and asset_id if none given
                number = 1
                while True:
                    suffix = str(number).zfill(3)
                    new_id = f"{prefix}{suffix}"
                    if new_id not in existing_ids:
                        cleaned['asset_id'] = new_id
                        self.instance.asset_id = new_id
                        self.instance.asset_number = number
                        break
                    number += 1

        # 2️⃣ Validate based on condition_status
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

    # -------------------------------
    # Save Method
    # -------------------------------
    def save(self, commit=True):
        return super().save(commit=commit)
    

class PendingProductForm(forms.ModelForm):
    class Meta:
        model = PendingProduct
        fields = '__all__'
        exclude = ['asset_number','','edited_by', 'edited_at', 'revenue']
        widgets = {
            'asset_id': forms.TextInput(attrs={'placeholder': 'Leave blank to auto-generate'}),
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'under_warranty': forms.CheckboxInput(),
            'sale_date': forms.DateInput(attrs={'type': 'date'}),
            'purchased_from': forms.Select(attrs={'class': 'autocomplete'}),
            'type_of_asset': forms.Select(attrs={'class': 'form-control'}),
            'date_marked_dead': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.original_instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

    def clean_asset_id(self):
        asset_id = self.cleaned_data['asset_id']
        if ProductAsset.objects.exclude(pk=getattr(self.original_instance, 'pk', None)).filter(asset_id=asset_id).exists():
            raise forms.ValidationError("Asset ID already exists. Please choose a unique one.")
        return asset_id

    def clean_serial_no(self):
        serial_no = self.cleaned_data['serial_no']
        if ProductAsset.objects.exclude(pk=getattr(self.original_instance, 'pk', None)).filter(serial_no=serial_no).exists():
            raise forms.ValidationError("Serial number already exists.")
        return serial_no

    def clean_asset_number(self):
        asset_number = self.cleaned_data.get('asset_number')
        asset_suffix = self.cleaned_data.get('asset_suffix')
        if not asset_suffix:
            asset_suffix = ""
        if asset_number:
            asset_suffix = asset_suffix or ""

            if ProductAsset.objects.exclude(pk=getattr(self.original_instance, 'pk', None)).filter(asset_number=asset_number, asset_suffix=asset_suffix).exists():
                raise forms.ValidationError("Asset number already exists.")
        return asset_number
    
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
    
    # def save(self, *args, **kwargs):
    #     if not self.asset_id:
    #         year = self.purchase_date.year if self.purchase_date else now().year
    #         prefix = f"Pixel/{year}/"
    #         existing_ids = list(
    #             ProductAsset.objects.filter(asset_id__startswith=prefix).values_list('asset_id', flat=True)
    #         ) + list(
    #             PendingProduct.objects.filter(asset_id__startswith=prefix).values_list('asset_id', flat=True)
    #         )

    #         number = 1
    #         while True:
    #             suffix = str(number).zfill(3)
    #             new_id = prefix + suffix
    #             if new_id not in existing_ids:
    #                 self.asset_id = new_id
    #                 break
    #             number += 1

    #     super().save(*args, **kwargs)





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
        self.fields['date_of_config'].widget = forms.DateInput(attrs={'type': 'date'})

# class RentalForm(forms.ModelForm):
#     class Meta:
#         model = Rental
#         fields = '__all__'

    
class RentalForm(forms.ModelForm):
    class Meta:
        model = Rental
        fields = [
            'customer',
            'asset',
            'payment_amount',
            'rental_start_date',
            'contract_number',
            'contract_validity',
            'status',
            'billing_day',
            'rental_end_date'
        ]
        widgets = {
            'customer': autocomplete.ModelSelect2(
                url='customer-autocomplete',
                attrs={
                    'data-placeholder': 'Search for a customer...',
                    'data-minimum-input-length': 1,
                }
            ),
            'asset': autocomplete.ModelSelect2(
                url='asset-autocomplete',
                attrs={
                    'data-placeholder': 'Search for an asset...',
                    'data-minimum-input-length': 1,
                }
            ),
            'rental_start_date': forms.DateInput(attrs={'type': 'date'}),
            'rental_end_date': forms.DateInput(attrs={'type': 'date'}),
            'contract_validity': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        current_instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        # Filter available assets for rental
        rented_ids = Rental.objects.filter(
            status__in=['ongoing', 'overdue'],
            asset__isnull=False
        ).values_list('asset_id', flat=True)

        if current_instance and current_instance.asset:
            # Allow the already selected asset to remain in the dropdown
            available_assets = ProductAsset.objects.filter(
                Q(id=current_instance.asset.id) | (
                    Q(condition_status='working') & ~Q(id__in=rented_ids)
                )
            )
        else:
            available_assets = ProductAsset.objects.filter(
                condition_status='working'
            ).exclude(id__in=rented_ids)

        # Set the queryset for the autocomplete widget
        self.fields['asset'].queryset = available_assets
        self.fields['customer'].queryset = Customer.objects.all()



class PendingRentalForm(forms.ModelForm):
    payment_amount = forms.DecimalField(max_digits=10, decimal_places=2, required=True)
    payment_status = forms.ChoiceField(choices=[('pending', 'Pending'), ('paid', 'Paid')])
    payment_method = forms.ChoiceField(
        choices=[('cash', 'Cash'), ('upi', 'UPI'), ('bank', 'Bank Transfer'), ('card', 'Card')],
        required=True
    )

    class Meta:
        model = PendingRental
        include = ['customer', 'asset', 'rental_start_date', 'contract_number', 'status', 'billing_day', 'rental_end_date']
        exclude = ['submitted_by', 'submitted_at']
        widgets = {
            'customer': forms.Select(attrs={'class': 'autocomplete'}),
            'asset': forms.Select(attrs={'class': 'autocomplete'}),
            'rental_start_date': forms.DateInput(attrs={'type': 'date'}),
            'rental_end_date': forms.DateInput(attrs={'type': 'date'}),
            'contract_validity': forms.DateInput(attrs={'type': 'date'}),
        
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
