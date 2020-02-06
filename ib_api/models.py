from django.db import models

class StockList(models.Model):
    stock_symbol = models.CharField(max_length=100)
    stock_price = models.FloatField(null=True)
    stock_high = models.FloatField(null=True)
    stock_low = models.FloatField(null=True)
    stock_close = models.FloatField(null=True)
    stock_volume = models.IntegerField(null=True)
    write_time  = models.DateTimeField(auto_now=True)

