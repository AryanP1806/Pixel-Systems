from django.contrib import admin
from .models import Customer, ProductAsset, ProductConfiguration, Rental, Supplier, Repair

admin.site.register(Customer)
admin.site.register(ProductAsset)
admin.site.register(ProductConfiguration)
admin.site.register(Rental)
admin.site.register(Supplier)

@admin.register(Repair)
class RepairAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'date',
        'cost',
        'repair_warranty_status',
        'repair_warranty_expiry_date',
        'repair_warranty_days_left',
    )
    list_filter = ('date', 'under_repair_warranty')
