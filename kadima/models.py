from django.db import models
from datetime import datetime

from django.contrib.auth.models import User

# class KadimaUser(User):
#     email_active = models.BooleanField(default=False)

#     def __str__(self):
#         return self.username

class EmailSupport(models.Model):
    enabled = models.BooleanField(default=False)

    def __str__(self):
        return self.enabled

class StockData(models.Model):

    table_index = models.IntegerField(default=0)


    stock_date = models.DateTimeField(auto_now=True)
    stock_displayed_date = models.CharField(max_length=100)
    ticker = models.CharField(max_length=100)
    stock_price = models.FloatField()

    prev_close = models.FloatField(null=True)
    todays_open = models.FloatField(null=True)

    sample_period_14 = models.BooleanField(default=False)

    stock_trend_30 = models.FloatField(null=True)
    stock_trend_14 = models.FloatField(null=True)

    macd_trend_30 = models.FloatField(null=True)
    macd_trend_14 = models.FloatField(null=True)

    money_flow_trend_30 = models.FloatField(null=True)
    money_flow_trend_14 = models.FloatField(null=True)

    week_1 = models.FloatField(null=True)
    week_1_min = models.FloatField(null=True)
    week_1_max = models.FloatField(null=True)

    week_2 = models.FloatField(null=True)
    week_2_min = models.FloatField(null=True)
    week_2_max = models.FloatField(null=True)

    week_3 = models.FloatField(null=True)
    week_3_min = models.FloatField(null=True)
    week_3_max = models.FloatField(null=True)

    week_5 = models.FloatField(null=True)
    week_5_min = models.FloatField(null=True)
    week_5_max = models.FloatField(null=True)

    week_1_color = models.CharField(max_length=100)
    week_2_color = models.CharField(max_length=100)
    week_3_color = models.CharField(max_length=100)
    week_5_color = models.CharField(max_length=100)

    gap_1 = models.FloatField(null=True)
    gap_2 = models.FloatField(null=True)
    gap_3 = models.FloatField(null=True)

    updading_gap_1_flag = models.BooleanField(default=False, null=True)

    gap_1_color = models.CharField(max_length=100)
    gap_2_color = models.CharField(max_length=100)
    gap_3_color = models.CharField(max_length=100)


    # Technical Indicators 
    macd_30_clash = models.BooleanField(null=True, default=False)
    macd_14_clash = models.BooleanField(null=True, default=False)
    macd_30_color = models.CharField(max_length=100)
    macd_14_color = models.CharField(max_length=100)
    
    mfi_30_clash = models.BooleanField(null=True, default=False)
    mfi_14_clash = models.BooleanField(null=True, default=False)
    mfi_30_color = models.CharField(max_length=100)
    mfi_14_color = models.CharField(max_length=100)

    rsi = models.FloatField()
    rsi_color = models.CharField(max_length=10, blank=True, null=True)

    # Company information
    earnings_call = models.DateTimeField(null=True)
    earnings_call_displayed = models.CharField(max_length=100, null=True)
    earnings_warning = models.CharField(max_length=100, null=True)

    dividend_date = models.CharField(max_length=100,null=True)
    dividend = models.FloatField(null=True)
    dividend_warning = models.CharField(max_length=100, null=True)
    
    # Trigger & alarm page
    stock_alarm = models.BooleanField(default=False) # Flag whether the stock is in the stock_alarm page
    stock_alarm_delta = models.FloatField(null=True) # delta amount to add to the current price 
    stock_initial_price = models.FloatField(null=True) # stock price at trigger set
    stock_current_price = models.FloatField(null=True) # stock price when adding to alarms list
    stock_load_price = models.FloatField(null=True) # stock price when adding to alarms list
    stock_price_up_alarm = models.BooleanField(default=False) # True when the current price exceeds the initial price + delta
    stock_price_down_alarm = models.BooleanField(default=False) # True when the current price goes lower the initial price + delta
    stock_alarm_trigger_set = models.BooleanField(default=False) # True when the alarm is set/trigger armed
    stock_alarm_sound_on_off = models.BooleanField(default=False) # Flag to control the sound (play only once)

    stock_alarm_1 = models.FloatField(null=True)
    stock_alarm_2 = models.FloatField(null=True)
    stock_alarm_3 = models.FloatField(null=True)
    stock_alarm_4 = models.FloatField(null=True)
    stock_alarm_5 = models.FloatField(null=True)
    stock_alarm_6 = models.FloatField(null=True)
    stock_alarm_7 = models.FloatField(null=True)
    stock_alarm_8 = models.FloatField(null=True)
    stock_alarm_9 = models.FloatField(null=True)
    stock_alarm_10 = models.FloatField(null=True)

    stock_alarm_1_color = models.CharField(max_length=30, null=True)
    stock_alarm_2_color = models.CharField(max_length=30, null=True)
    stock_alarm_3_color = models.CharField(max_length=30, null=True)
    stock_alarm_4_color = models.CharField(max_length=30, null=True)
    stock_alarm_5_color = models.CharField(max_length=30, null=True)
    stock_alarm_6_color = models.CharField(max_length=30, null=True)
    stock_alarm_7_color = models.CharField(max_length=30, null=True)
    stock_alarm_8_color = models.CharField(max_length=30, null=True)
    stock_alarm_9_color = models.CharField(max_length=30, null=True)
    stock_alarm_10_color = models.CharField(max_length=30, null=True)

    # Email alert flag
    stock_email_alert = models.BooleanField(default=False)

    # History Page Section
    saved_to_history = models.BooleanField(default=False)

    stocks_bought = models.FloatField(null=True, default=0)
    purchase_price = models.FloatField(null=True, default=0.0)
    stocks_sold  = models.FloatField(null=True, default=0)
    selling_price = models.FloatField(null=True, default=0.0)
    profit = models.FloatField(null=True, default=0.0)
    dividends = models.FloatField(null=True, default=0.0)
    total_profit = models.FloatField(null=True, default=0.0)

    def __str__(self):
        return self.ticker

    def delete(self, *args, **kwargs):
        self.ticker.delete()
        self.trend.delete()
        self.macd_trend.delete()
        self.money_flow_trend.delete()
        self.week_1.delete()
        self.week_2.delete()
        self.week_3.delete()
        self.week_5.delete()
        self.gap_1.delete()
        self.gap_2.delete()
        self.gap_3.delete()
        self.earnings_call.delete()
        super().delete(*args, **kwargs)

    class Meta:
        unique_together = (("ticker", "table_index"),)

class IndicesData(models.Model):
    index_symbol = models.CharField(max_length=10, primary_key=True)
    sample_date = models.DateTimeField(auto_now=True)
    index_prev_close = models.FloatField(null=True, blank=True)
    index_current_value = models.FloatField(null=True, blank=True)
    index_api_id = models.IntegerField(null=True)
    index_change = models.FloatField(null=True, blank=True)

    index_week1 = models.FloatField(null=True, blank=True)
    index_week1_min = models.FloatField(null=True, blank=True)
    index_week1_max = models.FloatField(null=True, blank=True)

    index_week2 = models.FloatField(null=True, blank=True)
    index_week2_min = models.FloatField(null=True, blank=True)
    index_week2_max = models.FloatField(null=True, blank=True)
    
    index_week3 = models.FloatField(null=True, blank=True)
    index_week3_min = models.FloatField(null=True, blank=True)
    index_week3_max = models.FloatField(null=True, blank=True)

    index_week_1_color = models.CharField(max_length=100, blank=True)
    index_week_2_color = models.CharField(max_length=100, blank=True)
    index_week_3_color = models.CharField(max_length=100, blank=True)

    index_trend = models.FloatField(null=True, blank=True)

    index_macd = models.FloatField(null=True, blank=True)
    index_macd_clash = models.BooleanField(null=True, default=False, blank=True)
    index_macd_color = models.CharField(max_length=50, null=True, blank=True)

    index_mfi = models.FloatField(null=True, blank=True)
    index_mfi_clash = models.BooleanField(null=True, default=False, blank=True)
    index_mfi_color = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
            return self.index_symbol

class HistoryStock(models.Model):
    stock = models.ForeignKey(StockData, on_delete=models.CASCADE)
    table_index = models.IntegerField()
    time_added = models.TimeField(auto_now=True)

    stocks_bought = models.FloatField(null=True, default=0)
    purchase_price = models.FloatField(null=True, default=0.0)
    stocks_sold  = models.FloatField(null=True, default=0)
    selling_price = models.FloatField(null=True, default=0.0)
    profit = models.FloatField(null=True, default=0.0)
    dividends = models.FloatField(null=True, default=0.0)
    total_profit = models.FloatField(null=True, default=0.0)
    
    def __str__(self):
        return self.stock.ticker