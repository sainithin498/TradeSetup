from django.shortcuts import render
from fyers_api import fyersModel
# from fyers_apiv3 import fyersModel
import os
from rest_framework.decorators import api_view
from django.http import FileResponse, HttpResponse, JsonResponse
from rest_framework import parsers, renderers, serializers, status, viewsets
import json
import datetime
from trade.models import *

# Create your views here.

def savingResponse(tradeUser, response, requestpath):
    data = {
        'trade_user_id':tradeUser,
        'response': response,
        'requestpath': requestpath
    }
    tradeResponse.objects.create(**data)

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
    offlineOrder = jsonData.get('offlineOrder', None)
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
    "offlineOrder":True if offlineOrder == "True" else False,
    "orderTag":"tag1"
    }
    print(eshwar_data)
    _token, _key = getToken()
    eshwar_id = _key
    token = _token
    tradeUser = TradeUser.objects.get(fyer_key = _key)
    eshwar = fyersModel.FyersModel(client_id=eshwar_id, token=token, log_path="")
    try:
        response = eshwar.exit_positions(data={})
        print(response)
        savingResponse(tradeUser.id, response, request.path)
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
            savingResponse(tradeUser.id, eshwar_response, request.path)
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
    offlineOrder = jsonData.get('offlineOrder', None)
   
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
    "offlineOrder":True if offlineOrder == "True" else False,
    "orderTag":"tag1"
    }
    
    _token, _key = getToken()
    eshwar_id = _key
    token = _token
    tradeUser = TradeUser.objects.get(fyer_key = _key)

    eshwar = fyersModel.FyersModel(client_id=eshwar_id, token=token, log_path="")
    try:
        response = eshwar.exit_positions(data={})
        savingResponse(tradeUser.id, response, request.path)
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
            savingResponse(tradeUser.id, eshwar_response, request.path)
            return JsonResponse({'message':'Order sell successfully','success':True},status=status.HTTP_200_OK)
        else: 
            return JsonResponse({'message':'Order Not places','success':True},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)

            
@api_view(["GET", "POST"])        
def exitOrder(request):
    _token, _key = getToken()
    eshwar_id = _key
    token = _token
    tradeUser = TradeUser.objects.get(fyer_key = _key)
    eshwar = fyersModel.FyersModel(client_id=eshwar_id, token=token, log_path="")
    try:
        response = eshwar.exit_positions(data={})
        print(response)
        savingResponse(tradeUser.id, response, request.path)
        return JsonResponse({'message':'Exit postitions successfully','success':True},status=status.HTTP_200_OK)
        
    except Exception as e:
        
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)



@api_view(["GET", "POST"])
def buystockOrder(request):
    # import ipdb ; ipdb.set_trace()
    print('body-----------------------', request.body)
    # jsonData = json.loads(request.body)
    # price = jsonData.get('price', 0)
    # symbol = jsonData.get('symbol')
    # prodType = jsonData.get('productType', None)
    # quantity = jsonData.get('qty', None)
    # offlineOrder = jsonData.get('offlineOrder', None)
    offlineOrder = "False"
    symbol = "NSE:MCX-EQ"
    quantity = 2
    prodType = "INTRADAY" 
    price = 0
    eshwar_data = {
    "symbol":symbol,
    "qty":quantity,
    "type":2,
    "side":1,
    "productType":prodType if prodType else 'INTRADAY',
    "limitPrice":price,
    "stopPrice":0,
    "validity":"DAY",
    "disclosedQty":0,
    "offlineOrder":True if offlineOrder == "True" else False,
    "orderTag":"tag1"
    }
    print(eshwar_data)
    _token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhcGkubG9naW4uZnllcnMuaW4iLCJpYXQiOjE3MTg2ODA3MzAsImV4cCI6MTcxODcxMDczMCwibmJmIjoxNzE4NjgwMTMwLCJhdWQiOiJbXCJ4OjBcIiwgXCJ4OjFcIiwgXCJ4OjJcIiwgXCJkOjFcIiwgXCJkOjJcIiwgXCJ4OjFcIiwgXCJ4OjBcIl0iLCJzdWIiOiJhdXRoX2NvZGUiLCJkaXNwbGF5X25hbWUiOiJYTTE4MjQ2Iiwib21zIjoiSzEiLCJoc21fa2V5IjoiOTA2MjNiYjkzODNjZTNiNWJjNTA4YzQzODQwNTFmZmVmNzZiNjhhZWQwNDgyOWM3YmFlMTBkY2IiLCJub25jZSI6IiIsImFwcF9pZCI6IklTT1JUODlUT0MiLCJ1dWlkIjoiYWM1NTZjYjIxYzM3NGI2YTg5NjMxODZiMThiOTc1YzkiLCJpcEFkZHIiOiIwLjAuMC4wIiwic2NvcGUiOiIifQ.W8EfRwwUA9CC1KmRjwcy2DUjv31O5TSe28qRLta56SA"
    _key = "ISORT89TOC-100"
    # _token, _key = getToken()
    eshwar_id = _key
    token = _token
    tradeUser = TradeUser.objects.get(fyer_key = _key)
    eshwar = fyersModel.FyersModel(client_id=eshwar_id, token=token, log_path="")
    try:
        response = eshwar.exit_positions(data={})
        print(response)
        savingResponse(tradeUser.id, response, request.path)
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
            savingResponse(tradeUser.id, eshwar_response, request.path)
            return JsonResponse({'message':'Order placed successfully','success':True},status=status.HTTP_200_OK)
        else: 
            return JsonResponse({'message':'Order Not placed','success':False},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
def sellstockOrder(request):
    # import ipdb ; ipdb.set_trace()
    print('body-----------------------', request.body)
    # jsonData = json.loads(request.body)
    # price = jsonData.get('price', 0)
    # symbol = jsonData.get('symbol')
    # prodType = jsonData.get('productType', None)
    # quantity = jsonData.get('qty', None)
    # offlineOrder = jsonData.get('offlineOrder', None)
    offlineOrder = "False"
    symbol = "NSE:MCX-EQ"
    quantity = 2
    prodType = "INTRADAY" 
    price = 0
    eshwar_data = {
    "symbol":symbol,
    "qty":quantity,
    "type":2,
    "side":-1,
    "productType":prodType if prodType else 'INTRADAY',
    "limitPrice":price,
    "stopPrice":0,
    "validity":"DAY",
    "disclosedQty":0,
    "offlineOrder":True if offlineOrder == "True" else False,
    "orderTag":"tag1"
    }
    print(eshwar_data)
    _token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhcGkubG9naW4uZnllcnMuaW4iLCJpYXQiOjE3MTg2ODA3MzAsImV4cCI6MTcxODcxMDczMCwibmJmIjoxNzE4NjgwMTMwLCJhdWQiOiJbXCJ4OjBcIiwgXCJ4OjFcIiwgXCJ4OjJcIiwgXCJkOjFcIiwgXCJkOjJcIiwgXCJ4OjFcIiwgXCJ4OjBcIl0iLCJzdWIiOiJhdXRoX2NvZGUiLCJkaXNwbGF5X25hbWUiOiJYTTE4MjQ2Iiwib21zIjoiSzEiLCJoc21fa2V5IjoiOTA2MjNiYjkzODNjZTNiNWJjNTA4YzQzODQwNTFmZmVmNzZiNjhhZWQwNDgyOWM3YmFlMTBkY2IiLCJub25jZSI6IiIsImFwcF9pZCI6IklTT1JUODlUT0MiLCJ1dWlkIjoiYWM1NTZjYjIxYzM3NGI2YTg5NjMxODZiMThiOTc1YzkiLCJpcEFkZHIiOiIwLjAuMC4wIiwic2NvcGUiOiIifQ.W8EfRwwUA9CC1KmRjwcy2DUjv31O5TSe28qRLta56SA"
    _key = "ISORT89TOC-100"
    # _token, _key = getToken()
    eshwar_id = _key
    token = _token
    tradeUser = TradeUser.objects.get(fyer_key = _key)
    eshwar = fyersModel.FyersModel(client_id=eshwar_id, token=token, log_path="")
    try:
        response = eshwar.exit_positions(data={})
        print(response)
        savingResponse(tradeUser.id, response, request.path)
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
            savingResponse(tradeUser.id, eshwar_response, request.path)
            return JsonResponse({'message':'Order placed successfully','success':True},status=status.HTTP_200_OK)
        else: 
            return JsonResponse({'message':'Order Not placed','success':False},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)

   