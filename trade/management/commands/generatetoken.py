from django.core.management.base import BaseCommand, CommandError
import requests
from trade.endpoints import CREDS, HEADERS, TOKEN, UPSTOX_AUTHORISE
from trade.models import TradeUser, UpstoxUser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import os
import time
from fyers_apiv3 import fyersModel
import datetime

class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def add_arguments(self, parser):
        parser.add_argument("mobile", type=str)
        parser.add_argument("broker", type=str)



    def handle(self, *args, **options):
        mobile = options.get('mobile',None)
        broker = options.get('broker', None)
        if broker == 'fyers':
            trader = TradeUser.objects.get(mobile=mobile)
            mobile = trader.mobile
            client_id = trader.fyer_key
            redirect_uri = trader.redirect_uri
            secret_key = trader.secret_key

            FYERS_AUTHORISE = "https://api.fyers.in/api/v2/generate-authcode?client_id="+ client_id + "&redirect_uri=" +redirect_uri + "&response_type=code&state=None"
            loginUrl = FYERS_AUTHORISE 
        
            print(loginUrl)
            time.sleep(15)
            auth_code = str(input("Enter auth code"))
            
            if not auth_code:
                auth_code = str(input("Enter auth code"))

            grant_type = "authorization_code"                  ## The grant_type always has to be "authorization_code"
            response_type = "code"                             ## The response_type always has to be "code"

            # Create a session object to handle the Fyers API authentication and token generation
            session = fyersModel.SessionModel(
                client_id=client_id,
                secret_key=secret_key, 
                redirect_uri=redirect_uri, 
                response_type=response_type, 
                grant_type=grant_type
            )

            # Set the authorization code in the session object
            session.set_token(auth_code)

            # Generate the access token using the authorization code
            response = session.generate_token()

            # Print the response, which should contain the access token and other details
            print(response['access_token'])

            trader.fyer_token = response['access_token']
            trader.token_date = datetime.datetime.now().date()
            trader.save()
        
        else:
            path = 'E:/Eswar/Trading/chromedriver-win64/chromedriver.exe'
            ser = Service(path)
            driver = webdriver.Chrome(service=ser)

            loginUrl = UPSTOX_AUTHORISE
            driver.get(loginUrl)

            driver.find_element(By.ID, "mobileNum").send_keys('8977810371')
            
            driver.find_element(By.ID, "getOtp").click()
            time.sleep(10)

            # driver.find_element(By.ID, "otpNum").send_keys('277627') ## Enter

            driver.find_element(By.ID, "continueBtn").click()
            time.sleep(2)

            driver.find_element(By.ID, "pinCode").send_keys('170916')

            driver.find_element(By.ID, "pinContinueBtn").click()
            time.sleep(3)

            get_url = driver.current_url
            time.sleep(1)

            print("The current url is:"+str(get_url))
            CODE = get_url.split('=')[1]
            driver.quit()

            url = TOKEN
            data = {
                'code': CODE,
                'client_id': CREDS['API_KEY'],
                'client_secret': CREDS['API_SECRET'],
                'redirect_uri': CREDS['REDIRECT_URI'],
                'grant_type': 'authorization_code',
            }

            response = requests.post(url, headers=HEADERS, data=data)
            res = response.json()
            print(res['access_token'])
            trader = UpstoxUser.objects.get(mobile=mobile)
            trader.upstox_token = res['access_token']
            trader.token_date = datetime.datetime.now().date()
            trader.save()
            
            
    