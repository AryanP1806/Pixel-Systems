from django.db import models
from django.contrib.auth.models import User

class Strategy(models.Model):
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=50) # e.g., NIFTY23FEB18000CE
    exchange = models.CharField(max_length=10, default='NFO')
    token = models.CharField(max_length=20) # Shoonya's numeric instrument ID
    is_active = models.BooleanField(default=False)
    
    # Strategy Parameters
    ema_period = models.IntegerField(default=50) # Set default to your recorded 50
    sma_period = models.IntegerField(default=200) # NEW: Add this for your SMA 200 logic
    rsi_period = models.IntegerField(default=14)
    st_period = models.IntegerField(default=7)
    st_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=3.0)

    class Meta:
        verbose_name_plural = "Strategies"

class Order(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    noren_order_no = models.CharField(max_length=100, unique=True)
    side = models.CharField(max_length=10, choices=[('B', 'Buy'), ('S', 'Sell')])
    qty = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='PENDING') # COMPLETE, REJECTED
    timestamp = models.DateTimeField(auto_now_add=True)