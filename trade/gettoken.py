
from __future__ import print_function
import datetime
import requests
import time
from .endpoints import *
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
# import sqlite3
import os
from fyers_api import fyersModel
from fyers_apiv3 import fyersModel
from trade.models import TradeUser, UpstoxUser
from selenium.webdriver.chrome.options import Options
from celery import shared_task

CHROMEDRIVER_PATH = '/usr/local/bin/chromedriver'
WINDOW_SIZE = "1920,1080"


def fyersToken(auth_code, redirect_uri, client_id, secret_key):
    if not auth_code:
        auth_code = str(input("Enter auth code"))

    redirect_uri= redirect_uri  ## redircet_uri you entered while creating APP.
    client_id = client_id                      ## Client_id here refers to APP_ID of the created app
    secret_key = secret_key                         ## app_secret key which you got after creating the app 
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
    return response['access_token']

# @shared_task
def scrappingToken(broker, otpNum, trader_id):
    if broker == 'upstox':
        trader = UpstoxUser.objects.get(id=trader_id)
    else:
        trader = TradeUser.objects.get(id=trader_id)
    mobile = trader.mobile
    # pinNumber = trader.pin
    # client_id = trader.fyer_key
    # redirect_uri = trader.redirect_uri
    # secret_key = trader.secret_key
    print(trader)
    if os.name == 'nt':
        path = 'E:/Eswar/Trading/chromedriver-win64/chromedriver.exe'
        ser = Service(path)
        driver = webdriver.Chrome(service=ser)
    else:
        ser = Service(CHROMEDRIVER_PATH)

        chrome_options = Options()

        chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')        
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(service=ser, options=chrome_options)
    if broker == 'upstox':

        path = 'E:/Eswar/Trading/chromedriver-win64/chromedriver.exe'
        ser = Service(path)
        driver = webdriver.Chrome(service=ser)

        loginUrl = UPSTOX_AUTHORISE
        driver.get(loginUrl)

        driver.find_element(By.ID, "mobileNum").send_keys(mobile)
        time.sleep(1)
        
        driver.find_element(By.ID, "getOtp").click()
        time.sleep(1)

        driver.find_element(By.ID, "otpNum").send_keys(otpNum) ## Enter
        time.sleep(1)
        
        driver.find_element(By.ID, "continueBtn").click()
        time.sleep(2)

        driver.find_element(By.ID, "pinCode").send_keys("170916")

        driver.find_element(By.ID, "pinContinueBtn").click()
        time.sleep(5)

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
        trader.upstox_token = res['access_token']
        trader.token_date = datetime.datetime.now().date()
        trader.save()
        data = {
            'succes': True
        }


    
    else:
        FYERS_AUTHORISE = "https://api.fyers.in/api/v2/generate-authcode?client_id="+ client_id + "&redirect_uri=" +redirect_uri + "&response_type=code&state=None"
        loginUrl = FYERS_AUTHORISE 
    
        driver.get(loginUrl)
        driver.find_element(By.ID, "mobile-code").send_keys(mobile)
        time.sleep(2)
        driver.find_element(By.ID, "mobileNumberSubmit").click()

        time.sleep(2)

        if otpNum != '1':
            for index, nm in enumerate(otpNum):
                ind = index +1
                driver.find_element(By.XPATH, "//div[@id='otp-container']/input[{}]".format(ind)).send_keys(nm)
        
            time.sleep(2)
        else:
            time.sleep(15)


        driver.find_element(By.ID, "confirmOtpSubmit").click()
        time.sleep(2)
        for index, pin in enumerate(pinNumber):
            ind = index +1
            driver.find_element(By.XPATH, "//div[@id='pin-container']/input[{}]".format(ind)).send_keys(pin)
        time.sleep(1)
        driver.find_element(By.ID, "verifyPinSubmit").click()
        time.sleep(3)

        get_url = driver.current_url
        time.sleep(1)

        print(get_url)
        auth_code = get_url.split('&')[2].split('=')[1]
        token = fyersToken(auth_code, redirect_uri, client_id, secret_key )

        trader.fyer_token = token
        trader.token_date = datetime.datetime.now().date()
        trader.save()

    # return token
