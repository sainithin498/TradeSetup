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
        return self.trader_name, self.mobile, self.is_active, self.balance

