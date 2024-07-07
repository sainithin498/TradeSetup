from datetime import date
import sqlite3
THISMONTH = date.today().strftime("%b").upper()
MONTHNUM = date.today().month


def getdBToken():
    con = sqlite3.connect("trade.db")
    cur = con.cursor()
    res = cur.execute("SELECT token FROM Token")
    token = res.fetchone()[0]
    con.close()
    TOKEN_HEADERS = {
            'Accept': 'application/json',
            'Authorization': 'Bearer {}'.format(token)
        }

    return TOKEN_HEADERS

CREDS = {
    'API_KEY' : '6b7566ef-63c0-47fb-a501-a5fd8c190ff9',
    'API_SECRET' : 'iez79urq62',
    'REDIRECT_URI' : 'https://google.com/',
    'EXCHANGES' : ['NFO', 'NSE', 'CDS', 'BSE', 'BCD', 'BFO'],
    'ORDER_TYPE' : ['MARKET', 'LIMIT', 'SL', 'SL-M'],
    'PRODUCTS' : ['OCO', 'D', 'CO', 'I'],
}


HEADERS = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }




INSTRUMENTs = 'https://assets.upstox.com/market-quote/instruments/exchange/complete.csv.gz'

BASE_URL = "https://api.upstox.com/v2"
UPSTOX_AUTHORISE = "https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id=6b7566ef-63c0-47fb-a501-a5fd8c190ff9&redirect_uri=https://google.com/"
TOKEN = BASE_URL + "/login/authorization/token"
LOGOUT = BASE_URL + '/logout'
PROFILE = BASE_URL + '/user/profile'
FUND_MARGIN = BASE_URL + '/user/get-funds-and-margin'
ORDER_HISTORY = BASE_URL + '/order/history'
TRADE_BOOK = BASE_URL + '/order/retrieve-all'
TRADES_FOR_DAY = BASE_URL + '/order/trades/get-trades-for-day'
POSITIONS = BASE_URL + '/portfolio/short-term-positions'
PLACE_ORDER = BASE_URL + '/order/place'
ORDER_DETAILS = BASE_URL + '/order/details'
BROKERAGE = BASE_URL + '/charges/brokerage'
EXITORDER = BASE_URL + '/order/cancel'



