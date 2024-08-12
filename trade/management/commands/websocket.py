from django.core.management.base import BaseCommand, CommandError
import requests
from trade.endpoints import CREDS, HEADERS, TOKEN, UPSTOX_AUTHORISE
from trade.models import  LiveFeedData, UpstoxUser
import os, zipfile, glob
import time
from django.conf import settings
import asyncio
import json
import ssl
import upstox_client
import websockets
from google.protobuf.json_format import MessageToDict
import datetime
from  trade import MarketDataFeed_pb2 as pb
import pytz
from trade.utils import getToken
from asgiref.sync import sync_to_async

@sync_to_async
def get_token():
    trader = UpstoxUser.objects.get(mobile=8977810371)
    return trader.upstox_token

@sync_to_async
def readFeed(data):
    import pytz
    from datetime import datetime
    timezone = pytz.timezone('Asia/Kolkata')
    starttime = datetime.strptime('00:00', '%H:%M').time()
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
    
    
    return tradeTime




def get_market_data_feed_authorize(api_version, configuration):
    """Get authorization for market data feed."""
    

    api_instance = upstox_client.WebsocketApi(
        upstox_client.ApiClient(configuration))
    api_response = api_instance.get_market_data_feed_authorize(api_version)
    return api_response



def decode_protobuf(buffer):
    """Decode protobuf message."""
    feed_response = pb.FeedResponse()
    feed_response.ParseFromString(buffer)
    return feed_response

class Command(BaseCommand):
    help = "Web socket"

    def handle(self, *args, **options):
        async def fetch_market_data():
            """Fetch market data using WebSocket and print it."""

            # Create default SSL context
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            # Configure OAuth2 access token for authorization
            configuration = upstox_client.Configuration()
            
            api_version = '2.0'
           
            fyer_token = await get_token()

            configuration.access_token = fyer_token
            
            # Get market data feed authorization
            response = get_market_data_feed_authorize(
                api_version, configuration)

            # Connect to the WebSocket with SSL context
            async with websockets.connect(response.data.authorized_redirect_uri, ssl=ssl_context) as websocket:
                print('Connection established')
                await asyncio.sleep(1)  # Wait for 1 second
               
              
                # Data to be sent over the WebSocket
                data = {
                    "guid": "someguid",
                    "method": "sub",
                    "data": {
                        "mode": "full",
                        # "instrumentKeys": ["NSE_INDEX|Nifty Bank", "NSE_INDEX|Nifty 50"]
                        "instrumentKeys": ["NSE_INDEX|Nifty Bank"]

                    }
                }

                # Convert data to binary and send over WebSocket
                binary_data = json.dumps(data).encode('utf-8')
                await websocket.send(binary_data)
                runing = True
                # Continuously receive and decode data from WebSocket
                while runing :
                    
                    message = await websocket.recv()
                    decoded_data = decode_protobuf(message)

                    # Convert the decoded data to a dictionary
                    data_dict = MessageToDict(decoded_data)
                  
                    tradeTime = await readFeed(data_dict)
                    print(tradeTime)
                    if tradeTime == '15:30':
                        runing = False
                    # Print the dictionary representationP
                    # print(json.dumps(data_dict), datetime.datetime.now())
                    # with open('somefile.txt', 'a') as the_file:
                    #     the_file.write(json.dumps(data_dict) + "\n")
                    # currenttime = datetime.datetime.now().time()
                    # timestamp = data['feeds']['NSE_INDEX|Nifty Bank']['ff']['indexFF']['ltpc']['ltt']
                    # dt_object = datetime.datetime.fromtimestamp(int(timestamp)/1000, tz=timezone)
                    # tradeDate = dt_object.date().strftime('%Y-%m-%d')
                    # tradeTime = dt_object.time().strftime('%H:%M')
                    # ohlc = data['feeds']['NSE_INDEX|Nifty Bank']['ff']['indexFF']['marketOHLC']['ohlc']
                    # high, low = 0,0
                    # topen = ohlc[1]['open'] 
                    
                    # high = ohlc[1]['high'] #if ohlc[1]['high'] > high else high
                    # low = ohlc[1]['low'] #if ohlc[1]['low'] < low else low
                    # tclose = ohlc[1]['close']

                    # tradeData = {
                    # 'DATE': tradeDate,
                    # "TIME": tradeTime,
                    # "OPEN": topen,
                    # "HIGH": high,
                    # "LOW": low,
                    # "CLOSE": tclose,
                    

                    # }
                    # print(tradeData)
                    # Print the dictionary representation
                    # with open('somefile.txt', 'a') as the_file:
                    #     print(json.dumps(data_dict), datetime.datetime.now())
                    #     the_file.write(json.dumps(data_dict) + '\n')

        asyncio.run(fetch_market_data())
       