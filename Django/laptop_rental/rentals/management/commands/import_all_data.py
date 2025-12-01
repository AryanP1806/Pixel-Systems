import os
import pandas as pd
from datetime import datetime, date
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from rentals.models import (
    Customer, PendingCustomer, Supplier, AssetType,
    ProductAsset, PendingProduct, ProductConfiguration, PendingProductConfiguration,
    Rental, PendingRental, Repair, PendingRepair,
    CPUOption, RAMOption, HDDOption, GraphicsOption, DisplaySizeOption
)

User = get_user_model()

# python manage.py import_all_data "data/my_asset_data.xlsx"


# ------------------------------
# Helpers
# ------------------------------
def try_get(row, *keys):
    """Try several keys and return first non-empty value."""
    for k in keys:
        if k is None:
            continue
        if k in row:
            v = row.get(k)
            # pandas NaN -> treat as missing
            if pd.isna(v):
                continue
            s = str(v).strip()
            if s == "":
                continue
            return v
    return None

def parse_date(raw):
    """Return date object or None. Accepts date, datetime, or many string formats."""
    if raw is None:
        return None
    if isinstance(raw, date) and not isinstance(raw, datetime):
        return raw
    if isinstance(raw, datetime):
        return raw.date()
    s = str(raw).strip()
    if not s or s.lower() in ("nan", "nat", "none"):
        return None
    # try several formats
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    # try pandas parsing
    try:
        parsed = pd.to_datetime(s, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.date()
    except Exception:
        return None

def parse_datetime(raw):
    """Return datetime or None."""
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw
    s = str(raw).strip()
    if not s or s.lower() in ("nan", "nat", "none"):
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d-%m-%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    try:
        parsed = pd.to_datetime(s, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.to_pydatetime()
    except Exception:
        return None

def parse_decimal(raw):
    if raw is None:
        return None
    try:
        return float(raw)
    except Exception:
        return None

def get_user_by_username(username):
    """
    Find user by username. If not found, create a new active user 
    with a default password.
    """
    if not username:
        return None
    username = str(username).strip()
    
    # UPDATED LOGIC HERE:
    user, created = User.objects.get_or_create(username=username)
    if created:
        # Set a default password for imported users
        # They should change this immediately
        user.set_password('12345678') 
        user.save()
        print(f"   > [INFO] Created new user: {username}")
        
    return user

def create_or_update_option(model, name, order=None):
    """Create or update option (CPU/RAM/HDD/Graphics/Display) and set order if provided."""
    if not name:
        return None
    name = str(name).strip()
    obj, created = model.objects.get_or_create(name=name)
    if order is not None:
        try:
            obj.order = int(order)
            obj.save()
        except Exception:
            # ignore bad order
            pass
    return obj

def get_or_create_asset_type(name, display_order=None):
    if not name:
        return None
    name = str(name).strip()
    obj, created = AssetType.objects.get_or_create(name=name)
    if display_order is not None:
        try:
            obj.display_order = int(display_order)
            obj.save()
        except Exception:
            pass
    return obj

def get_or_create_supplier_from_row(row):
    """Try multiple supplier fields and create supplier if not exists."""
    name = try_get(row, 'purchased_from', 'purchased_from__name', 'supplier', 'supplier_name', 'purchased_from_name')
    if not name:
        return None
    name = str(name).strip()
    defaults = {}
    # map common supplier columns
    defaults['gstin'] = try_get(row, 'gstin', 'gstin_number', 'gst_number')
    defaults['address_primary'] = try_get(row, 'address_primary', 'address')
    defaults['address_secondary'] = try_get(row, 'address_secondary')
    defaults['phone_primary'] = try_get(row, 'phone_primary', 'phone', 'contact_number')
    defaults['phone_secondary'] = try_get(row, 'phone_secondary')
    defaults['email'] = try_get(row, 'email')
    defaults['reference_name'] = try_get(row, 'reference_name')
    supplier, _ = Supplier.objects.get_or_create(name=name, defaults={k:v for k,v in defaults.items() if v is not None})
    return supplier

# ------------------------------
# Command
# ------------------------------
class Command(BaseCommand):
    help = "Import full report Excel/CSV into live + pending models. Handles options, edited_by, edited_at, orders."

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to Excel (.xlsx) or CSV file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        if not os.path.exists(file_path):
            raise CommandError(f"❌ File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext in ('.xlsx', '.xls'):
                all_sheets = pd.read_excel(file_path, sheet_name=None)
            elif ext == '.csv':
                # assume Products if single CSV
                all_sheets = {'Products': pd.read_csv(file_path)}
            else:
                raise CommandError("Unsupported file type. Use .xlsx or .csv")
        except Exception as e:
            raise CommandError(f"Error reading file: {e}")

        summary = {}

        # ------------------ AssetTypes and Option tables ------------------
        # AssetTypes
        if 'AssetTypes' in all_sheets:
            df = all_sheets['AssetTypes'].fillna("")
            cnt = 0
            for _, row in df.iterrows():
                name = try_get(row, 'name', 'type_of_asset', 'Type of Asset')
                display_order = try_get(row, 'display_order', 'order')
                if name:
                    get_or_create_asset_type(name, display_order)
                    cnt += 1
            summary['AssetTypes'] = cnt

        # CPUOptions, RAMOptions, HDDOptions, GraphicsOptions, DisplaySizeOptions
        option_mapping = [
            ('CPUOptions', CPUOption),
            ('RAMOptions', RAMOption),
            ('HDDOptions', HDDOption),
            ('GraphicsOptions', GraphicsOption),
            ('DisplaySizeOptions', DisplaySizeOption),
        ]
        for sheet_name, model in option_mapping:
            if sheet_name in all_sheets:
                df = all_sheets[sheet_name].fillna("")
                cnt = 0
                for _, row in df.iterrows():
                    name = try_get(row, 'name')
                    order = try_get(row, 'order', 'display_order')
                    if name:
                        create_or_update_option(model, name, order)
                        cnt += 1
                summary[sheet_name] = cnt

        # ------------------ Suppliers ------------------
        if 'Suppliers' in all_sheets:
            df = all_sheets['Suppliers'].fillna("")
            cnt = 0
            for _, row in df.iterrows():
                name = try_get(row, 'name', 'supplier', 'supplier_name')
                if not name:
                    continue
                defaults = {
                    'gstin': try_get(row, 'gstin', 'gst_number', 'gstin_number'),
                    'address_primary': try_get(row, 'address_primary', 'address'),
                    'address_secondary': try_get(row, 'address_secondary'),
                    'phone_primary': try_get(row, 'phone_primary', 'phone', 'contact_number'),
                    'phone_secondary': try_get(row, 'phone_secondary'),
                    'email': try_get(row, 'email'),
                    'reference_name': try_get(row, 'reference_name'),
                }
                # prune Nones
                defaults = {k:v for k,v in defaults.items() if v is not None}
                Supplier.objects.update_or_create(name=str(name).strip(), defaults=defaults)
                cnt += 1
            summary['Suppliers'] = cnt

        # ------------------ Customers ------------------
        if 'Customers' in all_sheets:
            df = all_sheets['Customers'].fillna("")
            cnt = 0
            for _, row in df.iterrows():
                name = try_get(row, 'name', 'customer', 'customer_name')
                if not name:
                    continue
                defaults = {
                    'email': try_get(row, 'email'),
                    'phone_number_primary': try_get(row, 'phone_number_primary','phone','phone_primary'),
                    'phone_number_secondary': try_get(row, 'phone_number_secondary'),
                    'address_primary': try_get(row, 'address_primary','address'),
                    'address_secondary': try_get(row, 'address_secondary'),
                    'is_permanent': bool(try_get(row, 'is_permanent') or False),
                    'is_bni_member': bool(try_get(row, 'is_bni_member') or False),
                    'reference_name': try_get(row, 'reference_name'),
                }
                # handle edited_by/edited_at
                edited_by_username = try_get(row, 'edited_by', 'edited_by__username', 'edited_by_username')
                if edited_by_username:
                    u = get_user_by_username(edited_by_username)
                    if u:
                        defaults['edited_by'] = u
                edited_at_val = try_get(row, 'edited_at', 'edited_at__date', 'edited_at_datetime')
                parsed_edited_at = parse_datetime(edited_at_val) or parse_date(edited_at_val)
                if parsed_edited_at:
                    # if time present, keep datetime, else make datetime at midnight
                    if isinstance(parsed_edited_at, datetime):
                        defaults['edited_at'] = parsed_edited_at
                    else:
                        defaults['edited_at'] = datetime.combine(parsed_edited_at, datetime.min.time())

                Customer.objects.update_or_create(name=str(name).strip(),
                                                  defaults={k:v for k,v in defaults.items() if v is not None})
                cnt += 1
            summary['Customers'] = cnt

        # ------------------ Products (live) ------------------
        if 'Products' in all_sheets:
            df = all_sheets['Products'].fillna("")
            cnt = 0
            for _, row in df.iterrows():
                asset_id = try_get(row, 'asset_id', 'Asset ID', 'asset')
                if not asset_id:
                    continue

                # lookups
                at_name = try_get(row, 'type_of_asset', 'type_of_asset__name', 'Type of Asset')
                asset_type = get_or_create_asset_type(at_name, try_get(row, 'type_display_order', 'type_display_order'))

                supplier = get_or_create_supplier_from_row(row)

                purchase_date = parse_date(try_get(row, 'purchase_date', 'purchase_date__date', 'Purchase Date'))
                purchase_price = parse_decimal(try_get(row, 'purchase_price', 'purchase_price__value'))
                current_value = parse_decimal(try_get(row, 'current_value'))

                # warranty fields
                under_warranty = bool(try_get(row, 'under_warranty') or False)
                warranty_months = try_get(row, 'warranty_duration_months','warranty_months') or 0

                # edited_by/edited_at
                edited_by_username = try_get(row, 'edited_by', 'edited_by__username', 'edited_by_username')
                edited_by_user = get_user_by_username(edited_by_username) if edited_by_username else None
                edited_at_raw = try_get(row, 'edited_at', 'edited_at__date', 'edited_at_datetime')
                edited_at_dt = parse_datetime(edited_at_raw) or (parse_date(edited_at_raw) and datetime.combine(parse_date(edited_at_raw), datetime.min.time()))
                # model defaults
                defaults = {
                    'type_of_asset': asset_type,
                    'brand': try_get(row, 'brand'),
                    'model_no': try_get(row, 'model_no'),
                    'serial_no': try_get(row, 'serial_no'),
                    'asset_number': try_get(row, 'asset_number'),
                    'asset_suffix': try_get(row, 'asset_suffix'),
                    'purchase_date': purchase_date,
                    'purchase_price': purchase_price,
                    'current_value': current_value,
                    'purchased_from': supplier,
                    'under_warranty': under_warranty,
                    'warranty_duration_months': warranty_months,
                    'condition_status': try_get(row, 'condition_status'),
                    'sold_to': try_get(row, 'sold_to'),
                    'sale_price': parse_decimal(try_get(row, 'sale_price')),
                    'sale_date': parse_date(try_get(row, 'sale_date')),
                    'date_marked_dead': parse_date(try_get(row, 'date_marked_dead')),
                    'damage_narration': try_get(row, 'damage_narration'),
                }
                if edited_by_user:
                    defaults['edited_by'] = edited_by_user
                if edited_at_dt:
                    defaults['edited_at'] = edited_at_dt

                # Remove None values from defaults (so update_or_create won't try to set them to None)
                defaults = {k:v for k,v in defaults.items() if v is not None}

                try:
                    ProductAsset.objects.update_or_create(asset_id=str(asset_id).strip(), defaults=defaults)
                    cnt += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Skipping Product {asset_id}: {e}"))
            summary['Products'] = cnt

        # ------------------ Pending Products ------------------
        if 'Pending_Products' in all_sheets:
            df = all_sheets['Pending_Products'].fillna("")
            cnt = 0
            for _, row in df.iterrows():
                # Create PendingProduct rows
                asset_id = try_get(row, 'asset_id', 'Asset ID', 'asset')
                at_name = try_get(row, 'type_of_asset', 'type_of_asset__name', 'Type of Asset')
                asset_type = get_or_create_asset_type(at_name)
                supplier = get_or_create_supplier_from_row(row)
                purchase_date = parse_date(try_get(row, 'purchase_date'))
                defaults = {
                    'type_of_asset': asset_type,
                    'brand': try_get(row, 'brand'),
                    'model_no': try_get(row, 'model_no'),
                    'serial_no': try_get(row, 'serial_no'),
                    'purchase_price': parse_decimal(try_get(row, 'purchase_price')),
                    'current_value': parse_decimal(try_get(row, 'current_value')),
                    'purchase_date': purchase_date,
                    'under_warranty': bool(try_get(row, 'under_warranty') or False),
                    'warranty_duration_months': try_get(row, 'warranty_duration_months') or 0,
                    'purchased_from': supplier,
                    'condition_status': try_get(row, 'condition_status') or 'working',
                    'asset_number': try_get(row, 'asset_number'),
                    'asset_id': asset_id,
                    'sold_to': try_get(row, 'sold_to'),
                    'sale_price': parse_decimal(try_get(row, 'sale_price')),
                    'sale_date': parse_date(try_get(row, 'sale_date')),
                    'date_marked_dead': parse_date(try_get(row, 'date_marked_dead')),
                    'damage_narration': try_get(row, 'damage_narration'),
                }
                submitted_by_user = get_user_by_username(try_get(row, 'submitted_by', 'submitted_by__username', 'submitted_by_username'))
                if submitted_by_user:
                    defaults['submitted_by'] = submitted_by_user
                # Clean defaults
                defaults = {k:v for k,v in defaults.items() if v is not None}
                try:
                    PendingProduct.objects.create(**defaults)
                    cnt += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Skipping PendingProduct row {asset_id}: {e}"))
            summary['Pending_Products'] = cnt

        # ------------------ Configurations (live) ------------------
        if 'Configurations' in all_sheets:
            df = all_sheets['Configurations'].fillna("")
            cnt = 0
            for _, row in df.iterrows():
                asset_id = try_get(row, 'asset_id', 'asset__asset_id', 'Asset ID', 'asset')
                if not asset_id:
                    continue
                asset = ProductAsset.objects.filter(asset_id=str(asset_id).strip()).first()
                if not asset:
                    self.stdout.write(self.style.WARNING(f"Skipping configuration: asset {asset_id} not found"))
                    continue

                cpu_obj = create_or_update_option(CPUOption, try_get(row, 'cpu'), try_get(row, 'cpu_order', 'order'))
                ram_obj = create_or_update_option(RAMOption, try_get(row, 'ram'), try_get(row, 'ram_order'))
                hdd_obj = create_or_update_option(HDDOption, try_get(row, 'hdd'), try_get(row, 'hdd_order'))
                gfx_obj = create_or_update_option(GraphicsOption, try_get(row, 'graphics'), try_get(row, 'graphics_order'))
                dsp_obj = create_or_update_option(DisplaySizeOption, try_get(row, 'display_size'), try_get(row, 'display_size_order'))

                date_of_config = parse_date(try_get(row, 'date_of_config', 'date'))
                cost = parse_decimal(try_get(row, 'cost'))
                detailed_config = try_get(row, 'detailed_config', 'detailed_config_description', 'detailed_config_text')

                edited_by_user = get_user_by_username(try_get(row, 'edited_by', 'edited_by__username'))

                edited_at_raw = try_get(row, 'edited_at', 'edited_at__datetime', 'edited_at_datetime')
                edited_at_dt = parse_datetime(edited_at_raw) or (parse_date(edited_at_raw) and datetime.combine(parse_date(edited_at_raw), datetime.min.time()))

                try:
                    ProductConfiguration.objects.create(
                        asset=asset,
                        date_of_config=date_of_config or timezone.now().date(),
                        cpu=cpu_obj,
                        ram=ram_obj,
                        hdd=hdd_obj,
                        ssd=try_get(row, 'ssd'),
                        graphics=gfx_obj,
                        display_size=dsp_obj,
                        power_supply=try_get(row, 'power_supply'),
                        detailed_config=detailed_config,
                        cost=cost or 0,
                        edited_by=edited_by_user,
                        edited_at=edited_at_dt if edited_at_dt else None
                    )
                    cnt += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Skipping configuration row for {asset_id}: {e}"))
            summary['Configurations'] = cnt

        # ------------------ Pending Configurations ------------------
        if 'Pending_Configurations' in all_sheets:
            df = all_sheets['Pending_Configurations'].fillna("")
            cnt = 0
            for _, row in df.iterrows():
                asset_id = try_get(row, 'asset_id', 'asset__asset_id', 'Asset ID')
                asset = ProductAsset.objects.filter(asset_id=str(asset_id).strip()).first() if asset_id else None
                if not asset:
                    self.stdout.write(self.style.WARNING(f"Skipping pending config: asset {asset_id} not found"))
                    continue

                cpu_obj = create_or_update_option(CPUOption, try_get(row, 'cpu'), try_get(row, 'cpu_order', 'order'))
                ram_obj = create_or_update_option(RAMOption, try_get(row, 'ram'), try_get(row, 'ram_order'))
                hdd_obj = create_or_update_option(HDDOption, try_get(row, 'hdd'), try_get(row, 'hdd_order'))
                gfx_obj = create_or_update_option(GraphicsOption, try_get(row, 'graphics'), try_get(row, 'graphics_order'))
                dsp_obj = create_or_update_option(DisplaySizeOption, try_get(row, 'display_size'), try_get(row, 'display_size_order'))

                date_of_config = parse_date(try_get(row, 'date_of_config', 'date'))
                cost = parse_decimal(try_get(row, 'cost'))

                submitted_by_user = get_user_by_username(try_get(row, 'submitted_by', 'submitted_by__username'))

                try:
                    PendingProductConfiguration.objects.create(
                        asset=asset,
                        date_of_config=date_of_config or timezone.now().date(),
                        cpu=cpu_obj,
                        ram=ram_obj,
                        hdd=hdd_obj,
                        ssd=try_get(row, 'ssd'),
                        graphics=gfx_obj,
                        display_size=dsp_obj,
                        power_supply=try_get(row, 'power_supply'),
                        detailed_config=try_get(row, 'detailed_config'),
                        cost=cost or 0,
                        submitted_by=submitted_by_user
                    )
                    cnt += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Skipping pending config row for {asset_id}: {e}"))
            summary['Pending_Configurations'] = cnt

        # ------------------ Rentals (live) ------------------
        if 'Rentals' in all_sheets:
            df = all_sheets['Rentals'].fillna("")
            cnt = 0
            for _, row in df.iterrows():
                cust_name = try_get(row, 'customer', 'customer__name', 'Customer')
                asset_id = try_get(row, 'asset', 'asset__asset_id', 'Asset')
                if not cust_name or not asset_id:
                    continue
                customer = Customer.objects.filter(name=str(cust_name).strip()).first()
                asset = ProductAsset.objects.filter(asset_id=str(asset_id).strip()).first()
                if not customer or not asset:
                    self.stdout.write(self.style.WARNING(f"Skipping rental: missing customer or asset ({cust_name}|{asset_id})"))
                    continue

                start_date = parse_date(try_get(row, 'rental_start_date', 'rental_start_date__date'))
                end_date = parse_date(try_get(row, 'rental_end_date', 'rental_end_date__date'))
                payment_amount = parse_decimal(try_get(row, 'payment_amount'))
                billing_day = try_get(row, 'billing_day') or 1
                status = try_get(row, 'status') or 'ongoing'
                contract = try_get(row, 'contract_number') or try_get(row, 'contract', 'contract_no') or "N/A"

                edited_by_user = get_user_by_username(try_get(row, 'edited_by', 'edited_by__username'))
                edited_at_dt = parse_datetime(try_get(row, 'edited_at')) or (parse_date(try_get(row, 'edited_at')) and datetime.combine(parse_date(try_get(row, 'edited_at')), datetime.min.time()))

                defaults = {
                    'rental_start_date': start_date,
                    'rental_end_date': end_date,
                    'payment_amount': payment_amount or 0,
                    'billing_day': billing_day,
                    'status': status,
                    'contract_number': contract,
                }
                if edited_by_user:
                    defaults['edited_by'] = edited_by_user
                if edited_at_dt:
                    defaults['edited_at'] = edited_at_dt

                try:
                    Rental.objects.update_or_create(customer=customer, asset=asset, defaults={k:v for k,v in defaults.items() if v is not None})
                    cnt += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Skipping rental row: {e}"))
            summary['Rentals'] = cnt

        # ------------------ Pending Rentals ------------------
        if 'Pending_Rentals' in all_sheets or 'PendingRentals' in all_sheets:
            key = 'Pending_Rentals' if 'Pending_Rentals' in all_sheets else 'PendingRentals'
            df = all_sheets[key].fillna("")
            cnt = 0
            for _, row in df.iterrows():
                cust_name = try_get(row, 'customer', 'customer__name', 'Customer')
                asset_id = try_get(row, 'asset', 'asset__asset_id', 'Asset')
                if not cust_name or not asset_id:
                    continue
                customer = Customer.objects.filter(name=str(cust_name).strip()).first()
                asset = ProductAsset.objects.filter(asset_id=str(asset_id).strip()).first()
                if not customer or not asset:
                    self.stdout.write(self.style.WARNING(f"Skipping pending rental: missing customer or asset ({cust_name}|{asset_id})"))
                    continue

                start_date = parse_date(try_get(row, 'rental_start_date', 'rental_start_date__date'))
                end_date = parse_date(try_get(row, 'rental_end_date', 'rental_end_date__date'))
                payment_amount = parse_decimal(try_get(row, 'payment_amount'))
                billing_day = try_get(row, 'billing_day') or 1
                status = try_get(row, 'status') or 'ongoing'
                contract = try_get(row, 'contract_number') or try_get(row, 'contract') or "N/A"

                submitted_by_user = get_user_by_username(try_get(row, 'submitted_by', 'submitted_by__username'))
                defaults = {
                    'customer': customer,
                    'asset': asset,
                    'rental_start_date': start_date,
                    'rental_end_date': end_date,
                    'payment_amount': payment_amount or 0,
                    'billing_day': billing_day,
                    'status': status,
                    'contract_number': contract
                }
                try:
                    PendingRental.objects.create(**defaults, submitted_by=submitted_by_user)
                    cnt += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Skipping pending rental row: {e}"))
            summary['Pending_Rentals'] = cnt

        # ------------------ Repairs (live) ------------------
        if 'Repairs' in all_sheets:
            df = all_sheets['Repairs'].fillna("")
            cnt = 0
            for _, row in df.iterrows():
                asset_id = try_get(row, 'product__asset_id', 'asset_id', 'Asset ID', 'product')
                if not asset_id:
                    continue
                asset = ProductAsset.objects.filter(asset_id=str(asset_id).strip()).first()
                if not asset:
                    self.stdout.write(self.style.WARNING(f"Skipping repair for missing asset {asset_id}"))
                    continue
                name = try_get(row, 'name', 'Repair Name', 'name')
                repair_date = parse_date(try_get(row, 'date', 'repair_date'))
                cost = parse_decimal(try_get(row, 'cost'))
                info = try_get(row, 'info')
                repair_warranty_months = try_get(row, 'repair_warranty_months') or try_get(row, 'repair_warranty', 'repair_warranty_months') or 0

                edited_by_user = get_user_by_username(try_get(row, 'edited_by', 'edited_by__username'))
                edited_at_dt = parse_datetime(try_get(row, 'edited_at')) or (parse_date(try_get(row, 'edited_at')) and datetime.combine(parse_date(try_get(row, 'edited_at')), datetime.min.time()))

                defaults = {
                    'date': repair_date or timezone.now().date(),
                    'cost': cost or 0,
                    'info': info,
                    'repair_warranty_months': repair_warranty_months,
                }
                if edited_by_user:
                    defaults['edited_by'] = edited_by_user
                if edited_at_dt:
                    defaults['edited_at'] = edited_at_dt

                try:
                    Repair.objects.update_or_create(product=asset, name=name, defaults={k:v for k,v in defaults.items() if v is not None})
                    cnt += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Skipping repair row for {asset_id}: {e}"))
            summary['Repairs'] = cnt

        # ------------------ Pending Repairs ------------------
        if 'Pending_Repairs' in all_sheets:
            df = all_sheets['Pending_Repairs'].fillna("")
            cnt = 0
            for _, row in df.iterrows():
                asset_id = try_get(row, 'product__asset_id', 'asset_id', 'Asset ID', 'product')
                asset = ProductAsset.objects.filter(asset_id=str(asset_id).strip()).first() if asset_id else None
                if not asset:
                    self.stdout.write(self.style.WARNING(f"Skipping pending repair for missing asset {asset_id}"))
                    continue
                name = try_get(row, 'name', 'Repair Name', 'name')
                repair_date = parse_date(try_get(row, 'date'))
                cost = parse_decimal(try_get(row, 'cost'))
                info = try_get(row, 'info')
                submitted_by_user = get_user_by_username(try_get(row, 'submitted_by', 'submitted_by__username'))

                try:
                    PendingRepair.objects.create(
                        original_repair=None,
                        product=asset,
                        date=repair_date,
                        cost=cost,
                        name=name,
                        info=info,
                        repair_warranty_months=try_get(row, 'repair_warranty_months') or 0,
                        submitted_by=submitted_by_user
                    )
                    cnt += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Skipping pending repair row for {asset_id}: {e}"))
            summary['Pending_Repairs'] = cnt

        # ------------------ Finished ------------------
        self.stdout.write(self.style.SUCCESS("✅ Import Summary"))
        for k,v in summary.items():
            self.stdout.write(self.style.SUCCESS(f"  {k}: {v} records imported"))
