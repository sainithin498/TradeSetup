from django.contrib import admin
from django.urls import path, include
from . import  views 


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

]
