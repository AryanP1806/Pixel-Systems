from rest_framework import serializers
from .models import (
    Customer, ProductAsset, Rental, ProductConfiguration, Repair, Supplier,
    PendingCustomer, PendingProduct, PendingRental, PendingProductConfiguration, PendingRepair,
    AssetType, CPUOption, HDDOption, RAMOption, DisplaySizeOption, GraphicsOption
)

# ===================================================================
# 1. OPTION SERIALIZERS (For Mobile Dropdowns)
# ===================================================================
class AssetTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetType
        fields = ['id', 'name']

class CPUOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPUOption
        fields = ['id', 'name']

class RAMOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RAMOption
        fields = ['id', 'name']

class HDDOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HDDOption
        fields = ['id', 'name']

class GraphicsOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GraphicsOption
        fields = ['id', 'name']

class DisplaySizeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisplaySizeOption
        fields = ['id', 'name']


# ===================================================================
# 2. MAIN MODEL SERIALIZERS (Read & Write)
# ===================================================================

# --- CUSTOMER ---
class CustomerSerializer(serializers.ModelSerializer):
    edited_by_name = serializers.ReadOnlyField(source='edited_by.username')

    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ['edited_by', 'edited_at']


# --- PRODUCT ASSET ---
class ProductAssetSerializer(serializers.ModelSerializer):
    # Read-Only fields for display (shows "Laptop" instead of "1")
    type_of_asset_name = serializers.ReadOnlyField(source='type_of_asset.name')
    purchased_from_name = serializers.ReadOnlyField(source='purchased_from.name')
    edited_by_name = serializers.ReadOnlyField(source='edited_by.username')

    class Meta:
        model = ProductAsset
        fields = '__all__'
        # This allows you to send ID '1' when saving, but read Name 'Dell' when viewing
        extra_kwargs = {
            'type_of_asset': {'write_only': True},
            'purchased_from': {'write_only': True},
            'edited_by': {'read_only': True},
            'revenue': {'read_only': True}
        }


# --- RENTAL ---
class RentalSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.name')
    asset_id_display = serializers.ReadOnlyField(source='asset.asset_id')
    edited_by_name = serializers.ReadOnlyField(source='edited_by.username')

    class Meta:
        model = Rental
        fields = '__all__'
        extra_kwargs = {
            'customer': {'write_only': True},
            'asset': {'write_only': True},
            'edited_by': {'read_only': True}
        }


# --- PRODUCT CONFIGURATION ---
class ProductConfigurationSerializer(serializers.ModelSerializer):
    # For displaying names
    cpu_name = serializers.ReadOnlyField(source='cpu.name')
    ram_name = serializers.ReadOnlyField(source='ram.name')
    hdd_name = serializers.ReadOnlyField(source='hdd.name')
    graphics_name = serializers.ReadOnlyField(source='graphics.name')
    display_name = serializers.ReadOnlyField(source='display_size.name')

    class Meta:
        model = ProductConfiguration
        fields = '__all__'
        extra_kwargs = {
            'cpu': {'write_only': True},
            'ram': {'write_only': True},
            'hdd': {'write_only': True},
            'graphics': {'write_only': True},
            'display_size': {'write_only': True},
            'asset': {'read_only': True} # Usually linked automatically in views
        }


# --- REPAIR ---
class RepairSerializer(serializers.ModelSerializer):
    product_display = serializers.ReadOnlyField(source='product.asset_id')

    class Meta:
        model = Repair
        fields = '__all__'
        read_only_fields = ['edited_by', 'edited_at']


# ===================================================================
# 3. PENDING SERIALIZERS (For Approval Dashboard)
# ===================================================================
# These are critical for your mobile "Approve/Reject" feature.

class PendingProductSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.ReadOnlyField(source='submitted_by.username')
    type_of_asset_name = serializers.ReadOnlyField(source='type_of_asset.name')

    class Meta:
        model = PendingProduct
        fields = '__all__'

class PendingRentalSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.ReadOnlyField(source='submitted_by.username')
    customer_name = serializers.ReadOnlyField(source='customer.name')
    asset_name = serializers.ReadOnlyField(source='asset.asset_id')

    class Meta:
        model = PendingRental
        fields = '__all__'

class PendingCustomerSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.ReadOnlyField(source='submitted_by.username')

    class Meta:
        model = PendingCustomer
        fields = '__all__'

class PendingRepairSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.ReadOnlyField(source='submitted_by.username')
    product_name = serializers.ReadOnlyField(source='product.asset_id')

    class Meta:
        model = PendingRepair
        fields = '__all__'

class PendingConfigSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.ReadOnlyField(source='submitted_by.username')
    asset_name = serializers.ReadOnlyField(source='asset.asset_id')

    class Meta:
        model = PendingProductConfiguration
        fields = '__all__'