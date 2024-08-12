from concurrent.futures import ThreadPoolExecutor
import datetime
import json
import pandas as pd
import requests
from trade.endpoints import BROKERAGE, EXITORDER, ORDER_DETAILS, PLACE_ORDER, POSITIONS
from trade.models import LiveFeedData, UpstoxOrder, UpstoxUser
from trade.utils import getStrikePrice, getexpiryValue
from django.conf import settings
from django.http import FileResponse, HttpResponse, JsonResponse
from rest_framework import parsers, renderers, serializers, status, viewsets
from rest_framework.decorators import api_view
from django.shortcuts import render, redirect
from django.db.models import F, FloatField,DecimalField
import pandas as pd
from django.db.models.functions import Cast

def saveplaceOrders(trader, id, symbol, trend, instrument,qty, product, index=None, expiry=None, triggerprice=None ):
    data = {
        'order_id': id,
        'symbol': symbol,
        'trend': trend,
        'trader_id':trader,
        'instrument_token': instrument,
        'qty':qty,
        'product': product,
        'index' : index,
        'expiry' : expiry,
        'trigger_price': triggerprice
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
        _type = "BUY" if trend == "CE" else "SELL"
        strike = getStrikePrice(spot, index, _type, weekday)
        trader = UpstoxUser.objects.get(mobile= mobile)
        TOKEN_HEADERS = {
                    'Accept': 'application/json',
                    'Authorization': 'Bearer {}'.format(trader.upstox_token)
                }  
        data_path = settings.NSE_PATH if index in settings.NSE_INDEX else settings.BSE_PATH
     
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

        if trader.is_active:
            url = PLACE_ORDER
            response = requests.post(url, json=data, headers=TOKEN_HEADERS)
            print(response.json())
            res = response.json()

            orderId = res['data']

            url = ORDER_DETAILS

            det_res = requests.get(url, headers=TOKEN_HEADERS, params=orderId)
            print(det_res.json()['data'])
            if det_res.json()['data']['status'] == 'complete':
                message='Order placed'    
                saveplaceOrders(trader.id, orderId['order_id'], option, trend, INSTUMENT_KEY, quantity, 
                                data['product'],index )
            else:
                success = False
                message='Order Not placed'    
            data = det_res.json()['data']
        else:
            today = datetime.datetime.now().date()
            week = today.weekday()
            if index == 'NIFTY':
                instrument_key = "NSE_INDEX|Nifty 50"
                if not weekday:
                    weekday = 3
            else:
                instrument_key =  "NSE_INDEX|Nifty Bank"
                if not weekday:
                    weekday = 2
            days_ahead = weekday - week
            if days_ahead < 0: 
                days_ahead += 7
            resDt =  today + datetime.timedelta(days_ahead)
            year, month, date = resDt.year, resDt.month, str(resDt.day).rjust(2, '0')
           
            optionch = "https://api.upstox.com/v2/option/chain?instrument_key=" +instrument_key + "&expiry_date=" \
                +str(year)+'-'+str(month)+'-'+str(date)

            _res = requests.get(optionch, headers=TOKEN_HEADERS)
            _res = _res.json()
            option_strike = option[-7:][:5]
            if trend == 'CE':
                optchain_strk = [ele['call_options']['market_data']['ltp'] for ele in _res['data'] if int(ele['strike_price']) ==  int(option_strike)][0]
            else:
                optchain_strk = [ele['put_options']['market_data']['ltp'] for ele in _res['data'] if int(ele['strike_price']) ==  int(option_strike)][0]
            saveplaceOrders(trader.id, "Testing", option, trend, INSTUMENT_KEY, quantity, 
                                data['product'],index, str(year)+'-'+str(month)+'-'+str(date), optchain_strk )
            message = INSTUMENT_KEY
      
        return JsonResponse({'message':message,'success':success, "response": data},status=status.HTTP_200_OK)
    except Exception as e:
        print("Some error occured in Eshwar account:", str(e))
        return JsonResponse({'message':str(e),'success':False},status=status.HTTP_200_OK)

def getOrderId(trend, index=None):

    openorders = UpstoxOrder.objects.filter(is_open=True).values('instrument_token', 'qty', 'product', 'symbol', 'order_id', 'index')
    if index:
        openorders = openorders.filter(index=index)
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
        "mobile": "8977810371",
        "symbol": "NIFTY/BANKNIFTY/SENSEX"
    }
    """
    jsonData = json.loads(request.body)
    mobile = jsonData.get('mobile', None)
    trend = jsonData.get('trend', None)
    index = jsonData.get('symbol', None)

    try:
        openOrders = getOrderId(trend, index)
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
        optchain_strk = None
        for order in openOrders:
            if "SENSEX" in order['symbol'] or 'BANKEX' in  order['symbol']:
                orderId = order['order_id']
                url = ORDER_DETAILS
                det_res = requests.get(url, headers=TOKEN_HEADERS, params=orderId)
                cur_price = det_res.json()['response']['price']
                data.update({"order_type": "LIMIT", "trigger_price": cur_price +.05, "price":cur_price })
            
            
            data.update({"instrument_token": order['instrument_token'],  "quantity": order['qty'], 
                        'product': order['product']})
            if trader.is_active:
                url = PLACE_ORDER
                print(data)
                response = requests.post(url, json=data, headers=TOKEN_HEADERS)
                print(response.json())
            else:
                today = datetime.datetime.now().date()
                week = today.weekday()
                if index == 'NIFTY':
                    instrument_key = "NSE_INDEX|Nifty 50"
                    weekday = 3
                else:
                    instrument_key =  "NSE_INDEX|Nifty Bank"
                    weekday = 2
                days_ahead = weekday - week
                if days_ahead < 0: 
                    days_ahead += 7
                resDt =  today + datetime.timedelta(days_ahead)
                year, month, date = resDt.year, resDt.month, str(resDt.day).rjust(2, '0')
            
                optionch = "https://api.upstox.com/v2/option/chain?instrument_key=" +instrument_key + "&expiry_date=" \
                    +str(year)+'-'+str(month)+'-'+str(date)

                _res = requests.get(optionch, headers=TOKEN_HEADERS)
                _res = _res.json()
                option_strike = order['symbol'][-7:][:5]
                
                if trend == 'CE':
                    optchain_strk = [ele['call_options']['market_data']['ltp'] for ele in _res['data'] if int(ele['strike_price']) ==  int(option_strike)][0]
                else:
                    optchain_strk = [ele['put_options']['market_data']['ltp'] for ele in _res['data'] if int(ele['strike_price']) ==  int(option_strike)][0]
        openOrders.update(is_open=False, closed_at=datetime.datetime.now(), close_price=optchain_strk)


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

        saveplaceOrders(trader.id, orderId['order_id'], stock, trend, INSTUMENT_KEY, qty, data['product'])

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
        transaction_type = "SELL" if pos['quantity'] > 0 else "BUY"
        transaction_type = data['_type'] if data['_type'] else transaction_type
     
        payload.update({"product": pos["product"], "transaction_type": transaction_type, "instrument_token": pos['instrument_token'], 
                        "quantity": abs(pos['quantity']) })
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
    url =/trade/upstox/exitall?mobile=8977810371&symbol=BANKNIFTY&trend=CE/PE&_type=BUY/SELL
   
    """

    mobile = request.GET.get('mobile',None)
    symbol = request.GET.get('symbol', None)
    trend = request.GET.get('trend', None)
    _type = request.GET.get('type', None)

    try:
        if not mobile:
            active_up_trader_objects = UpstoxUser.objects.filter(is_active=True)
        else:
            active_up_trader_objects = UpstoxUser.objects.filter(mobile=mobile)
        data = {
            "symbol": symbol,
            "trend": trend,
            "_type": _type
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
    trans_type = request.GET.get('transaction_type', None)
    jsonData = json.loads(request.body)
    index = jsonData.get('symbol')
    price = jsonData.get('price')
    trend = jsonData.get('trend', None)
    quantity = jsonData.get('qty', None)
    offlineOrder = jsonData.get('offlineOrder', None)
    mobile = jsonData.get('mobile', None)
    product = jsonData.get('product', None)
    weekday = jsonData.get('weekday', None)
    order_type = jsonData.get('order_type', None)
    trigger_price = jsonData.get('trigger_price', None)
    try:
        success = True
       
        year, month, date, week  = getexpiryValue(index, weekday)
        if date :
            option = index.upper() + str(year)[2:] + str(month) + str(date)+ str(price) + trend
        else:
            option = index.upper() + str(year)[2:] + str(month) + str(price) + trend
        trader = UpstoxUser.objects.get(mobile= mobile)
        TOKEN_HEADERS = {
                    'Accept': 'application/json',
                    'Authorization': 'Bearer {}'.format(trader.upstox_token)
                }  
        data_path = settings.NSE_PATH if index in settings.NSE_INDEX else settings.BSE_PATH
      
        df = pd.read_csv(data_path)
        
        df = df.loc[df['tradingsymbol'] == option]
        INSTUMENT_KEY = df.iloc[0]['instrument_key']
        print(INSTUMENT_KEY , ':::::', option)
   
        data = {
            "quantity": quantity,
            "product": "D" if  product and product == "D" else "I",
            "validity": "DAY",
            "price": trigger_price if trigger_price else 0,
            "tag": "string",
            "instrument_token": INSTUMENT_KEY ,
            "order_type": "MARKET" if not order_type else order_type,
            "transaction_type": "SELL" if trans_type and trans_type == "SELL" else "BUY",
            "disclosed_quantity": 0,
            "trigger_price": trigger_price+.05 if trigger_price else 0 ,
            "is_amo": True if offlineOrder and offlineOrder == "True"  else False
        }
       
        url = PLACE_ORDER
        response = requests.post(url, json=data, headers=TOKEN_HEADERS)
        print(data)
        res = response.json()
        if res['status'] == 'error':
            return JsonResponse({'message':res,'success':False},status=status.HTTP_200_OK)
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
    


def pandlcalculation(request):
    all_orders = UpstoxOrder.objects.filter(order_id='Testing', is_open=False)
    all_order_objects = all_orders.values("trader__trader_name", "order_id", "symbol",
        "instrument_token", "product", "trigger_price", "close_price", "qty", "trend", "is_open", "created_at",
         "closed_at" ).annotate(points=Cast(F("close_price")-F("trigger_price"), DecimalField(max_digits=20, decimal_places=2)), 
        trade_total = (F("points")*F("qty"))).order_by('-id')
    start = all_orders.last().closed_at.date().strftime('%Y-%m-%d')
    end = start
    if request.method == 'POST':
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
    filtered_orders =  all_order_objects.filter(closed_at__date__gte=start, closed_at__date__lte=end)
    order_df = pd.DataFrame(filtered_orders)
    PnL_Total = 0
    if not  order_df.empty:

        PnL_Total = order_df['trade_total'].sum()

    return render(request,'trade/pandltrades.html',{'orders':filtered_orders, "start_date": start, "end_date":end, "PnL":PnL_Total})



def readFeed():
    path = "E:/Eswar/Trading/TradeSetup/somefile.txt"
    feeFile = open(path, "r")
    ltt = ""
    ltd = ""
    import pytz
    import datetime
    timezone = pytz.timezone('Asia/Kolkata')
    starttime = datetime.datetime.strptime('00:00', '%H:%M').time()
   

    minuteData = {}
    import ipdb ; ipdb.set_trace()
    for line in feeFile:
        data = json.loads(line)
        from datetime import datetime
        timestamp = data['feeds']['NSE_INDEX|Nifty Bank']['ff']['indexFF']['ltpc']['ltt']       
        dt_object = datetime.fromtimestamp(int(timestamp)/1000, tz=timezone)
        tradeDate = dt_object.date().strftime('%Y-%m-%d')
        tradeTime = dt_object.time().strftime('%H:%M')
        ohlc = data['feeds']['NSE_INDEX|Nifty Bank']['ff']['indexFF']['marketOHLC']['ohlc']
       
    
        if starttime == tradeTime:            
            minuteData['thigh']  = ohlc[2]['high'] if ohlc[2]['high'] > minuteData['thigh'] else minuteData['thigh']
            minuteData['tlow']  = ohlc[2]['low']  if ohlc[2]['low'] < minuteData['tlow'] else minuteData['tlow']
            
        else:
            starttime = tradeTime   
            minuteData = {
                              
                "thigh": ohlc[2]['high'],
                "tlow": ohlc[2]['low']                
            }
        minuteData["topen"]  = ohlc[2]['open'] 
        minuteData["tclos"]  = ohlc[2]['close']    
      
        LiveFeedData.objects.update_or_create(symbol="BANKNIFTY",
            tradedate=tradeDate, tradetime=tradeTime, instrumentKey='NSE_INDEX|Nifty Bank',
            defaults={**minuteData}
        )
                  
       

    feeFile.close()

