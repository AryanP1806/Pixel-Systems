from django.db import models

# -----------------------------
# Product Collection
# -----------------------------
class ProductCollection(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# -----------------------------
# Product Model (Type)
# -----------------------------
class ProductModel(models.Model):
    brand = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    description = models.TextField()
    collection = models.ForeignKey(ProductCollection, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.brand} {self.model_name}"

# -----------------------------
# Product Unit (Individual Laptop)
# -----------------------------
class ProductUnit(models.Model):
    model = models.ForeignKey(ProductModel, on_delete=models.CASCADE)
    asset_id = models.CharField(max_length=50, unique=True)
    serial_number = models.CharField(max_length=100, unique=True)
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('rented', 'Rented'),
        ('maintenance', 'Under Maintenance'),
        ('retired', 'Retired'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')

    def __str__(self):
        return f"{self.model} - {self.asset_id}"

# -----------------------------
# Customer
# -----------------------------
class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number_primary = models.CharField(max_length=15)
    phone_number_secondary = models.CharField(max_length=15, blank=True, null=True)

    address_primary = models.TextField()
    address_secondary = models.TextField(blank=True, null=True)

    is_permanent = models.BooleanField(default=False)
    is_bni_member = models.BooleanField(default=False)

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
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    unit = models.ForeignKey(ProductUnit, on_delete=models.CASCADE)
    rental_start_date = models.DateField()
    rental_end_date = models.DateField(null=True, blank=True)
    
    STATUS_CHOICES = [
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')

    def __str__(self):
        return f"Rental #{self.id} - {self.customer.name} - {self.unit.asset_id}"

# -----------------------------
# Payment
# -----------------------------
class Payment(models.Model):
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    
    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
    ]
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('unpaid', 'Unpaid'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unpaid')

    def __str__(self):
        return f"Payment #{self.id} - {self.rental} - {self.amount}"
