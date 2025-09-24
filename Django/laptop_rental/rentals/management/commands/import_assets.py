import pandas as pd
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rentals.models import ProductAsset, AssetType, Supplier
from django.utils.dateparse import parse_date
from datetime import datetime, date
import uuid  # for generating unique serial numbers


class Command(BaseCommand):
    help = "Import asset data from Excel into ProductAsset table"

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Excel file')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        self.stdout.write(self.style.NOTICE(f"Reading Excel file: {file_path}"))

        # === Load Excel ===
        df = pd.read_excel(file_path)

        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Remove completely empty rows first
        df = df.dropna(how='all')
        
        # Now fill remaining NaN values with empty string
        df = df.fillna("")

        # Show preview for debugging
        self.stdout.write(self.style.NOTICE(f"Columns found: {list(df.columns)}"))
        self.stdout.write(self.style.NOTICE(f"Total rows after removing empty rows: {len(df)}"))
        self.stdout.write(self.style.NOTICE(f"Preview:\n{df.head()}"))

        # === Process Each Row ===
        processed_count = 0
        skipped_count = 0
        
        for index, row in df.iterrows():
            # --------- Early validation: Check if row has essential data ----------
            asset_id_val = str(row.get('Asset ID Tag', "")).strip()
            asset_type_val = str(row.get('Asset Type', "")).strip()
            
            # Skip if both Asset ID and Asset Type are empty (likely an empty row)
            if not asset_id_val and not asset_type_val:
                self.stdout.write(self.style.WARNING(f"[Row {index + 1}] Empty row detected, skipping."))
                skipped_count += 1
                continue
                
            # Skip if Asset ID is empty (required field)
            if not asset_id_val:
                self.stdout.write(self.style.WARNING(f"[Row {index + 1}] Missing Asset ID, skipping row."))
                skipped_count += 1
                continue
                
            # Check for duplicate Asset ID early
            if ProductAsset.objects.filter(asset_id=asset_id_val).exists():
                self.stdout.write(self.style.WARNING(
                    f"[Row {index + 1}] Asset ID {asset_id_val} already exists, skipping."
                ))
                skipped_count += 1
                continue

            # --------- Handle Asset Type (Required) ----------
            asset_type = None
            if asset_type_val:
                asset_type, _ = AssetType.objects.get_or_create(name=asset_type_val)
            else:
                self.stdout.write(self.style.WARNING(f"[Row {index + 1}] Missing Asset Type, skipping row."))
                skipped_count += 1
                continue

            # --------- Handle Edited By (User FK) ----------
            edited_by = None
            edited_by_val = str(row.get('Edited By', "")).strip()
            if edited_by_val:
                edited_by, _ = User.objects.get_or_create(username=edited_by_val)

            # --------- Handle Supplier (Purchased From FK) ----------
            purchased_from = None
            purchased_from_val = str(row.get('Purchased From', "")).strip()
            if purchased_from_val:
                purchased_from, _ = Supplier.objects.get_or_create(name=purchased_from_val)

            # --------- Handle Purchase Date ----------
            purchase_date_val = row.get('Purchase Date', None)
            purchase_date = None

            if (
                purchase_date_val is None
                or str(purchase_date_val).strip().lower() in ["", "unknown", "nan"]
            ):
                purchase_date = date(2006, 5, 18)
            elif isinstance(purchase_date_val, pd.Timestamp):
                purchase_date = purchase_date_val.date()
            elif isinstance(purchase_date_val, date):
                purchase_date = purchase_date_val
            else:
                try:
                    purchase_date = datetime.strptime(str(purchase_date_val).strip(), "%d-%m-%Y").date()
                except (ValueError, TypeError):
                    purchase_date = parse_date(str(purchase_date_val).strip())
                    if purchase_date is None:
                        purchase_date = date(2025, 5, 18)

            # --------- Handle Numeric Fields ----------
            def parse_float(value):
                try:
                    if pd.isna(value):
                        return 0.0
                    value_str = str(value).strip()
                    if value_str == "" or value_str.lower() == "nan":
                        return 0.0
                    return float(value_str)
                except (ValueError, TypeError):
                    return 0.0

            purchase_price = parse_float(row.get('Our Purchase Cost', 0.0))
            current_value = parse_float(row.get('Current Value', 0.0))

            # --------- Handle Serial No ----------
            serial_no_val = str(row.get('Serial No', "")).strip()
            if not serial_no_val or serial_no_val.lower() == "nan":
                serial_no_val = f"NA"

            # --------- Handle Company (Brand) ----------
            company_val = str(row.get('Company', "")).strip()
            if not company_val or company_val.lower() == "nan":
                company_val = "Default Brand"

            # --------- Create ProductAsset ----------
            try:
                product = ProductAsset.objects.create(
                    asset_id=asset_id_val,
                    type_of_asset=asset_type,
                    brand=company_val,
                    model_no=str(row.get('Model No.', "")).strip(),
                    serial_no=serial_no_val,
                    purchase_date=purchase_date,
                    purchase_price=purchase_price,
                    current_value=current_value,
                    purchased_from=purchased_from,
                    edited_by=edited_by,
                )
                
                processed_count += 1
                self.stdout.write(self.style.SUCCESS(f"[Row {index + 1}] Added new asset: {product.asset_id}"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[Row {index + 1}] Error creating asset: {str(e)}"))
                skipped_count += 1

        # --------- Final Summary ----------
        self.stdout.write(self.style.SUCCESS(f"✅ Import completed!"))
        self.stdout.write(self.style.SUCCESS(f"📊 Processed: {processed_count} assets"))
        self.stdout.write(self.style.WARNING(f"⚠️  Skipped: {skipped_count} rows"))