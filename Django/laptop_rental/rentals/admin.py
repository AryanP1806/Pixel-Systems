from django.contrib import admin
from .models import Customer, ProductModel, ProductUnit, ProductCollection, Rental, Payment

admin.site.register(Customer)
admin.site.register(ProductModel)
admin.site.register(ProductUnit)
admin.site.register(ProductCollection)
admin.site.register(Rental)
admin.site.register(Payment)
