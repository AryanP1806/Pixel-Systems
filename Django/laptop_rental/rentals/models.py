from django.db import models
from django.utils.timezone import now
from datetime import timedelta, date, timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

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
    serial_no = models.CharField(max_length=100, unique=True)
    hsn_code = models.CharField(max_length=15, blank=True)
    asset_number = models.PositiveIntegerField(null=True, blank=True)
    asset_suffix = models.CharField(max_length=1, null=True, blank=True)  # optional



    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_value = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateField()

    under_warranty = models.BooleanField(default=False)
    warranty_duration_months = models.PositiveIntegerField(null=True, blank=True)

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


    def save(self, *args, **kwargs):
        if not self.asset_id:
            year = self.purchase_date.year if self.purchase_date else now().year

            if self.asset_number:  # Asset number manually given
                number_str = str(self.asset_number).zfill(3)
                suffix = f" {self.asset_suffix}" if self.asset_suffix else ""
                generated_id = f"Pixel/{year}/{number_str}{suffix}"
            else:
                # Generate next available number automatically
                existing_ids = ProductAsset.objects.filter(purchase_date__year=year).values_list('asset_id', flat=True)

                used_numbers = set()
                for aid in existing_ids:
                    try:
                        parts = aid.split("/")[-1].split()
                        num = int(parts[0])
                        used_numbers.add(num)
                    except:
                        continue

                next_number = 1
                while next_number in used_numbers:
                    next_number += 1

                generated_id = f"Pixel/{year}/{str(next_number).zfill(3)}"

            # Check for duplication
            if ProductAsset.objects.exclude(pk=self.pk).filter(asset_id=generated_id).exists():
                raise ValueError(f"Asset ID '{generated_id}' already exists. Please use a unique one.")

            self.asset_id = generated_id

        else:
            # Asset ID manually entered → check uniqueness
            if ProductAsset.objects.exclude(pk=self.pk).filter(asset_id=self.asset_id).exists():
                raise ValueError(f"Asset ID '{self.asset_id}' already exists. Please use a unique one.")

        super().save(*args, **kwargs)



    def __str__(self):
        return f"{self.type_of_asset} | {self.brand} {self.model_no} [{self.asset_id}]"
    
    @property
    def is_available(self):
        # return (self.condition_status == 'working' and not self.rentals.filter(status__in=['ongoing', 'overdue']).exists())
        return (self.condition_status == 'working' and not self.rentals.filter(status__in=['ongoing']).exists())

    
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
    serial_no = models.CharField(max_length=100, unique=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_value = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateField()
    under_warranty = models.BooleanField(default=False)
    warranty_duration_months = models.PositiveIntegerField(null=True, blank=True)
    purchased_from = models.ForeignKey('Supplier', on_delete=models.SET_NULL, null=True, blank=True)
    condition_status = models.CharField(max_length=20, choices=CONDITION_CHOICES)  # same choices
    hsn_code = models.CharField(max_length=15, blank=True, null=True)
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
        # year = self.purchase_date.year if self.purchase_date else now().year
        # prefix = f"Pixel/{year}/"

        if not self.asset_id:
            year = self.purchase_date.year if self.purchase_date else now().year

            if self.asset_number:  # Asset number manually given
                number_str = str(self.asset_number).zfill(3)
                suffix = f" {self.asset_suffix}" if self.asset_suffix else ""
                generated_id = f"Pixel/{year}/{number_str}{suffix}"
            else:
                # Generate next available number automatically
                existing_ids = ProductAsset.objects.filter(purchase_date__year=year).values_list('asset_id', flat=True)

                used_numbers = set()
                for aid in existing_ids:
                    try:
                        parts = aid.split("/")[-1].split()
                        num = int(parts[0])
                        used_numbers.add(num)
                    except:
                        continue

                next_number = 1
                while next_number in used_numbers:
                    next_number += 1

                generated_id = f"Pixel/{year}/{str(next_number).zfill(3)}"

        # If full asset_id already provided, use it after validation
        
        # Check uniqueness across both ProductAsset and PendingProduct (except self)
        # if ProductAsset.objects.filter(asset_id=self.asset_id).exists() or \
        # PendingProduct.objects.filter(asset_id=self.asset_id).exclude(pk=self.pk).exists():
        #     raise ValidationError({'asset_id': 'Asset ID already exists. Please choose a unique one.'})

        super().save(*args, **kwargs)


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

    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

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

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'phone_number_primary'], name='unique_customer_by_name_and_phone'),
        ]

    def __str__(self):
        return self.name
    


class PendingCustomer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone_number_primary = models.CharField(max_length=15)
    phone_number_secondary = models.CharField(max_length=15, blank=True, null=True)
    address_primary = models.TextField()
    address_secondary = models.TextField(blank=True, null=True)
    is_permanent = models.BooleanField(default=False)
    is_bni_member = models.BooleanField(default=False)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    reference_name = models.CharField(max_length=100, blank=True, null=True)

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


    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    contract_number = models.CharField(max_length=50, blank=True)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)



class PendingRental(models.Model):
    STATUS_CHOICES = (
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    asset = models.ForeignKey(ProductAsset, on_delete=models.CASCADE,blank=True, null=True)
    rental_start_date = models.DateField()
    billing_day = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="Day of the month for billing"
    )
    rental_end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')


    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    contract_number = models.CharField(max_length=50, blank=True)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pending_rentals')
    submitted_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)


# -----------------------------
# Payment
# -----------------------------
class Payment(models.Model):
   
    
    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
    ]
    
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('unpaid', 'Unpaid'),
    ]

    rental = models.OneToOneField(Rental, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unpaid')
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Payment #{self.id} - {self.rental} - {self.amount}"

class Repair(models.Model):
    product = models.ForeignKey(ProductAsset, on_delete=models.CASCADE, related_name='repairs')
    name = models.CharField(max_length=100)
    date = models.DateField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)



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

    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)




# models.py

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    gstin = models.CharField(max_length=20, verbose_name="GSTIN Number")

    address_primary = models.TextField()
    address_secondary = models.TextField(blank=True, null=True)

    phone_primary = models.CharField(max_length=15)
    phone_secondary = models.CharField(max_length=15, blank=True, null=True)

    email = models.EmailField()
    reference_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.gstin})"


