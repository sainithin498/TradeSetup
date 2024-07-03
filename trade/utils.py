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
    
    year, month, date = resDt.year, resDt.month, str(resDt.day).rjust(2, '0')
    return year, month, date, week

def getStrikePrice(spot, index, _type):
    """Using for index alerts, not for option alerts"""
    """NSE:NIFTY2292217000CE"""
    if index == 'NIFTY':
        weekday = 3
        # qty = 25
    elif index == 'BANKNIFTY':
        weekday = 2
        # qty = 15
    year, month, date, week = dategeneration(weekday)
    value, code = roundnearest(int(spot), _type)
    print(value)
    try:
        points = strikepointMaster.objects.get(index=index, weekday=week).trade_round_points

    except:
        points = 500
    if _type == 'BUY':
        value -= points
    else:
        value += points
    # value - 51400%500 +500
    # round(value / 500) * 500
    strike = "NSE:" + index.upper() + str(year)[2:] + str(month) + str(date)+ str(value) + code
    # strike = "NSE:" + index.upper() + str(year)[2:] + "JUN"+ str(value) + code
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
            
