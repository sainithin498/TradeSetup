from django.contrib import admin
from django.urls import path, include
from . import  views 


urlpatterns = [    
    path('buyorder/', views.buyOrder),
    path('sellorder/', views.sellOrder),
    path('exitorder/<str:key>/', views.exitOrder),
    path('buystockorder/', views.buystockOrder),
    path('sellstockorder/', views.sellstockOrder), 
    path('checkprofile/<str:key>/', views.checkProfile),
    path('optionorder/', views.optionOrder),    
    path('optionexit/', views.optionExit),

]
