from django.shortcuts import render, redirect
from fyers_api import fyersModel
from fyers_apiv3 import fyersModel
import os
from rest_framework.decorators import api_view
from django.http import FileResponse, HttpResponse, JsonResponse
from rest_framework import parsers, renderers, serializers, status, viewsets
import json
import datetime
from trade.models import *
from gettoken import scrappingToken
import time

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
    # strike = "NSE:" + index.upper() + str(year)[2:] + str(month) + str(date)+ str(value) + code
    strike = "NSE:" + index.upper() + str(year)[2:] + "JUN"+ str(value) + code
    return strike, qty


def getToken(mobile):
    print(mobile)
    if mobile:
        trduser = TradeUser.objects.filter(mobile=mobile).last()
    else:
        trduser = TradeUser.objects.filter(is_active=True).last()
    fyer_token = trduser.fyer_token
    fyer_key = trduser.fyer_key
    print(fyer_token, fyer_key)
    return fyer_token, fyer_key


def getTokenRequest(request, pk):
    trader = TradeUser.objects.get(id=pk)
    print(trader)

    if request.method == 'POST':
        otp = request.POST.get('otp_pin')
        scrappingToken.delay('fyers', otp, pk)
        time.sleep(20)
        
        
        return redirect('/admin/trade/tradeuser/')
    return render(request,'trade/tokengenerate.html',{
        'trader_name': trader.trader_name
    })

@api_view(["GET", "POST"])
def buyOrder(request):
    print('body-----------------------', request.body)
    jsonData = json.loads(request.body)
    spot = jsonData.get('price')
    index = jsonData.get('index')
    mobile = jsonData.get('mobile', None)
       
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
    _token, _key = getToken(mobile)
    eshwar_id = _key
    token = _token
    tradeUser = TradeUser.objects.get(fyer_key = _key)
    print(tradeUser)
    eshwar = fyersModel.FyersModel(client_id=eshwar_id, token=token, log_path="")
    try:
        response = eshwar.exit_positions(data={})
        print(response)
        savingResponse(tradeUser.id, response, request.path)
        
        buytrigger = True
        if response['s'] == 'ok' and 'Exit request has been' in response['message']: 
            response = eshwar.exit_positions(data={})
            time.sleep(2)
            buytrigger = True

        elif response['s'] == 'ok' or 'no open positions' in response['message']:
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
    mobile = jsonData.get('mobile', None)

   
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
    
    _token, _key = getToken(mobile)
    eshwar_id = _key
    token = _token
    tradeUser = TradeUser.objects.get(fyer_key = _key)
    print(tradeUser)
    eshwar = fyersModel.FyersModel(client_id=eshwar_id, token=token, log_path="")
    try:
        response = eshwar.exit_positions(data={})
        savingResponse(tradeUser.id, response, request.path)
        sub = 'Exit request has been'
        buytrigger = True
        if response['s'] == 'ok' and sub in response['message']: 
            response = eshwar.exit_positions(data={})
            time.sleep(2)
            buytrigger = True

        elif response['s'] == 'ok' or 'no open positions' in response['message']:
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
    mobile = None
    _token, _key = getToken(mobile)
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
    jsonData = json.loads(request.body)
    price = jsonData.get('price', 0)
    symbol = jsonData.get('symbol')
    prodType = jsonData.get('productType', None)
    quantity = jsonData.get('qty', None)
    offlineOrder = jsonData.get('offlineOrder', None)
    # offlineOrder = "False"
    # prodType = "INTRADAY" 
    # price = 0
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
    _token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhcGkuZnllcnMuaW4iLCJpYXQiOjE3MTg4NTg0NjQsImV4cCI6MTcxODkyOTgwNCwibmJmIjoxNzE4ODU4NDY0LCJhdWQiOlsieDowIiwieDoxIiwieDoyIiwiZDoxIiwiZDoyIiwieDoxIiwieDowIl0sInN1YiI6ImFjY2Vzc190b2tlbiIsImF0X2hhc2giOiJnQUFBQUFCbWM3TGdvZVY4b2t1TkZ2cnVUaGs5aTlqTFEtZlEyMXVVSVoxQ1F1UmdsUnp6eWZxTUFwNXZwdjNDQTZhTU5faHFJeEY0dFlfMTgzQ3JmNGxrT2V1LWQ1Sm5xNmJxdmRXS01qdEt4ZTJ3WXFaUU4xdz0iLCJkaXNwbGF5X25hbWUiOiJSQU1BTkFESEEgS0FOQUtBIERVUkdBIiwib21zIjoiSzEiLCJoc21fa2V5IjoiMDg4MjAzM2I0ZGU1NjY3MmUzYmU4YWZiODYzMzRhZTI1MWU5NTFkNDczMDRhYmU0OTllMjk4NmQiLCJmeV9pZCI6IllSMTAwNzIiLCJhcHBUeXBlIjoxMDAsInBvYV9mbGFnIjoiTiJ9.zK-yCnPp8HC_kK0Ls832sLB_-P7p4Q0nswCqXNtVBSc"
    _key = "T6RUCIRR09-100"
    # _token, _key = getToken()
    eshwar_id = _key
    token = _token
    # tradeUser = TradeUser.objects.get(fyer_key = _key)
    eshwar = fyersModel.FyersModel(client_id=eshwar_id, token=token, log_path="")
    try:
        response = eshwar.exit_positions(data={})
        print(response)
        savingResponse(6, response, request.path)
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
            savingResponse(6, eshwar_response, request.path)
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
    jsonData = json.loads(request.body)
    price = jsonData.get('price', 0)
    symbol = jsonData.get('symbol')
    prodType = jsonData.get('productType', None)
    quantity = jsonData.get('qty', None)
    offlineOrder = jsonData.get('offlineOrder', None)
    # offlineOrder = "False"
    # prodType = "INTRADAY" 
    # price = 0
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
    _token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhcGkuZnllcnMuaW4iLCJpYXQiOjE3MTg4NTg0NjQsImV4cCI6MTcxODkyOTgwNCwibmJmIjoxNzE4ODU4NDY0LCJhdWQiOlsieDowIiwieDoxIiwieDoyIiwiZDoxIiwiZDoyIiwieDoxIiwieDowIl0sInN1YiI6ImFjY2Vzc190b2tlbiIsImF0X2hhc2giOiJnQUFBQUFCbWM3TGdvZVY4b2t1TkZ2cnVUaGs5aTlqTFEtZlEyMXVVSVoxQ1F1UmdsUnp6eWZxTUFwNXZwdjNDQTZhTU5faHFJeEY0dFlfMTgzQ3JmNGxrT2V1LWQ1Sm5xNmJxdmRXS01qdEt4ZTJ3WXFaUU4xdz0iLCJkaXNwbGF5X25hbWUiOiJSQU1BTkFESEEgS0FOQUtBIERVUkdBIiwib21zIjoiSzEiLCJoc21fa2V5IjoiMDg4MjAzM2I0ZGU1NjY3MmUzYmU4YWZiODYzMzRhZTI1MWU5NTFkNDczMDRhYmU0OTllMjk4NmQiLCJmeV9pZCI6IllSMTAwNzIiLCJhcHBUeXBlIjoxMDAsInBvYV9mbGFnIjoiTiJ9.zK-yCnPp8HC_kK0Ls832sLB_-P7p4Q0nswCqXNtVBSc"
    _key = "T6RUCIRR09-100"
    # _token, _key = getToken()
    eshwar_id = _key
    token = _token
    # tradeUser = TradeUser.objects.get(fyer_key = _key)
    eshwar = fyersModel.FyersModel(client_id=eshwar_id, token=token, log_path="")
    try:
        response = eshwar.exit_positions(data={})
        print(response)
        savingResponse(6, response, request.path)
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
            savingResponse(6, eshwar_response, request.path)
            return JsonResponse({'message':'Order placed successfully','success':True},status=status.HTTP_200_OK)
        else: 
            return JsonResponse({'message':'Order Not placed','success':False},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)

   