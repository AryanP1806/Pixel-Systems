from django.contrib import admin
from .models import Strategy, Order

@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'is_active')
    list_editable = ('is_active',) # Quick toggle in the list view

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('noren_order_no', 'strategy', 'side', 'status', 'timestamp')