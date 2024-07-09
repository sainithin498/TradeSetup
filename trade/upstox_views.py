import datetime
import json
import pandas as pd
import requests
from trade.endpoints import BROKERAGE, EXITORDER, ORDER_DETAILS, PLACE_ORDER, POSITIONS
from trade.models import UpstoxOrder, UpstoxUser
from trade.utils import getStrikePrice
from django.conf import settings
from django.http import FileResponse, HttpResponse, JsonResponse
from rest_framework import parsers, renderers, serializers, status, viewsets
from rest_framework.decorators import api_view


def saveplaceOrders(trader, id, symbol, trend, instrument,qty ):
    data = {
        'order_id': id,
        'symbol': symbol,
        'trend': trend,
        'trader_id':trader,
        'instrument_token': instrument,
        'qty':qty
    }
    UpstoxOrder.objects.create(**data)


@api_view(["GET", "POST"])
def placeOrder(request):
    
    """
    url = /trade/upstox/buyorder/
    data = {
        "symbol": "NIFTY/BANKNIFTY",
        "price": 51231, #spot price
        "trend": "CE"/"PE"
        "qty": 15*x/25*x,
        "offlineOrder": "True/False",
        "mobile": "8977810371" #trader mobile
    }"""
    jsonData = json.loads(request.body)
    spot = jsonData.get('price')
    index = jsonData.get('symbol')
    trend = jsonData.get('trend', None)
    quantity = jsonData.get('qty', None)
    offlineOrder = jsonData.get('offlineOrder', None)
    mobile = jsonData.get('mobile', None)   
    try:
        if trend == "CE":
            _type = "BUY"
        else:
            _type = "SELL"
        strike = getStrikePrice(spot, index, _type)
        trader = UpstoxUser.objects.get(mobile= mobile)
        TOKEN_HEADERS = {
                    'Accept': 'application/json',
                    'Authorization': 'Bearer {}'.format(trader.upstox_token)
                }  
        if index in settings.NSE_INDEX:
            data_path = settings.NSE_PATH
        else:
            data_path = settings.BSE_PATH
        # NSE:BANKNIFTY2471052400CE
        option = strike[4:]
        print(option)
        df = pd.read_csv(data_path)
        
        df = df.loc[df['tradingsymbol'] == option]
        INSTUMENT_KEY = df.iloc[0]['instrument_key']
        print(INSTUMENT_KEY)
        data = {
            "quantity": quantity,
            "product": "I",
            "validity": "DAY",
            "price": 0,
            "tag": "string",
            "instrument_token": INSTUMENT_KEY ,
            "order_type": "MARKET",
            "transaction_type": "BUY",
            "disclosed_quantity": 0,
            "trigger_price": 0,
            "is_amo": True if offlineOrder and offlineOrder == "True"  else False
        }
        brok_data = {
            "instrument_token":"NSE_FO|55217",
            "quantity":quantity,
            "product":"I",
            "transaction_type": "BUY",
            "price":0
        }
        url = PLACE_ORDER
        response = requests.post(url, json=data, headers=TOKEN_HEADERS)
        print(response.json())

        res = response.json()
        orderId = res['data']
        saveplaceOrders(trader.id, orderId['order_id'], option, trend, INSTUMENT_KEY, quantity)
        url = ORDER_DETAILS
        # url =BROKERAGE
        # response = requests.request("GET", url, headers=TOKEN_HEADERS, data=brok_data)
        response = requests.get(url, headers=TOKEN_HEADERS, params=orderId)
        print(response.json())
        url = POSITIONS
        response = requests.get(url, headers=TOKEN_HEADERS)

        print(response.json())
        return JsonResponse({'message':'Order placed','success':True},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)

def getOrderId(trend):
    openorders = UpstoxOrder.objects.filter(is_open=True).values('instrument_token', 'qty')
    if trend == 'all':
        orders = openorders
    else:
        orders = openorders.filter(trend=trend)
    return orders
       


@api_view(["GET", "POST"])
def exitOrderbyId(request):
    """
    url = /trade/upstox/exitorderbyid/
    {
        "trend":"PE",
        "mobile": "8977810371"
    }
    """
    jsonData = json.loads(request.body)
    mobile = jsonData.get('mobile', None)
    trend = jsonData.get('trend', None)
    try:
        openOrders = getOrderId(trend)
        trader = UpstoxUser.objects.get(mobile=mobile)
        TOKEN_HEADERS = {
                    'Accept': 'application/json',
                    'Authorization': 'Bearer {}'.format(trader.upstox_token)
                }
        data = {
            "product": "I",
            "validity": "DAY",
            "price": 0,
            "tag": "string",
            "order_type": "MARKET",
            "transaction_type": "SELL",
            "disclosed_quantity": 0,
            "trigger_price": 0,
            "is_amo": False
        }
        for order in openOrders:
            data.update({"instrument_token": order['instrument_token'],  "quantity": order['qty']})
            url = PLACE_ORDER
            response = requests.post(url, json=data, headers=TOKEN_HEADERS)
            print(response.json())
        openOrders.update(is_open=False, closed_at=datetime.datetime.now())

        return JsonResponse({'message':'Order Exited','success':True},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)



@api_view(["GET", "POST"])
def upstoxStocks(request):
    """
    url =/trade/upstox/stockorder/
    {
        "stock":"IRCTC",
        "mobile": "8977810371",
        "qty":10,
        "trend": "BUY"/"SELL",
        "offlineOrder": "True"/"False"
    }   
    """
    jsonData = json.loads(request.body)
    mobile = jsonData.get('mobile', None)
    stock = jsonData.get('stock', None)
    qty = jsonData.get('qty', None)
    offlineOrder = jsonData.get('offlineOrder', None)
    trend = jsonData.get('trend', None)

    try:
        trader = UpstoxUser.objects.get(mobile=mobile)
        TOKEN_HEADERS = {
                'Accept': 'application/json',
                'Authorization': 'Bearer {}'.format(trader.upstox_token)
        }
        data_path = settings.NSE_PATH            
        df = pd.read_csv(data_path)            
        df = df.loc[df['tradingsymbol'] == stock]
        INSTUMENT_KEY = df.iloc[0]['instrument_key']
        
        data = {
            "product": "I",
            "validity": "DAY",
            "price": 0,
            "tag": "string",
            "order_type": "MARKET",
            "transaction_type": trend,
            "disclosed_quantity": 0,
            "trigger_price": 0,
            "is_amo": True if offlineOrder and offlineOrder == "True"  else False,
            "instrument_token": INSTUMENT_KEY,  
            "quantity": qty
        }
        
        
        url = PLACE_ORDER
        response = requests.post(url, json=data, headers=TOKEN_HEADERS)
        print(response.json())

        return JsonResponse({'message':' {} Stock Order Placed'.format(stock),'success':True},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)



@api_view(["GET", "POST"])
def exitallOrders(request, mobile):
    """
    url =/trade/upstox/exitall/8977810371/
   
    """
    try:
        if mobile:
            trader = UpstoxUser.objects.get(mobile=mobile)
            TOKEN_HEADERS = {
                    'Accept': 'application/json',
                    'Authorization': 'Bearer {}'.format(trader.upstox_token)
            }
            openOrders = getOrderId('all')
            data = {
                "product": "I",
                "validity": "DAY",
                "price": 0,
                "tag": "string",
                "order_type": "MARKET",
                "transaction_type": "SELL",
                "disclosed_quantity": 0,
                "trigger_price": 0,
                "is_amo": False
            }
            for order in openOrders:
                data.update({"instrument_token": order['instrument_token'],  "quantity": order['qty']})
                url = PLACE_ORDER
                response = requests.post(url, json=data, headers=TOKEN_HEADERS)
                print(response.json())
                openOrders.update(is_open=False, closed_at=datetime.datetime.now())

        return JsonResponse({'message':' All Orders Exited','success':True},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)