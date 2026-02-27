from django.db import models
from django.contrib.auth.models import User

class Strategy(models.Model):
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=50) # e.g., NIFTY23FEB18000CE
    exchange = models.CharField(max_length=10, default='NFO')
    token = models.CharField(max_length=20) # Shoonya's numeric instrument ID
    is_active = models.BooleanField(default=False)
    
    # Strategy Parameters
    # ema_period = models.IntegerField(default=50)
    # sma_period = models.IntegerField(default=200)
    # rsi_period = models.IntegerField(default=14)
    # rsi_threshold = models.IntegerField(default=30) # For your "RSI < 30" rule
    
    logic_config = models.JSONField(default=dict, blank=True)
    
    # Risk & Execution
    sl_pct = models.FloatField(default=1.0)
    target_pct = models.FloatField(default=2.0)
    start_time = models.TimeField(default="09:15")
    square_off = models.TimeField(default="15:15")

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