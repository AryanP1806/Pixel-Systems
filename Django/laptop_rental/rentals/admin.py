from django.contrib import admin
from .models import Customer, ProductAsset, ProductConfiguration, Rental, Supplier

admin.site.register(Customer)
admin.site.register(ProductAsset)
admin.site.register(ProductConfiguration)
admin.site.register(Rental)
admin.site.register(Supplier)

