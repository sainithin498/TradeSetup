from django.core.management.base import BaseCommand, CommandError
import requests
from trade.endpoints import CREDS, HEADERS, TOKEN, UPSTOX_AUTHORISE
from trade.models import TradeUser, UpstoxUser, UpstoxTradeSymbol
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import os, zipfile, glob
import time
from django.conf import settings
import gzip, shutil, tarfile
from selenium.webdriver.chrome.options import Options
import pytz
from datetime import datetime
from django.db import connection
timezone = pytz.timezone('Asia/Kolkata')


def unzip_file(zip_file_path, extract_to_path):
    if not os.path.exists(extract_to_path):
        os.makedirs(extract_to_path)
    with gzip.open(zip_file_path,"rb") as f_in, open(extract_to_path,"wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    # with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
    #     zip_ref.extractall(extract_to_path)
    
    for root, dirs, files in os.walk(extract_to_path):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o777)
        for f in files:
            os.chmod(os.path.join(root, f), 0o777)

def getDate(timestamp):
    tradeDate = None
    try:
        if timestamp:
            dt_object = datetime.fromtimestamp(int(timestamp)/1000, tz=timezone)
            tradeDate = dt_object.date().strftime('%Y-%m-%d')
    except: pass
    return tradeDate



class Command(BaseCommand):
    help = """Get the getinstruments
    /home/ubuntu/workspace/tenv/bin/python /home/ubuntu/workspace/TradeSetup/manage.py getinstruments >> /home/ubuntu/workspace/cron_logs/instruments.log 2>&1
    """

   

    def handle(self, *args, **options):
        download_dir = settings.BASE_DIR
        instrument = os.path.join(download_dir, 'instrument/')
        preferences = {
                    "download.default_directory": instrument ,
                    "directory_upgrade": False,
                    "safebrowsing.enabled": False }
        chrome_options = Options()

        chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')        
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option("prefs", preferences)

        if os.name == 'nt':
            path = 'E:/Eswar/Trading/chromedriver-win64/chromedriver.exe'
            ser = Service(path)
        else:
            
            CHROMEDRIVER_PATH = '/usr/local/bin/chromedriver'
            WINDOW_SIZE = "1920,1080"
            ser = Service(CHROMEDRIVER_PATH)


        driver = webdriver.Chrome(service=ser, options=chrome_options)
       
        upstoxurl = "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"
        driver.get(upstoxurl)
        time.sleep(5)
        driver.quit()
        zip_files = glob.glob(os.path.join(instrument, '*.gz'))        
        zip_files.sort(key=os.path.getmtime, reverse=True)
       
        for name in zip_files:
            chunk_size = 4096
            with gzip.open(name, 'rb') as f_in:
                with open(os.path.join(instrument, 'tradeData.json'), 'wb') as f_out:
                    chunk = f_in.read(chunk_size)
                    while chunk:
                        f_out.write(chunk)
                        chunk = f_in.read(chunk_size)
        
        import pandas as pd
        json_file = os.path.join(instrument, 'tradeData.json')
        df = pd.read_json(json_file)
       
        columns = ['name', 'instrument_key', 'segment', 'trading_symbol', 'expiry', 'lot_size','asset_type',
         'instrument_type', 'asset_symbol', 'strike_price']
        datadf = df[columns]
        datadf = datadf.loc[datadf['segment'].isin(['NSE_FO', 'NSE_EQ', 'BSE_FO'])]
        
        datadf = datadf.where(pd.notnull(datadf), None)
        datadf['expiry'] = datadf['expiry'].apply(lambda x: getDate(x) if x else None)
        datadf['strike_price'] = datadf['strike_price'].fillna(0)
        chunk_size = 2000
        num_chunks = len(datadf) // chunk_size + (1 if len(datadf) % chunk_size != 0 else 0)
        smaller_dataframes = [datadf.iloc[i * chunk_size:(i + 1) * chunk_size] for i in range(num_chunks)]
        print('truncating')
        cursor = connection.cursor()
        cursor.execute("""TRUNCATE TABLE trade_upstoxtradesymbol RESTART IDENTITY;""")
        cursor.close()
        connection.close()

        for i, small_df in enumerate(smaller_dataframes):         
            
            UpstoxTradeSymbol.objects.bulk_create(
                UpstoxTradeSymbol(**vals) for vals in small_df.to_dict('records')
            )
        os.remove(json_file)
        for zf in zip_files:
            os.remove(zf)
        


