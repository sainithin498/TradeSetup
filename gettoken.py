
from __future__ import print_function
import requests
import time
from endpoints import *
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
# import sqlite3
import os
from fyers_api import fyersModel
from selenium.webdriver.chrome.options import Options

CHROMEDRIVER_PATH = '/usr/local/bin/chromedriver'
WINDOW_SIZE = "1920,1080"


def fyersToken(auth_code):

    redirect_uri= "https://myapi.fyers.in/"  ## redircet_uri you entered while creating APP.
    client_id = "ISORT89TOC-100"                       ## Client_id here refers to APP_ID of the created app
    secret_key = "OMDV0GX733"                          ## app_secret key which you got after creating the app 
    grant_type = "authorization_code"                  ## The grant_type always has to be "authorization_code"
    response_type = "code"                             ## The response_type always has to be "code"
    state = "sample"    

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

# def dbconn():
#     con = sqlite3.connect("trade.db")
#     cur = con.cursor()
#     cur.execute("CREATE TABLE tradeorders(option, orderId)")
#     cur.execute("CREATE TABLE Token(token)")

def scrappingToken(broker):
    if os.name == 'nt':
        path = 'E:/Eswar/Trading/chromedriver-win64/chromedriver.exe'
        ser = Service(path)
        driver = webdriver.Chrome(service=ser)
    else:
        ser = Service(CHROMEDRIVER_PATH)

        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
        chrome_options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(service=ser,
                                chrome_options=chrome_options
                            )
    if broker == 'upstox':
        loginUrl = UPSTOX_AUTHORISE
        driver.get(loginUrl)
        driver.find_element(By.ID, "mobileNum").send_keys('8977810371')
        
        driver.find_element(By.ID, "getOtp").click()
        time.sleep(2)

        driver.find_element(By.ID, "otpNum").send_keys('412750') ## Enter

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
        print(res)

        
        con = sqlite3.connect("trade.db")
        cur = con.cursor()
        cur.execute("""DELETE FROM Token""")
        con.commit()
        cur.execute("""
        INSERT INTO Token VALUES ('{}')""".format(res['access_token']))
        con.commit()
        con.close()
    else:
        loginUrl = FYERS_AUTHORISE 
    
        driver.get(loginUrl)
        driver.find_element(By.ID, "mobile-code").send_keys('8977810371')
        
        driver.find_element(By.ID, "mobileNumberSubmit").click()

        time.sleep(2)
       
        time.sleep(15)

        driver.find_element(By.ID, "confirmOtpSubmit").click()
        time.sleep(2)
        pinNumber = "1607"
        for index, pin in enumerate(pinNumber):
            ind = index +1
            driver.find_element(By.XPATH, "//div[@id='pin-container']/input[{}]".format(ind)).send_keys(pin)
    
        driver.find_element(By.ID, "verifyPinSubmit").click()
        time.sleep(3)

        get_url = driver.current_url
        time.sleep(1)

        print(get_url)
        auth_code = get_url.split('&')[2].split('=')[1]
        fyersToken(auth_code)


# def logout():
#     url = LOGOUT
#     response = requests.delete(url, headers=getdBToken())
#     print(response.json())
    
if __name__ == '__main__':
    # execute only if run as the entry point into the program
    scrappingToken('fyers')
    # logout()
   