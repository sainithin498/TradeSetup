from django.apps import apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from .models import *
from django.utils.html import format_html


class tradeUserAdmin(admin.ModelAdmin):
    model = TradeUser
    list_display = ['trader_name', 'mobile', 'is_active', 'balance', 'generateToken', 'token_date' ]

    def generateToken(self, obj):
        url = '/admin/trade/'+ str(obj.id) +'/token/'
        return format_html("<a href={}>Generate Token</a>", url)


class tradeResponseAdmin(admin.ModelAdmin):
    model = tradeResponse
    list_display = ['trade_user','requestpath', 'response', 'created_at' ]

    def trade_user(self, obj):
        return obj.trade_user.trader_name


admin.site.register(TradeUser, tradeUserAdmin)
admin.site.register(tradeResponse, tradeResponseAdmin)
