from django.contrib import admin
from django.urls import path, include
from . import  views 


urlpatterns = [    
    path('placeorder/', views.buyOrder),
    path('sellorder/', views.sellOrder)

]
