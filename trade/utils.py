import datetime
from trade.gettoken import fyersToken
from trade.models import TradeUser, strikepointMaster, tradeResponse
from fyers_apiv3 import fyersModel


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
    nxtDt = resDt + datetime.timedelta(7)
    if  resDt.month == nxtDt.month:
        year, month, date = resDt.year, resDt.month, str(resDt.day).rjust(2, '0')
    else:
        year, month, date = resDt.year, resDt.strftime("%b").upper(), None
    return year, month, date, week

def getexpiryValue(index, weekday=None ):
    if index == 'NIFTY':
        if not weekday:
            weekday = 3
        # qty = 25
    elif index == 'BANKNIFTY':
        if not weekday:
            weekday = 2
        # qty = 15
    elif index in  ['MIDCPNIFTY', 'BANKEX']:
        if not weekday:
            weekday = 0
    elif index == 'FINNIFTY':
        if not weekday:
            weekday = 1
    elif index == 'SENSEX':
        if not weekday:
            weekday = 4
            
    year, month, date, week = dategeneration(weekday)
    return year, month, date, week 
    

def getStrikePrice(spot, index, _type, weekday=None):
    """Using for index alerts, not for option alerts"""
    """NSE:NIFTY2292217000CE"""
 
    year, month, date, week = getexpiryValue(index, weekday)
    value, code = roundnearest(int(spot), _type)
    try:
        points = strikepointMaster.objects.get(index=index, weekday=week).trade_round_points
    except:
        points = 500
    if index in ['NIFTY', 'FINNIFTY']:
        points = points/2
    elif index == 'MIDCPNIFTY':
        points = points/4

    if _type == 'BUY':
        value -= points
    else:
        value += points
    if index in ['NIFTY', 'FINNIFTY']:
        value =  round(value / 200) * 200
    
    elif index == 'MIDCPNIFTY':
        value =  round(value / 100) * 100
    
    elif index == 'BANKNIFTY':
        value = round(value / 500) * 500
    if date:    
        strike = "NSE:" + index.upper() + str(year)[2:] + str(month) + str(date) + str(value) + code
    else:
        strike = "NSE:" + index.upper() + str(year)[2:] + month + str(value) + code
    return strike#, qty


def getToken(mobile):
    print(mobile)
    if mobile:
        trduser = TradeUser.objects.filter(mobile=mobile).last()
    else:
        trduser = TradeUser.objects.filter(is_active=True).last()
    fyer_token = trduser.fyer_token
    fyer_key = trduser.fyer_key
    return fyer_token, fyer_key



def execute(user):
    try:
        session = fyersModel.FyersModel(client_id=user.fyer_key, token=user.fyer_token)
        return user.trader_name, session.get_profile()


    except Exception as e:
        print(str(e))
        return str(e)


def findSymbol(netPositions, symbol, _side):
    exist = False
    qty = 0
    
    for pos in netPositions:
        if pos['symbol'] == symbol and pos['side'] == _side:
            exist = True
            qty = pos['netQty']
            break;
    return exist, qty
            
