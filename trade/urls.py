from django.contrib import admin
from django.urls import path, include
from . import  views, upstox_views



urlpatterns = [    
    path('buyorder/', views.buyOrder),    
    path('buyindexorder/', views.buyindexAlertOrder),
    path('sellorder/', views.sellOrder),
    path('exitorder/<str:key>/', views.exitOrder),
    path('buystockorder/', views.buystockOrder),
    path('sellstockorder/', views.sellstockOrder), 
    path('checkprofile/', views.checkProfile),
    path('optionorder/', views.optionOrder),    
    path('exitbyid/', views.exitbyId),

    ### Upstox Urls
    path('upstox/buyorder/', upstox_views.placeOrder),    
    path('upstox/exitorderbyid/', upstox_views.exitOrderbyId),
    path('upstox/exitall/<str:mobile>/', upstox_views.exitallOrders),



]
