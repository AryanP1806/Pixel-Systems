from django.db import models
from django.utils.timezone import now
from datetime import timedelta, date, timezone
from django.contrib.auth.models import User

# -----------------------------
# Product 
# -----------------------------




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
    ]
    # asset_id = models.CharField(max_length=50, unique=True, blank=True)
    asset_id = models.CharField(max_length=50, blank=True, null=True)

    type_of_asset = models.CharField(max_length=50, choices=ASSET_TYPES)
    brand = models.CharField(max_length=100)
    model_no = models.CharField(max_length=100)
    serial_no = models.CharField(max_length=100, unique=True)

    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_value = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateField()

    under_warranty = models.BooleanField(default=False)
    warranty_duration_months = models.PositiveIntegerField(null=True, blank=True)
    purchased_from = models.CharField(max_length=255) 

    condition_status = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='working'
    )

    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.asset_id:
            year = self.purchase_date.year if self.purchase_date else now().year
            last_id = ProductAsset.objects.filter(purchase_date__year=year).count() + 1
            self.asset_id = f"Pixel/{year}/{last_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.type_of_asset} | {self.brand} {self.model_no} [{self.asset_id}]"
    
    @property
    def is_available(self):
        # return not self.rentals.filter(status__in=['ongoing', 'overdue']).exists()
        return (self.condition_status == 'working' and not self.rentals.filter(status__in=['ongoing', 'overdue']).exists())

    @property
    @property
    def total_rent_earned(self):
        return sum(r.payment.amount for r in self.rentals.all() if r.payment)


    @property
    def total_rent_earned(self):
       return sum(r.payment.amount for r in self.rentals.all() if r.payment)

    @property
    def total_repairs(self):
        return sum(repair.cost for repair in self.repairs.all())
    
    @property
    def net_profit(self):
        return (self.total_rent_earned - self.total_repairs)




# -----------------------------
# Product Unit (Individual Laptop)
# -----------------------------
class ProductConfiguration(models.Model):
    asset = models.ForeignKey(ProductAsset, on_delete=models.CASCADE, related_name='configurations')
    date_of_config = models.DateField()

    ram = models.CharField(max_length=50, blank=True, null=True)
    hdd = models.CharField(max_length=50, blank=True, null=True)
    ssd = models.CharField(max_length=50, blank=True, null=True)
    graphics = models.CharField(max_length=100, blank=True, null=True)
    display_size = models.CharField(max_length=50, blank=True, null=True)
    power_supply = models.CharField(max_length=100, blank=True, null=True)
    detailed_config = models.TextField(blank=True, null=True)
    repair_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

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
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'phone_number_primary'], name='unique_customer_by_name_and_phone'),
        ]

    def __str__(self):
        return self.name
# -----------------------------
# Rental
# -----------------------------
class Rental(models.Model):
    STATUS_CHOICES = (
        ('ongoing', 'Ongoing'),
        ('overdue', 'Overdue'),
        ('completed', 'Completed'),
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    asset = models.ForeignKey(ProductAsset, on_delete=models.CASCADE, related_name='rentals',blank=True, null=True)
    rental_start_date = models.DateField()
    duration_days = models.PositiveIntegerField(blank=True)
    rental_end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')


    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    contract_number = models.CharField(max_length=50, blank=True)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.rental_start_date and self.duration_days:
            self.rental_end_date = self.rental_start_date + timedelta(days=self.duration_days)
        super().save(*args, **kwargs)

    def is_overdue(self):
        return self.status == 'ongoing' and date.today() > self.rental_end_date

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
    date = models.DateField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
