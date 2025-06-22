from django.contrib import admin
from .models import Customer, ProductAsset, ProductConfiguration, Rental, Payment

admin.site.register(Customer)
admin.site.register(ProductAsset)
admin.site.register(ProductConfiguration)
admin.site.register(Rental)
admin.site.register(Payment)

# @admin.register(ProductUnit)
# class ProductUnitAdmin(admin.ModelAdmin):
#     list_display = ['asset_id', 'serial_no', 'asset']
#     search_fields = ['asset_id', 'serial_no', 'asset__brand']