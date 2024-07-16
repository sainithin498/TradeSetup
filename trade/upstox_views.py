from concurrent.futures import ThreadPoolExecutor
import datetime
import json
import pandas as pd
import requests
from trade.endpoints import BROKERAGE, EXITORDER, ORDER_DETAILS, PLACE_ORDER, POSITIONS
from trade.models import UpstoxOrder, UpstoxUser
from trade.utils import getStrikePrice, getexpiryValue
from django.conf import settings
from django.http import FileResponse, HttpResponse, JsonResponse
from rest_framework import parsers, renderers, serializers, status, viewsets
from rest_framework.decorators import api_view


def saveplaceOrders(trader, id, symbol, trend, instrument,qty, product ):
    data = {
        'order_id': id,
        'symbol': symbol,
        'trend': trend,
        'trader_id':trader,
        'instrument_token': instrument,
        'qty':qty,
        'product': product
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
    product = jsonData.get('product', None)
    weekday = jsonData.get('weekday', None)
    try:
        success = True
        if trend == "CE":
            _type = "BUY"
        else:
            _type = "SELL"
        strike = getStrikePrice(spot, index, _type, weekday)
        trader = UpstoxUser.objects.get(mobile= mobile)
        TOKEN_HEADERS = {
                    'Accept': 'application/json',
                    'Authorization': 'Bearer {}'.format(trader.upstox_token)
                }  
        if index in settings.NSE_INDEX:
            data_path = settings.NSE_PATH
        else:
            data_path = settings.BSE_PATH
        option = strike[4:]
        df = pd.read_csv(data_path)
        
        df = df.loc[df['tradingsymbol'] == option]
        INSTUMENT_KEY = df.iloc[0]['instrument_key']
        print(INSTUMENT_KEY , ':::::', option)
        data = {
            "quantity": quantity,
            "product": "D" if  product and product == "D" else "I",
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
       
        url = PLACE_ORDER
        response = requests.post(url, json=data, headers=TOKEN_HEADERS)
        print(response.json())
        res = response.json()

        orderId = res['data']

        url = ORDER_DETAILS
        det_res = requests.get(url, headers=TOKEN_HEADERS, params=orderId)
        if det_res.json()['data']['status'] == 'complete':
            message='Order placed'    
            saveplaceOrders(trader.id, orderId['order_id'], option, trend, INSTUMENT_KEY, quantity, data['product'])
        else:
            success = False
            message='Order Not placed'    

      
        return JsonResponse({'message':message,'success':success, "response": det_res.json()['data']},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)

def getOrderId(trend):
    openorders = UpstoxOrder.objects.filter(is_open=True).values('instrument_token', 'qty', 'product')
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
            data.update({"instrument_token": order['instrument_token'],  "quantity": order['qty'], 
                         'product': order['product']})
            url = PLACE_ORDER
            print(data)
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
        res = response.json()
        orderId = res['data']

        saveplaceOrders(trader.id, orderId['order_id'], stock, trend, INSTUMENT_KEY, qty)

        return JsonResponse({'message':' {} Stock Order Placed'.format(stock),'success':True},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)


def multiUpstoxUserorderExit(user, data):
    TOKEN_HEADERS = {
            'Accept': 'application/json',
            'Authorization': 'Bearer {}'.format(user.upstox_token)
    }
    url = POSITIONS
    response = requests.get(url, headers=TOKEN_HEADERS)
    positions = response.json()['data']
    payload = {
        "product": "I",
        "validity": "DAY",
        "price": 0,
        "tag": "string",
        "order_type": "MARKET",
        "disclosed_quantity": 0,
        "trigger_price": 0,
        "is_amo": False
    }
    res = []
    findoption = [ opt for opt in positions if opt['quantity']!= 0]
    if data['symbol']:
        findoption = [ opt for opt in findoption if data['symbol'].upper() in  opt['tradingsymbol'] ]
    if data['trend']:
        findoption = [ opt for opt in findoption if data['trend'].upper() in  opt['tradingsymbol'] ]

    instruments = []
    payloads = []
    print('::::::::::::::::::::::::::::',findoption)
    for pos in findoption:
        if pos['quantity'] > 0 :
            transaction_type = "SELL"
        else:
             transaction_type = "BUY"
        payload.update({"product": pos["product"], "transaction_type": transaction_type, "instrument_token": pos['instrument_token'], 
                        "quantity": pos['quantity'] })
        url = PLACE_ORDER
        payloads.append(payload)
        response = requests.post(url, json=payload, headers=TOKEN_HEADERS)
        print('-----------------------',response.json())
        res.append(response.json())
        if response.json()['status'] != "error":
            instruments.append(pos['instrument_token'])

    return res, instruments, payloads


@api_view(["GET", "POST"])
def exitallOrders(request):
    """
    url =/trade/upstox/exitall?mobile=8977810371&symbol=BANKNIFTY
   
    """

    mobile = request.GET.get('mobile',None)
    symbol = request.GET.get('symbol', None)
    trend = request.GET.get('trend', None)

    try:
        if not mobile:
            active_up_trader_objects = UpstoxUser.objects.filter(is_active=True)
        else:
            active_up_trader_objects = UpstoxUser.objects.filter(mobile=mobile)
        data = {
            "symbol": symbol,
            "trend": trend
        }
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(multiUpstoxUserorderExit, record, data) for record in active_up_trader_objects]
            print(futures)
            for future in futures:
                response = future.result()
                results.append(response)
                try:
                    UpstoxOrder.objects.filter(instrument_token__in=response[1]).update(is_open=False, closed_at=datetime.datetime.now())
                except: pass
        return JsonResponse({'message':'All Order Exited successfully','success':True, 'data': results},status=status.HTTP_200_OK)
            
    except Exception as e:        
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)
      

@api_view(["GET", "POST"])
def placeoptionOrder(request):
    
    """
    url = /trade/upstox/optionorder/
    data = {
        "symbol": "NIFTY/BANKNIFTY",
        "price": 52600
        "trend": "CE"/"PE"
        "qty": 15*x/25*x,
        "offlineOrder": "True/False",
        "mobile": "8977810371" #trader mobile
    }"""
    jsonData = json.loads(request.body)
    index = jsonData.get('symbol')
    price = jsonData.get('price')
    trend = jsonData.get('trend', None)
    quantity = jsonData.get('qty', None)
    offlineOrder = jsonData.get('offlineOrder', None)
    mobile = jsonData.get('mobile', None)
    product = jsonData.get('product', None)
    weekday = jsonData.get('weekday', None)
    try:
        success = True
        if trend == "CE":
            _type = "BUY"
        else:
            _type = "SELL"
        year, month, date, week  = getexpiryValue(index, weekday)
        option = index.upper() + str(year)[2:] + str(month) + str(date)+ str(price) + trend
        trader = UpstoxUser.objects.get(mobile= mobile)
        TOKEN_HEADERS = {
                    'Accept': 'application/json',
                    'Authorization': 'Bearer {}'.format(trader.upstox_token)
                }  
        if index in settings.NSE_INDEX:
            data_path = settings.NSE_PATH
        else:
            data_path = settings.BSE_PATH
        df = pd.read_csv(data_path)
        
        df = df.loc[df['tradingsymbol'] == option]
        INSTUMENT_KEY = df.iloc[0]['instrument_key']
        print(INSTUMENT_KEY , ':::::', option)
        
        data = {
            "quantity": quantity,
            "product": "D" if  product and product == "D" else "I",
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
       
        url = PLACE_ORDER
        response = requests.post(url, json=data, headers=TOKEN_HEADERS)
        print(response.json())
        res = response.json()

        orderId = res['data']

        url = ORDER_DETAILS
        det_res = requests.get(url, headers=TOKEN_HEADERS, params=orderId)
        if det_res.json()['data']['status'] == 'complete':
            message='Order placed'    
            saveplaceOrders(trader.id, orderId['order_id'], option, trend, INSTUMENT_KEY, quantity, data['product'])
        else:
            success = False
            message='Order Not placed'    

      
        return JsonResponse({'message':message,'success':success, "response": det_res.json()['data']},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)
