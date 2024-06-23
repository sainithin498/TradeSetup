from django.db import models

# Create your models here.
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

    def __str__(self):
        return f'{self.trader_name}' 

class tradeResponse(models.Model):
    trade_user  = models.ForeignKey('TradeUser', related_name='trade_user', on_delete=models.CASCADE)
    response = models.TextField()
    requestpath = models.CharField(max_length=50, blank=True, null=True)
    symbol = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     return f'{self.trade_user.trader_name} {self.response}'


class strikepointMaster(models.Model):
    index = models.CharField(max_length=10)
    weekday = models.IntegerField()
    trade_round_points = models.IntegerField()
    week = models.CharField(max_length=15, blank=True, null=True)


    

