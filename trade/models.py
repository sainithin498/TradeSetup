from django.db import models

# Create your models here.
class TradeUser(models.Model):
    trader_name = models.CharField(max_length=50)
    fyer_token = models.TextField()
    fyer_key = models.CharField(max_length=50)
    updated_at = models.DateTimeField(auto_now=True)

