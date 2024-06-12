from django.shortcuts import render
from fyers_api import fyersModel
import os
from rest_framework.decorators import api_view
from django.http import FileResponse, HttpResponse, JsonResponse
from rest_framework import parsers, renderers, serializers, status, viewsets
import json
import datetime
from trade.models import *

# Create your views here.

def roundnearest(val, _type):
    prcn = val%100
    # if prcn <= 50 :
    #     res = val-prcn
    # else:
    #     res = 100 + val-prcn
    if _type == 'BUY':
        res = val-prcn
        code = 'CE'
    else:
        res = 100 + val-prcn
        code = 'PE'
    return res, code

def dategeneration(weekday):
    today = datetime.datetime.now().date()
    days_ahead = weekday - today.weekday()
    if days_ahead < 0: 
        days_ahead += 7
    resDt =  today + datetime.timedelta(days_ahead)
    year, month, date = resDt.year, resDt.month, resDt.day
    return year, month, date 

def getStrikePrice(spot, index, _type):
    """NSE:NIFTY2292217000CE"""
    if index == 'NIFTY':
        weekday = 3
        qty = 25
    elif index == 'BANKNIFTY':
        weekday = 2
        qty = 15
    year, month, date = dategeneration(weekday)
    value, code = roundnearest(int(spot), _type)
    strike = "NSE:" + index.upper() + str(year)[2:] + str(month) + str(date)+ str(value) + code
    return strike, qty


def getToken():
    trduser = TradeUser.objects.last()
    fyer_token = trduser.fyer_token
    fyer_key = trduser.fyer_key
    return fyer_token, fyer_key


@api_view(["GET", "POST"])
def buyOrder(request):
    # import ipdb ; ipdb.set_trace()
    print('body-----------------------', request.body)
    jsonData = json.loads(request.body)
    spot = jsonData.get('price')
    index = jsonData.get('index')
   
    strike, qty = getStrikePrice(spot, index, 'BUY')
    quantity = jsonData.get('qty', None)
   
    if quantity:
        qty = quantity
    eshwar_data = {
    "symbol":strike,
    "qty":qty,
    "type":2,
    "side":1,
    "productType":"MARGIN",
    "limitPrice":0,
    "stopPrice":0,
    "validity":"DAY",
    "disclosedQty":0,
    "offlineOrder":False,
    "orderTag":"tag1"
    }
    print(eshwar_data)
    _token, _key = getToken()
    eshwar_id = _key
    token = _token
    eshwar = fyersModel.FyersModel(client_id=eshwar_id, token=token, log_path="")
    try:
        response = eshwar.exit_positions(data={})
        if response['s'] == 'ok':
            buytrigger = True
        else:
            buytrigger = False
    except Exception as e:
        buytrigger = False
        print("Some error occured in Eshwar account:", str(e))

    try:
        if buytrigger:       
            eshwar_response = eshwar.place_order(data=eshwar_data)
            print(eshwar_response)
            return JsonResponse({'message':'Order placed successfully','success':True},status=status.HTTP_200_OK)
        else: 
            return JsonResponse({'message':'Order Not placed','success':False},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)

     
            

@api_view(["GET", "POST"])
def sellOrder(request):
    print('body-----------------------', request.body)
    jsonData = json.loads(request.body)
    spot = jsonData.get('price')
    index = jsonData.get('index')
    quantity = jsonData.get('qty', None)
   
    strike, qty = getStrikePrice(spot, index, "SELL")
    if quantity:
        qty = quantity
    eshwar_data = {
    "symbol": strike,
    "qty":qty,
    "type":2,
    "side":1,
    "productType":"MARGIN",
    "limitPrice":0,
    "stopPrice":0,
    "validity":"DAY",
    "disclosedQty":0,
    "offlineOrder":False,
    "orderTag":"tag1"
    }
    
    _token, _key = getToken()
    eshwar_id = _key
    token = _token
    eshwar = fyersModel.FyersModel(client_id=eshwar_id, token=token, log_path="")
    try:
        response = eshwar.exit_positions(data={})
        if response['s'] == 'ok':
            buytrigger = True
        else:
            buytrigger = False
    except Exception as e:
        buytrigger = False
        print("Some error occured in Eshwar account:", str(e))

    try:
        if buytrigger:
            eshwar_response = eshwar.place_order(data=eshwar_data)
            print(eshwar_response)
            return JsonResponse({'message':'Order sell successfully','success':True},status=status.HTTP_200_OK)
        else: 
            return JsonResponse({'message':'Order Not places','success':True},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)
            
            

