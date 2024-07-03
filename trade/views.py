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
from concurrent.futures import ThreadPoolExecutor

from trade.utils import execute, getStrikePrice, getToken, savingResponse


# Create your views here.

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
  
def multiOrderExecute(user, data, qty, path):
    common_data = {
        "qty": qty,    
        "type":2,
        "side":1,
        "productType":"MARGIN",
        "limitPrice":0,
        "stopPrice":0,
        "validity":"DAY",
        "disclosedQty":0,
        "orderTag":"tag1"
    }
    if not qty:
        if 'BANKNIFTY' in data['symbol']:
            qty = user.bn_option_quantity if user.bn_option_quantity else 15
        else:
            qty = user.nf_option_quantity if user.nf_option_quantity else 25
        common_data['qty'] = qty
    data.update(common_data)
    session = fyersModel.FyersModel(client_id=user.fyer_key, token=user.fyer_token)
    try:
        _response = session.place_order(data=data)
        return user.id, user.trader_name, _response
    
    except Exception as e:
        return str(e)
    
@api_view(["GET", "POST"])
def buyindexAlertOrder(request):
    """Buy order placing for index alerts"""
    """/trade/buyindexorder/"""
    """data = {
        "symbol": "NIFTY/BANKNIFTY",
        "price": 51231, #spot price
        "qty": 15*x/25*x,
        "offlineOrder": "True/False",
        "mobile": "8977810371" #trader mobile
        "_type": "BUY"
    }"""
    print('body-----------------------', request.body)
    jsonData = json.loads(request.body)
    spot = jsonData.get('price')
    index = jsonData.get('symbol')
    quantity = jsonData.get('qty', None)
    offlineOrder = jsonData.get('offlineOrder', None)
    trend = jsonData.get('trend', None)
    mobile = jsonData.get('mobile', None) 

    if trend == "CE":
        _type = "BUY"
    else:
        _type = "SELL"
    strike = getStrikePrice(spot, index, _type)
    
    data = {
        "symbol":strike,       
        "offlineOrder":True if offlineOrder and offlineOrder == "True"  else False,
    }
    if not mobile:
        active_trader_objects = TradeUser.objects.filter(is_active=True)
    else:
        active_trader_objects = TradeUser.objects.filter(mobile=mobile)
    try:
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(multiOrderExecute, record, data, quantity, request.path) for record in active_trader_objects]
            for future in futures:
                response = future.result()
                results.append(response)
                savingResponse(response[0], response[2], request.path, data['symbol'])

        return JsonResponse({'message':'Order placed successfully','success':True, "data": results},status=status.HTTP_200_OK)
    
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)


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
        "offlineOrder":True if offlineOrder and offlineOrder == "True"  else False,
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
        "offlineOrder": True if offlineOrder and offlineOrder == "True"  else False,
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
        "offlineOrder":True if offlineOrder and offlineOrder == "True"  else False,
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
        "offlineOrder":True if offlineOrder and offlineOrder == "True"  else False,
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
        "offlineOrder":True if offlineOrder and offlineOrder == "True"  else False,
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

# @api_view(['GET', 'POST'])
# def exitbyId(request):

#     """
#     url = "/trade/exitbyid/"
#     data = {
#         "symbol": "NSE:BANKNIFTY24JUN51000CE-MARGIN",
#         "mobile": 8977810371,
#         "trend": "PE"/"CE"
#     }"""
#     jsonData = json.loads(request.body)
#     symbol = jsonData.get('symbol', None)
#     mobile = jsonData.get("mobile", None)
#     trend = jsonData.get('trend', None) # "CE"/"PE"

#     _token, _key = getToken(mobile)
#     tradeUser = TradeUser.objects.get(fyer_key = _key)
    
#     session = fyersModel.FyersModel(client_id=_key, token=_token)
#     openPositions=[symbol]
#     if not symbol and (trend and 'netPositions' in session.positions()):
#         netPositions = session.positions()['netPositions']
#         openPositions = [ pos['id'] for pos in netPositions if pos['qty']>0 and trend in pos['id']]
            
#     if not len(openPositions)>0:
#         savingResponse(tradeUser.id, "No Open Postions for {}".format(trend), request.path, openPositions)
        
#         return JsonResponse({'message':'Please Provide Symbol','success':True},status=status.HTTP_200_OK)
    
#     session = fyersModel.FyersModel(client_id=_key, token=_token,is_async=False)
#     data = { "id": openPositions }
#     try:
#         response = session.exit_positions(data=data)
#         savingResponse(tradeUser.id, response, request.path, openPositions)
#         return JsonResponse({'message':'Exit postitions successfully','success':True},status=status.HTTP_200_OK)
        
#     except Exception as e:        
#         return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)

def multiUserorderExit(user, data):

    session = fyersModel.FyersModel(client_id=user.fyer_key, token=user.fyer_token)
    openPositions=[data['symbol']]
    if not data['symbol'] and (data['trend'] and 'netPositions' in session.positions()):
        netPositions = session.positions()['netPositions']
        openPositions = [ pos['id'] for pos in netPositions if pos['qty']>0 and data['trend'] in pos['id']]
            
    if not len(openPositions)>0:
        return user.id,user.trader_name, "No Open Positions for {}".format(data['trend']), openPositions
    
    data = { "id": openPositions }
    try:
        response = session.exit_positions(data=data)
        return user.id, user.trader_name, response, openPositions
        
    except Exception as e:        
        return user.id, user.trader_name, str(e), openPositions


@api_view(['GET', 'POST'])
def exitbyId(request):

    """
    url = "/trade/exitbyid/"
    data = {
        "symbol": "NSE:BANKNIFTY24JUN51000CE-MARGIN",
        "mobile": 8977810371,
        "trend": "PE"/"CE"
    }"""
    jsonData = json.loads(request.body)
    symbol = jsonData.get('symbol', None)
    mobile = jsonData.get("mobile", None)
    trend = jsonData.get('trend', None) # "CE"/"PE"

    data = {
        "symbol": symbol,
        "trend": trend
    }
    if not mobile:
        active_trader_objects = TradeUser.objects.filter(is_active=True)
    else:
        active_trader_objects = TradeUser.objects.filter(mobile=mobile)
    try:
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(multiUserorderExit, record, data) for record in active_trader_objects]
            for future in futures:
                response = future.result()
                results.append(response)
                savingResponse(response[0], response[2], request.path, response[3])
        return JsonResponse({'message':'Order Exited successfully','success':True, "data": results},status=status.HTTP_200_OK)
        
    except Exception as e:        
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)

    



@api_view(["GET"])
def checkProfile(request):  
    """http://65.0.99.151/trade/checkprofile/ISORT89TOC-100/"""
    active_trader_objects =  TradeUser.objects.all()
    results = []
    try:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(execute, record) for record in active_trader_objects]
            for future in futures:
                response = future.result()
                results.append(response)

        return JsonResponse({'success':True , "data":results},status=status.HTTP_200_OK)

    except Exception as e:
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)
