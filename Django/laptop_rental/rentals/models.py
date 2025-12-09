from django.db import models
from django.utils.timezone import now
from django.utils import timezone
from datetime import timedelta, date
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

# -----------------------------
# Product 
# -----------------------------

class AssetType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    display_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['display_order', 'name']


class CPUOption(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name
    

class HDDOption(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

class RAMOption(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

class DisplaySizeOption(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

class GraphicsOption(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name
# -----------------------------
# Product Model (Type)
# -----------------------------
class ProductAsset(models.Model):
    ASSET_TYPES = [
        ('Laptop', 'Laptop'),
        ('Monitor', 'Monitor'),
        ('Printer', 'Printer'),
        ('Adaptor', 'Adaptor'),
        ('Graphics', 'Graphics Card'),
        ('Desktop', 'Desktop'),
        ('Server', 'Server'),
        # Add more as needed
    ]
    CONDITION_CHOICES = [
        ('working', 'Working'),
        ('damaged', 'Damaged'),
        ('missing', 'Missing'),
        ('sold', 'Sold'),
    ]
    asset_number = models.PositiveIntegerField(help_text="Enter the asset id (e.g., 7 for 007)",null=True, blank=True)

    asset_id = models.CharField(max_length=50, blank=True, null=True)

    type_of_asset = models.ForeignKey(AssetType, on_delete=models.CASCADE)
    brand = models.CharField(max_length=100)
    model_no = models.CharField(max_length=100)
    serial_no = models.CharField(max_length=100,null=True,blank=True)
    # hsn_code = models.CharField(max_length=15, blank=True)
    asset_number = models.PositiveIntegerField(null=True, blank=True)
    asset_suffix = models.CharField(max_length=1, null=True, blank=True)  # optional
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Total accumulated revenue


    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_value = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateField()

    under_warranty = models.BooleanField(default=False)
    warranty_duration_months = models.PositiveIntegerField(null=True, blank=True, default=0)

    purchased_from = models.ForeignKey(
        'Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products_supplied'
    )
    condition_status = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='working'
    )
    sold_to = models.CharField(max_length=100, blank=True, null=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_date = models.DateField(null=True, blank=True)
    date_marked_dead = models.DateField(null=True, blank=True)
    damage_narration = models.TextField(blank=True, null=True)


    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    edited_at = models.DateTimeField(null=True, blank=True) 


    # Calculate warranty expiry date dynamically
    # @property
    # def warranty_expiry_date(self):
    #     """
    #     Warranty ends after purchase_date + warranty_duration_months
    #     """
    #     if self.purchase_date and self.warranty_duration_months > 0:
    #         return self.purchase_date + relativedelta(months=self.warranty_duration_months)
    #     return None
    # @property
    # def warranty_expiry_date(self):
    #     """
    #     Calculates the warranty expiry date based on purchase_date and warranty_duration_months.
    #     """
    #     if self.purchase_date and self.warranty_duration_months is not None and self.warranty_duration_months > 0:
    #         return self.purchase_date + relativedelta(months=self.warranty_duration_months)
    #     return None
    @property
    def warranty_expiry_date(self):
        """Return expiry date based on purchase_date and duration."""
        if not self.purchase_date:
            return None
        
        # Convert purchase_date if it's a string (from import)
        if isinstance(self.purchase_date, str):
            try:
                from datetime import datetime
                self.purchase_date = datetime.strptime(self.purchase_date, "%Y-%m-%d").date()
            except Exception:
                return None

        months = self.warranty_duration_months or 0
        return self.purchase_date + relativedelta(months=months)
    # Calculate remaining days until warranty ends
    @property
    def warranty_days_left(self):
        expiry = self.warranty_expiry_date
        if expiry:
            remaining_days = (expiry - timezone.now().date()).days
            return remaining_days if remaining_days > 0 else 0
        return 0

    # Determine warranty status
    @property
    def warranty_status(self):
        expiry = self.warranty_expiry_date
        warrenty = self.under_warranty

        if not warrenty:
            return "No Warranty"

        today = timezone.now().date()
        remaining_days = (expiry - today).days

        if remaining_days < 0:
            return "Expired"
        elif remaining_days <= 30:
            return "Expiring Soon"
        return "Active"
    

    def save(self, *args, **kwargs):
        # ... (keep your existing warranty logic here) ...
        if self._state.adding:
                if self.purchase_date and (self.warranty_duration_months or 0) > 0:
                    expiry = self.purchase_date + relativedelta(
                        months=int(self.warranty_duration_months or 0)
                    )
                    self.under_warranty = timezone.now().date() <= expiry
        # --- START: REPLACEMENT LOGIC FOR ASSET ID ---
        if not self.asset_id:
            year = self.purchase_date.year if self.purchase_date else timezone.now().year
            prefix = f"Pixel/{year}/"

            # ✅ CORRECT: Query BOTH tables for existing IDs
            existing_ids = list(ProductAsset.objects.filter(asset_id__startswith=prefix).values_list('asset_id', flat=True)) + \
                           list(PendingProduct.objects.filter(asset_id__startswith=prefix).values_list('asset_id', flat=True))

            # --- (The rest of the logic is for generating the next number) ---
            if self.asset_number:  # Use manually provided asset_number
                number_str = str(self.asset_number).zfill(3)
                suffix = f" {self.asset_suffix}" if self.asset_suffix else ""
                generated_id = f"{prefix}{number_str}{suffix}"

                if generated_id in existing_ids:
                    raise ValueError(f"Asset Number '{self.asset_number}' is already in use for year {year}.")

            else:  # Auto-generate the next available number
                used_numbers = set()
                for aid in existing_ids:
                    try:
                        # Extract the numeric part of the asset ID
                        num_part = aid.split('/')[-1].split()[0]
                        used_numbers.add(int(num_part))
                    except (ValueError, IndexError):
                        continue
                
                next_number = 1
                while next_number in used_numbers:
                    next_number += 1
                
                self.asset_number = next_number # Also set the asset_number field
                generated_id = f"{prefix}{str(next_number).zfill(3)}"

            self.asset_id = generated_id
        # --- END: REPLACEMENT LOGIC FOR ASSET ID ---

        # Final check against both tables is good practice
        # Exclude the pending being approved (if set) to avoid false positive during approval
        pending_pk_to_exclude = getattr(self, '_pending_pk', None)
        pending_conflict_qs = PendingProduct.objects.filter(asset_id=self.asset_id)
        if pending_pk_to_exclude:
            pending_conflict_qs = pending_conflict_qs.exclude(pk=pending_pk_to_exclude)

        if ProductAsset.objects.exclude(pk=self.pk).filter(asset_id=self.asset_id).exists() or pending_conflict_qs.exists():
            raise ValueError(f"Asset ID '{self.asset_id}' already exists. Please use a unique one.")

        if self.edited_by:
            self.edited_at = timezone.now()

        super().save(*args, **kwargs)

    # ... rest of your model ...



    def __str__(self):
        return f"{self.type_of_asset} | {self.brand} {self.model_no} [{self.asset_id}]"
    
    @property
    def is_available(self):
        """
        An asset is available if:
        1. It is marked as 'working'.
        2. It has NO ongoing rentals.
        3. It has NO pending rentals awaiting approval.
        """
        has_ongoing_rental = self.rentals.filter(status='ongoing').exists()
        has_pending_rental = PendingRental.objects.filter(asset=self).exists()
        
        return self.condition_status == 'working' and not has_ongoing_rental and not has_pending_rental

    # @property
    # def total_rent_earned(self):
    #     return sum(r.payment.amount for r in self.rentals.all() if r.payment)


    @property
    def total_rent_earned(self):
       return sum(r.payment.amount for r in self.rentals.all() if r.payment)

    @property
    def total_repairs(self):
        return sum(repair.cost for repair in self.repairs.all())
    
    # @property
    # def net_profit(self):
        
    #     base_profit = self.total_rent_earned - self.total_repairs
    #     if self.is_sold and self.sale_price:
    #         base_profit += self.sale_price
    #     return base_profit







class PendingProduct(models.Model):
    CONDITION_CHOICES = [
        ('working', 'Working'),
        ('damaged', 'Damaged'),
        ('missing', 'Missing'),
        ('sold', 'Sold'),
    ]
    original_product = models.ForeignKey(ProductAsset, null=True, blank=True, on_delete=models.SET_NULL)
    pending_type = models.CharField(max_length=10, choices=[('add', 'Add'), ('edit', 'Edit')], default='add')
    
    asset_suffix = models.CharField(max_length=1, null=True, blank=True)
    type_of_asset = models.ForeignKey(AssetType, on_delete=models.CASCADE)
    brand = models.CharField(max_length=100)
    model_no = models.CharField(max_length=100)
    serial_no = models.CharField(max_length=100,null=True,blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_value = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateField()
    under_warranty = models.BooleanField(default=False)
    warranty_duration_months = models.PositiveIntegerField(null=True, blank=True)
    purchased_from = models.ForeignKey('Supplier', on_delete=models.SET_NULL, null=True, blank=True)
    condition_status = models.CharField(max_length=20, choices=CONDITION_CHOICES)  # same choices
    # hsn_code = models.CharField(max_length=15, blank=True, null=True)
    asset_number = models.PositiveIntegerField(null=True, blank=True)
    asset_id = models.CharField(max_length=50, blank=True, null=True)
    sold_to = models.CharField(max_length=255, blank=True, null=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_date = models.DateField(null=True, blank=True)
    date_marked_dead = models.DateField(null=True, blank=True)
    damage_narration = models.TextField(blank=True, null=True)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.asset_id:
            year = self.purchase_date.year if self.purchase_date else timezone.now().year
            prefix = f"Pixel/{year}/"

            # ✅ CORRECT: Query BOTH tables
            existing_ids = list(ProductAsset.objects.filter(asset_id__startswith=prefix).values_list('asset_id', flat=True)) + \
                           list(PendingProduct.objects.filter(asset_id__startswith=prefix).exclude(pk=self.pk).values_list('asset_id', flat=True))

            if self.asset_number:
                number_str = str(self.asset_number).zfill(3)
                suffix = f" {self.asset_suffix}" if self.asset_suffix else ""
                generated_id = f"{prefix}{number_str}{suffix}"
                if generated_id in existing_ids:
                    raise ValueError(f"Asset Number '{self.asset_number}' is already in use for year {year}.")
            else:
                used_numbers = set()
                for aid in existing_ids:
                    try:
                        num_part = aid.split('/')[-1].split()[0]
                        used_numbers.add(int(num_part))
                    except (ValueError, IndexError):
                        continue
                
                next_number = 1
                while next_number in used_numbers:
                    next_number += 1
                
                self.asset_number = next_number
                generated_id = f"{prefix}{str(next_number).zfill(3)}"

            self.asset_id = generated_id

        super().save(*args, **kwargs)
    # ... rest of your model ...


    def get_next_available_number(self, year):
        prefix = f"Pixel/{year}/"
        existing_ids = list(ProductAsset.objects.filter(asset_id__startswith=prefix).values_list('asset_id', flat=True)) + \
                    list(PendingProduct.objects.filter(asset_id__startswith=prefix).values_list('asset_id', flat=True))

        used_numbers = set()
        for aid in existing_ids:
            try:
                num_part = aid.replace(prefix, '').split()[0]
                used_numbers.add(int(num_part))
            except:
                pass

        for i in range(1, 1000):
            if i not in used_numbers:
                return f"{i:03d}"
        return "999"



# -----------------------------
# Product Unit (Individual Laptop)
# -----------------------------
class ProductConfiguration(models.Model):
    asset = models.ForeignKey(ProductAsset, on_delete=models.CASCADE, related_name='configurations')
    date_of_config = models.DateField()

    cpu = models.ForeignKey(CPUOption, on_delete=models.SET_NULL, null=True, blank=True)
    ram = models.ForeignKey(RAMOption, on_delete=models.SET_NULL, null=True, blank=True)
    hdd = models.ForeignKey(HDDOption, on_delete=models.SET_NULL, null=True, blank=True)
    ssd = models.CharField(max_length=50, blank=True, null=True)
    graphics = models.ForeignKey(GraphicsOption, on_delete=models.SET_NULL, null=True, blank=True)
    display_size = models.ForeignKey(DisplaySizeOption, on_delete=models.SET_NULL, null=True, blank=True)
    power_supply = models.CharField(max_length=100, blank=True, null=True)
    detailed_config = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    edited_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.edited_by:
            self.edited_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Config on {self.date_of_config} for {self.asset}"




# -----------------------------
# Customer
# -----------------------------
class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone_number_primary = models.CharField(max_length=15)
    phone_number_secondary = models.CharField(max_length=15, blank=True, null=True)

    address_primary = models.TextField()
    address_secondary = models.TextField(blank=True, null=True)

    is_permanent = models.BooleanField(default=False)
    is_bni_member = models.BooleanField(default=False)

    reference_name = models.CharField(max_length=100, blank=True, null=True)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    edited_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'phone_number_primary'], name='unique_customer_by_name_and_phone'),
        ]
    def save(self, *args, **kwargs):
        if self.edited_by:
            self.edited_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    

class PendingCustomer(models.Model):
    original_customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)  # ✅ Add this
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone_number_primary = models.CharField(max_length=15)
    phone_number_secondary = models.CharField(max_length=15, blank=True, null=True)
    address_primary = models.TextField()
    address_secondary = models.TextField(blank=True, null=True)
    is_permanent = models.BooleanField(default=False)
    is_bni_member = models.BooleanField(default=False)
    reference_name = models.CharField(max_length=100, blank=True, null=True)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

# -----------------------------
# Rental
# -----------------------------
class Rental(models.Model):
    STATUS_CHOICES = (
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    asset = models.ForeignKey(ProductAsset, on_delete=models.CASCADE, related_name='rentals',blank=True, null=True)
    rental_start_date = models.DateField()
    billing_day = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="Day of the month for billing"
    )
    rental_end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')
    contract_validity = models.DateField(blank=True, null=True)


    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    contract_number = models.CharField(max_length=50, blank=True)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    edited_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        if self.edited_by:
            self.edited_at = timezone.now()
        super().save(*args, **kwargs)

    def is_active(self):
        return self.status == 'active'
    
    def __str__(self):
        return f'''Rental of '{self.asset}' to "{self.customer}" starting from {self.rental_start_date}'''


class PendingRental(models.Model):
    original_rental = models.ForeignKey(Rental, null=True, blank=True, on_delete=models.SET_NULL)  # ✅ Add this
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    asset = models.ForeignKey(ProductAsset, on_delete=models.CASCADE, blank=True, null=True)
    rental_start_date = models.DateField()
    billing_day = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Day of the month for billing")
    rental_end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('ongoing', 'Ongoing'), ('completed', 'Completed')], default='ongoing')
    contract_validity = models.DateField(blank=True, null=True)

    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    contract_number = models.CharField(max_length=50, blank=True)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pending_rentals')
    submitted_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    def is_active(self):
        return self.status == 'active'

# -----------------------------
# Payment
# -----------------------------

class Repair(models.Model):
    product = models.ForeignKey(ProductAsset, on_delete=models.CASCADE, related_name='repairs')
    name = models.CharField(max_length=100)
    date = models.DateField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    info = models.TextField(blank=True, null=True)
    repair_warranty_months = models.PositiveIntegerField(null=True, blank=True, default=0)
    under_repair_warranty = models.BooleanField(default=False)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    edited_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.product.asset_id} Repair - {self.date}"

    # -------------------------
    # Warranty Logic
    # -------------------------
    @property
    def repair_warranty_expiry_date(self):
        """Calculate when the repair warranty expires."""
        if self.date and self.repair_warranty_months and self.repair_warranty_months > 0:
            return self.date + relativedelta(months=self.repair_warranty_months)
        return None

    @property
    def repair_warranty_days_left(self):
        """Calculate how many days are left until the repair warranty expires."""
        expiry = self.repair_warranty_expiry_date
        if expiry:
            remaining_days = (expiry - timezone.now().date()).days
            return remaining_days if remaining_days > 0 else 0
        return None

    @property
    def repair_warranty_status(self):
        """Return repair warranty status: Active, Expiring Soon, Expired, or No Warranty."""
        expiry = self.repair_warranty_expiry_date
        today = timezone.now().date()

        if not self.date or not self.repair_warranty_months or self.repair_warranty_months <= 0:
            return "No Warranty"

        if today > expiry:
            return "Expired"
        elif (expiry - today).days <= 30:
            return "Expiring Soon"
        else:
            return "Active"

    # models.py inside Repair class
    def save(self, *args, **kwargs):
        """Auto update the under_repair_warranty field when saving."""
        
        # Check if this is a new record or an update
        # Note: We usually check dates on every save, not just adding, 
        # just in case the date changed during an edit.
        
        if self.date and (self.repair_warranty_months or 0) > 0:
            expiry = self.date + relativedelta(
                months=int(self.repair_warranty_months or 0)
            )
            self.under_repair_warranty = timezone.now().date() <= expiry
        else:
            # If no date or no duration, it is not under warranty
            self.under_repair_warranty = False
            
        super().save(*args, **kwargs)

class PendingProductConfiguration(models.Model):
    asset = models.ForeignKey(ProductAsset, on_delete=models.CASCADE)
    date_of_config = models.DateField()
    
    cpu = models.ForeignKey(CPUOption, on_delete=models.SET_NULL, null=True, blank=True)
    ram = models.ForeignKey(RAMOption, on_delete=models.SET_NULL, null=True, blank=True)
    hdd = models.ForeignKey(HDDOption, on_delete=models.SET_NULL, null=True, blank=True)
    ssd = models.CharField(max_length=50, blank=True, null=True)
    graphics = models.ForeignKey(GraphicsOption, on_delete=models.SET_NULL, null=True, blank=True)
    display_size = models.ForeignKey(DisplaySizeOption, on_delete=models.SET_NULL, null=True, blank=True)
    power_supply = models.CharField(max_length=100, blank=True, null=True)
    detailed_config = models.TextField(blank=True, null=True)
    
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    is_edit = models.BooleanField(default=False)
    original_config = models.ForeignKey(ProductConfiguration, on_delete=models.SET_NULL, null=True, blank=True)






# models.py

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    gstin = models.CharField(max_length=20, verbose_name="GSTIN Number", blank=True, null=True)

    address_primary = models.TextField(blank=True, null=True)
    address_secondary = models.TextField(blank=True, null=True)

    phone_primary = models.CharField(max_length=15,blank=True, null=True)
    phone_secondary = models.CharField(max_length=15, blank=True, null=True)

    email = models.EmailField(blank=True, null=True)
    reference_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name
    

    

class PendingRepair(models.Model):
    original_repair = models.ForeignKey('Repair', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey('ProductAsset', on_delete=models.CASCADE)
    date = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    info = models.TextField(blank=True, null=True)
    repair_warranty_months = models.PositiveIntegerField(null=True, blank=True, default=0)
    under_repair_warranty = models.BooleanField(default=False)
    is_edit = models.BooleanField(default=False)  # True = edit or delete pending
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pending Repair for {self.product.asset_id}"
