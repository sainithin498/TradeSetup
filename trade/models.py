from django.db import models

# Create your models here.
class TradeUser(models.Model):
    trader_name = models.CharField(max_length=50)
    fyer_token = models.TextField()
    fyer_key = models.CharField(max_length=50, unique=True)
    updated_at = models.DateTimeField(auto_now=True)
    mobile = models.CharField(unique=True)
    is_active = models.BooleanField(default=True)
    balance = models.IntegerField(default=0)
    token_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f'{self.trader_name}' 

class tradeResponse(models.Model):
    trade_user  = models.ForeignKey('TradeUser', related_name='trade_user', on_delete=models.CASCADE)
    response = models.TextField()
    requestpath = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     return f'{self.trade_user.trader_name} {self.response}'

    

