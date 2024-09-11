from django.db import models
"""['segment', 'name', 'instrument_type',
       'instrument_key', 'lot_size',
       'asset_type', 'asset_symbol
       'trading_symbol', 'strike_price'
       ]"""
# Create your models here.
class UpstoxTradeSymbol(models.Model):
    instrument_key = models.CharField(max_length=50, blank=True, null=True)
    segment = models.CharField(max_length=50, blank=True, null=True)
    trading_symbol = models.CharField(max_length=50,blank=True, null=True)
    name = models.CharField(max_length=50,blank=True, null=True)
    lot_size = models.IntegerField(blank=True, null=True)
    asset_type = models.CharField(max_length=50, blank=True, null=True)
    asset_symbol = models.CharField(max_length=50, blank=True, null=True)
    instrument_type	= models.CharField(max_length=50,blank=True, null=True)
    strike_price = models.IntegerField(blank=True, null=True)
    expiry = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)



class PandLReport(models.Model):
    class Meta:
        verbose_name = 'PandL Report'
        verbose_name_plural  = 'PandL Report'


class TradeUser(models.Model):
    trader_name = models.CharField(max_length=50)
    fyer_token = models.TextField()
    fyer_key = models.CharField(max_length=50, unique=True)
    updated_at = models.DateTimeField(auto_now=True)
    mobile = models.CharField(unique=True)
    pin = models.CharField(max_length=10, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    balance = models.IntegerField(default=0)
    stock_quantity = models.IntegerField(blank=True, null=True)
    bn_option_quantity = models.IntegerField(blank=True, null=True)
    nf_option_quantity = models.IntegerField(blank=True, null=True)

    token_date = models.DateField(blank=True, null=True)
    redirect_uri = models.CharField(max_length=100, blank=True, null=True)
    secret_key = models.CharField(max_length=100, blank=True, null=True)
    symbol = models.CharField(max_length=50, blank=True, null=True)
    

    def __str__(self):
        return f'{self.trader_name}' 

class tradeResponse(models.Model):
    trade_user  = models.ForeignKey('TradeUser', related_name='trade_user', on_delete=models.CASCADE)
    response = models.TextField()
    requestpath = models.CharField(max_length=50, blank=True, null=True)
    symbol = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class strikepointMaster(models.Model):
    index = models.CharField(max_length=10)
    weekday = models.IntegerField()
    trade_round_points = models.IntegerField()
    week = models.CharField(max_length=15, blank=True, null=True)

class Transaction(models.Model):
    payload = models.TextField()
    symbol = models.CharField(max_length=50)
    qty = models.IntegerField()
    trx_id = models.CharField(max_length=30)
    trader = models.ForeignKey('TradeUser', related_name='trax_trader', on_delete=models.CASCADE)
    is_close = models.BooleanField(default=False)


class UpstoxUser(models.Model):
    trader_name = models.CharField(max_length=50)
    upstox_token = models.TextField()
    upstox_key = models.CharField(max_length=50, unique=True)
    updated_at = models.DateTimeField(auto_now=True)
    mobile = models.CharField(unique=True)
    pin = models.CharField(max_length=10, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    balance = models.IntegerField(default=0)
    stock_quantity = models.IntegerField(blank=True, null=True)
    bn_option_quantity = models.IntegerField(blank=True, null=True)
    nf_option_quantity = models.IntegerField(blank=True, null=True)
    token_date = models.DateField(blank=True, null=True)
    redirect_uri = models.CharField(max_length=100, blank=True, null=True)
    upstox_secret_key = models.CharField(max_length=100, blank=True, null=True)
    symbol = models.CharField(max_length=50, blank=True, null=True)

    # def __str__(self):
    #     return f'{self.trader_name}' 

class UpstoxOrder(models.Model):
    trader = models.ForeignKey('UpstoxUser', related_name='order_trader', on_delete=models.CASCADE)    
    order_id = models.CharField(max_length=50)
    symbol = models.CharField(max_length=50)
    index = models.CharField(max_length=20, blank=True, null=True)
    expiry = models.CharField(max_length=15, blank=True, null=True)
    product = models.CharField(max_length=5, blank=True, null=True)
    instrument_token = models.CharField(max_length=50, blank=True, null=True)
    qty = models.IntegerField(blank=True, null=True)
    trend = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    is_open = models.BooleanField(default=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    trigger_price = models.FloatField(blank=True, null=True)
    close_price = models.FloatField(blank=True, null=True)
    
class LiveFeedData(models.Model):
    symbol = models.CharField(max_length=30, blank=True, null=True)
    instrumentKey = models.CharField(max_length=30, blank=True, null=True)
    tradedate = models.DateField(max_length=15, blank=True, null=True)
    tradetime = models.TimeField(max_length=10, blank=True, null=True)
    endtime = models.TimeField(max_length=10, blank=True, null=True)
    topen = models.DecimalField(max_digits=10,decimal_places=2, blank=True, null=True)
    thigh = models.DecimalField(max_digits=10,decimal_places=2, blank=True, null=True)
    tlow = models.DecimalField(max_digits=10,decimal_places=2, blank=True, null=True)
    tclos = models.DecimalField(max_digits=10,decimal_places=2, blank=True, null=True)
    e20 = models.DecimalField(max_digits=10,decimal_places=2, blank=True, null=True)
    e50 = models.DecimalField(max_digits=10,decimal_places=2, blank=True, null=True)
    rsi = models.DecimalField(max_digits=10,decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('symbol', 'instrumentKey', 'tradedate', 'tradetime')
