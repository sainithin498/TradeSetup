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
from trade.gettoken import scrappingToken
import time
from django.contrib import messages

# Create your views here.

def savingResponse(tradeUser, response, requestpath, symbol=None):
    data = {
        'trade_user_id':tradeUser,
        'response': response,
        'requestpath': requestpath,
        'symbol': symbol
    }
    tradeResponse.objects.create(**data)

def roundnearest(val, _type):
    prcn = val%100
    if _type == 'BUY':
        res = val-prcn
        code = 'CE'
    else:
        res = 100 + val-prcn
        code = 'PE'
    return res, code

def dategeneration(weekday):
    today = datetime.datetime.now().date()
    week = today.weekday()
    days_ahead = weekday - week
    if days_ahead < 0: 
        days_ahead += 7
    resDt =  today + datetime.timedelta(days_ahead)
    year, month, date = resDt.year, resDt.month, resDt.day
    return year, month, date, week

def getStrikePrice(spot, index, _type):
    """Using for index alerts, not for option alerts"""
    """NSE:NIFTY2292217000CE"""
    if index == 'NIFTY':
        weekday = 3
        qty = 25
    elif index == 'BANKNIFTY':
        weekday = 2
        qty = 15
    year, month, date, week = dategeneration(weekday)
    value, code = roundnearest(int(spot), _type)
    print(value)
    try:
        points = strikepointMaster.objects.get(index=index, weekday=week)
    except:
        points = 500
    if _type == 'BUY':
        value -= points
    else:
        value += points
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
    return fyer_token, fyer_key


def getTokenRequest(request, pk):
    trader = TradeUser.objects.get(id=pk)
    print(trader)

    if request.method == 'POST':
        otp = request.POST.get('otp_pin')
        scrappingToken('fyers', otp, pk)
        # time.sleep(20)
        
        
        return redirect('/admin/trade/tradeuser/')
    return render(request,'trade/tokengenerate.html',{
        'trader_name': trader.trader_name
    })


def getBalanceRequest(request, pk):
    trader = TradeUser.objects.get(id=pk)

    session = fyersModel.FyersModel(client_id=trader.fyer_key, token=trader.fyer_token)
    try:
        funds = session.funds()
        amount = 0
        for dt in funds['fund_limit']:
            if dt['title']=="Available Balance":
                amount = dt['equityAmount']
                break;
        trader.balance = amount
        trader.save()
        messages.success(request, 'Balance Updated for User : {}'.format(trader.trader_name))
    except Exception as e:
        print(str(e))
        messages.error(request, "Please check the Token for User : {}".format(trader.trader_name))
        
    return redirect('/admin/trade/tradeuser/')
  

@api_view(["GET", "POST"])
def buyOrder(request):
    """Buy order placing for index alerts"""
    """/trade/buyorder/"""
    """data = {
        "symbol": "NIFTY/BANKNIFTY",
        "price": 51231, #spot price
        "qty": 15*x/25*x,
        "offlineOrder": "True/False",
        "mobile": "8977810371" #trader mobile
    }"""
    print('body-----------------------', request.body)
    jsonData = json.loads(request.body)
    spot = jsonData.get('price')
    index = jsonData.get('symbol')
    quantity = jsonData.get('qty', None)
    offlineOrder = jsonData.get('offlineOrder', None)
    mobile = jsonData.get('mobile', None)   

    strike, qty = getStrikePrice(spot, index, 'BUY')
    _token, _key = getToken(mobile)
    tradeUser = TradeUser.objects.get(fyer_key = _key)
    if quantity:
        qty = quantity
    else:
        if index == 'BANKNIFTY':
            qty = tradeUser.bn_option_quantity
        elif index == 'NIFTY':
            qty = tradeUser.nf_option_quantity
    data = {
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
    print(data)
    print(tradeUser)
    session = fyersModel.FyersModel(client_id=_key, token=_token)
    try:
        response = session.exit_positions(data={})
        savingResponse(tradeUser.id, response, request.path, strike)
        
        buytrigger = True
        if response['s'] == 'ok' and 'Exit request has been' in response['message']: 
            response = session.exit_positions(data={})
            time.sleep(2)
            buytrigger = True

        elif response['s'] == 'ok' or 'no open positions' in response['message']:
            buytrigger = True
        else:
            buytrigger = False
    except Exception as e:
        buytrigger = False
        print("Some error occured  account:", str(e))

    try:
        if buytrigger:       
            _response = session.place_order(data=data)
            print(_response)
            savingResponse(tradeUser.id, _response, request.path, strike)
            return JsonResponse({'message':'Order placed successfully','success':True},status=status.HTTP_200_OK)
        else: 
            return JsonResponse({'message':'Order Not placed','success':False},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)

     
            

@api_view(["GET", "POST"])
def sellOrder(request):
    """Sell order placing for index alerts"""
    """/trade/sellorder/"""
    """data = {
        "symbol": "NIFTY/BANKNIFTY",
        "price": 51231, #spot price
        "qty": 15*x/25*x, #(Optional)
        "offlineOrder": "True/False",
        "mobile": "8977810371" #trader mobile #(Optional)
    }"""
    print('body-----------------------', request.body)
    jsonData = json.loads(request.body)
    spot = jsonData.get('price')
    index = jsonData.get('symbol')
    quantity = jsonData.get('qty', None)
    offlineOrder = jsonData.get('offlineOrder', None)
    mobile = jsonData.get('mobile', None)

   
    strike, qty = getStrikePrice(spot, index, "SELL")
    _token, _key = getToken(mobile)
   
    tradeUser = TradeUser.objects.get(fyer_key = _key)
    if quantity:
        qty = quantity
    else:
        if index == 'BANKNIFTY':
            qty = tradeUser.bn_option_quantity
        elif index == 'NIFTY':
            qty = tradeUser.nf_option_quantity
    data = {
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
    
    
    print(tradeUser)
    session = fyersModel.FyersModel(client_id=_key, token=_token)
    try:
        response = session.exit_positions(data={})
        savingResponse(tradeUser.id, response, request.path, strike)
        
        buytrigger = True
        if response['s'] == 'ok' and 'Exit request has been' in response['message']: 
            response = session.exit_positions(data={})
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
            _response = session.place_order(data=data)
            print(_response)
            savingResponse(tradeUser.id, _response, request.path, strike)
            return JsonResponse({'message':'Order sell successfully','success':True},status=status.HTTP_200_OK)
        else: 
            return JsonResponse({'message':'Order Not places','success':True},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)

            
@api_view(["GET", "POST"])        
def exitOrder(request, key):
    """exitorder/<str:key>/"""
    """Using to exit all positions for a user"""
    
    tradeUser = TradeUser.objects.get(fyer_key = key)
    _token, _key = getToken(tradeUser.mobile)
    
    session = fyersModel.FyersModel(client_id=_key, token=_token)
    try:
        response = session.exit_positions(data={})
        print(response)
        savingResponse(tradeUser.id, response, request.path)
        return JsonResponse({'message':'Exit postitions successfully','success':True},status=status.HTTP_200_OK)
        
    except Exception as e:
        
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)



@api_view(["GET", "POST"])
def buystockOrder(request):
    """"/trade/buystockorder/"
    data = {
        "symbol":"NSE:IDEA-EQ",
        "price": :limitPrice/0,
        "qty":10,
        "productType": "INTRADAY" (Optional)
        "offlineOrder": True/False,
        "mobile": "8977810371"
    }"""
    print('body-----------------------', request.body)
    jsonData = json.loads(request.body)
    price = jsonData.get('price', 0)
    symbol = jsonData.get('symbol')
    prodType = jsonData.get('productType', None)
    quantity = jsonData.get('qty', None)
    offlineOrder = jsonData.get('offlineOrder', None)
    mobile = jsonData.get('mobile', None)
    is_first = jsonData.get('is_first', None)


    _token, _key = getToken(mobile)    
    tradeUser = TradeUser.objects.get(fyer_key = _key)
    session = fyersModel.FyersModel(client_id=_key, token=_token)
    if quantity:
        qty = quantity
    else:
        if is_first:
            qty = tradeUser.stock_quantity
        else:
            qty = tradeUser.stock_quantity*2

    data = {
        "symbol":symbol,
        "qty":qty,
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
    
    buytrigger = True
   
    try:
        if buytrigger:       
            _response = session.place_order(data=data)
            print(_response)
            savingResponse(tradeUser.id, _response, request.path, symbol)
            return JsonResponse({'message':'Order placed successfully','success':True},status=status.HTTP_200_OK)
        else: 
            return JsonResponse({'message':'Order Not placed','success':False},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
def sellstockOrder(request):
    # "/trade/sellstockorder/"
    # data = {
    #     "symbol":"NSE:IDEA-EQ",
    #     "price": :limitPrice/0,
    #     "qty":10,
    #     "offlineOrder": True/False,
    #     "mobile": "8977810371"
    # }
    print('body-----------------------', request.body)
    jsonData = json.loads(request.body)
    price = jsonData.get('price', 0)
    symbol = jsonData.get('symbol')
    prodType = jsonData.get('productType', None)
    quantity = jsonData.get('qty', None)
    offlineOrder = jsonData.get('offlineOrder', None)
    mobile = jsonData.get('mobile', None)
    is_first = jsonData.get('is_first', None)
    if quantity:
        qty = quantity
    else:
        if is_first:
            qty = tradeUser.stock_quantity
        else:
            qty = tradeUser.stock_quantity*2

    data = {
        "symbol":symbol,
        "qty":qty,
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
  
    _token, _key = getToken(mobile)
   
    tradeUser = TradeUser.objects.get(fyer_key = _key)
    session = fyersModel.FyersModel(client_id=_key, token=_token, log_path="")
    buytrigger = True
   
    try:
        if buytrigger:       
            _response = session.place_order(data=data)
            print(_response)
            savingResponse(tradeUser.id, _response, request.path, symbol)
            return JsonResponse({'message':'Order placed successfully','success':True},status=status.HTTP_200_OK)
        else: 
            return JsonResponse({'message':'Order Not placed','success':False},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)

@api_view(["GET", "POST"])
def optionOrder(request):
    """data = {
        "sybmol": "NSE:BANKNIFTY24JUN51000CE",
        "qty":15,
        "mobile": 8977810371,
        "offlineOrder":False/True
    }"""
    jsonData = json.loads(request.body)
    symbol = jsonData.get('symbol', None)
    qty = jsonData.get("qty", None)
    mobile = jsonData.get("mobile", None)
    offlineOrder = jsonData.get("offlineOrder", None)
    data = {
        "symbol":symbol,
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
    print(data)
    _token, _key = getToken(mobile)
    tradeUser = TradeUser.objects.get(fyer_key = _key)
    session = fyersModel.FyersModel(client_id=_key, token=_token, log_path="")
    print(tradeUser)
    try:
        _response = session.place_order(data=data)
        print(_response)
        savingResponse(tradeUser.id, _response, request.path, symbol)
        return JsonResponse({'message':'Order placed successfully','success':True},status=status.HTTP_200_OK)
        
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
def optionExit(request):
    """data = {
        "symbol": "NSE:BANKNIFTY24JUN51000CE-MARGIN",
        "mobile": 8977810371
    }"""
    jsonData = json.loads(request.body)
    symbol = jsonData.get('symbol', None)
    mobile = jsonData.get("mobile", None)

    _token, _key = getToken(mobile)
    tradeUser = TradeUser.objects.get(fyer_key = _key)
    session = fyersModel.FyersModel(client_id=_key, token=_token,is_async=False)
    data = { "id": symbol  }
    try:
        response = session.exit_positions(data=data)
        savingResponse(tradeUser.id, response, request.path, symbol)
        return JsonResponse({'message':'Exit postitions successfully','success':True},status=status.HTTP_200_OK)
        
    except Exception as e:        
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)


@api_view(["GET"])
def checkProfile(request, key):  
    """/trade/checkprofile/ISORT89TOC-100/"""
    if key:
        try:
            user = TradeUser.objects.get(fyer_key=key)
            session = fyersModel.FyersModel(client_id=user.fyer_key, token=user.fyer_token, log_path="")
            return JsonResponse({'success':True , "data":session.get_profile()},status=status.HTTP_200_OK)


        except Exception as e:
            return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)
