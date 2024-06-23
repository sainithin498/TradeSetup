from django.apps import apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from .models import *
from django.utils.html import format_html


class tradeUserAdmin(admin.ModelAdmin):
    model = TradeUser
    list_display = ['trader_name', 'mobile', 'is_active', 'balance', 'fetchBalance', 'stock_quantity', 'bn_option_quantity','nf_option_quantity', 'token_date' ]

    def fetchBalance(self, obj):
        url = '/admin/trade/'+ str(obj.id) +'/balance/'
        return format_html("<a href={}>Fetch Balance</a>", url)


class tradeResponseAdmin(admin.ModelAdmin):
    model = tradeResponse
    list_display = ['trade_user','requestpath', 'symbol', 'response', 'created_at' ]

    def trade_user(self, obj):
        return obj.trade_user.trader_name
        

class strikepointMasterAdmin(admin.ModelAdmin):
    model = strikepointMaster
    list_display = ['index', 'week', 'weekday', 'trade_round_points' ]

    def trade_user(self, obj):
        return obj.trade_user.trader_name

admin.site.register(TradeUser, tradeUserAdmin)
admin.site.register(tradeResponse, tradeResponseAdmin)
admin.site.register(strikepointMaster, strikepointMasterAdmin)

