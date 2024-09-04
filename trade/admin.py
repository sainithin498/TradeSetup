from django.apps import apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from .models import *
from django.utils.html import format_html
from .adminaction import export_as_csv_action
from django.urls import path
from trade.upstox_views import pandlcalculation
class tradeUserAdmin(admin.ModelAdmin):
    model = TradeUser
    list_display = ['trader_name', 'mobile', 'is_active', 'balance', 'fetchBalance', 'stock_quantity', 'bn_option_quantity','nf_option_quantity', 'token_date' ]
    export_fields = ['trader_name', 'fyer_token','fyer_key','mobile','pin','is_active','balance','stock_quantity','bn_option_quantity',
            'nf_option_quantity','token_date','redirect_uri','secret_key']
    
    actions = [export_as_csv_action("Export to CSV", fields=export_fields)]
    def fetchBalance(self, obj):
        url = '/admin/trade/'+ str(obj.id) +'/fyers/balance/'
        return format_html("<a href={}>Fetch Balance</a>", url)
    
    def has_delete_permission(self, request, obj=None):
        return False

class tradeResponseAdmin(admin.ModelAdmin):
    model = tradeResponse
    list_display = ['trade_user','requestpath', 'symbol', 'response', 'created_at' ]

    export_fields = ['trade_user','requestpath', 'symbol', 'response', 'created_at' ]

    actions = [export_as_csv_action("Export to CSV", fields=export_fields)]

    def trade_user(self, obj):
        return obj.trade_user.trader_name
    
    def has_delete_permission(self, request, obj=None):
        return False

class strikepointMasterAdmin(admin.ModelAdmin):
    model = strikepointMaster
    list_display = ['index', 'week', 'weekday', 'trade_round_points' ]

    def trade_user(self, obj):
        return obj.trade_user.trader_name
    
class TransactionAdmin(admin.ModelAdmin):
    model = Transaction
    list_display = ['symbol', 'qty', 'trx_id', 'trader' ]

    def trade(self, obj):
        return obj.trade_user.trader_name
    
class UpstoxUserAdmin(admin.ModelAdmin):
    model = UpstoxUser
    list_display = ['trader_name', 'mobile', 'is_active', 'balance', 'fetchBalance', 'stock_quantity', 'bn_option_quantity','nf_option_quantity', 'token_date', 'tokengen' ]
    export_fields = ['trader_name', 'fyer_token','fyer_key','mobile','pin','is_active','balance','stock_quantity','bn_option_quantity',
            'nf_option_quantity','token_date','redirect_uri','secret_key']
    
    actions = [export_as_csv_action("Export to CSV", fields=export_fields)]
    def fetchBalance(self, obj):
        url = '/admin/trade/'+ str(obj.id) +'/upstox/balance/'
        return format_html("<a href={}>Fetch Balance</a>", url)
    
    def tokengen(self, obj):
        url = '/admin/trade/'+ str(obj.id) +'/upstox/gentoken/'
        return format_html("<a href={}>Gen Token</a>", url)
    
    def has_delete_permission(self, request, obj=None):
        return False

class UpstoxOrderAdmin(admin.ModelAdmin):
    model = UpstoxOrder
    list_display = ['traderName','order_id','symbol', 'index','instrument_token','product','trigger_price', 'close_price', 'qty','trend',
                    'created_at','is_open', 'closed_at']

    def traderName(self, obj):
        return obj.trader.trader_name
  
class UpstoxTradeSymbolAdmin(admin.ModelAdmin):
    model = UpstoxTradeSymbol
    list_display = ['instrument_key', 'tradingsymbol', 'expiry', 'lot_size', 'instrument_type', 'option_type', 'exchange']

    
    
class PandLReportAdmin(admin.ModelAdmin):
    model = PandLReport

    def get_urls(self):
        add_view_name = '{}_{}_add'.format(
            self.model._meta.app_label, self.model._meta.model_name)
        view_name = '{}_{}_changelist'.format(
            self.model._meta.app_label, self.model._meta.model_name)
        return [
            path('', pandlcalculation, name=add_view_name),
            path('', pandlcalculation, name=view_name),
        ]

class LiveFeedDataAdmin(admin.ModelAdmin):
    model = LiveFeedData
    list_display = ['symbol', 'instrumentKey', 'tradedate', 'tradetime', 'endtime', 'topen', 'thigh', 'tlow', 'tclos']



class LiveFeedDataAdmin(admin.ModelAdmin):
    model = LiveFeedData
    list_display = ['symbol', 'instrumentKey', 'tradedate', 'tradetime', 'topen', 'thigh', 'tlow', 'tclos']

admin.site.register(TradeUser, tradeUserAdmin)
admin.site.register(tradeResponse, tradeResponseAdmin)
admin.site.register(strikepointMaster, strikepointMasterAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(UpstoxUser, UpstoxUserAdmin)
admin.site.register(UpstoxOrder, UpstoxOrderAdmin)
admin.site.register(UpstoxTradeSymbol, UpstoxTradeSymbolAdmin)
admin.site.register(PandLReport, PandLReportAdmin)
admin.site.register(LiveFeedData, LiveFeedDataAdmin)
