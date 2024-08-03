from django.core.management.base import BaseCommand, CommandError
import requests
from trade.endpoints import CREDS, HEADERS, TOKEN, UPSTOX_AUTHORISE
from trade.models import TradeUser, UpstoxUser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import os, zipfile, glob
import time
from django.conf import settings
import gzip, shutil, tarfile

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

class Command(BaseCommand):
    help = "Get the instruments"

   

    def handle(self, *args, **options):
        download_dir = settings.BASE_DIR
        instrument = os.path.join(download_dir, 'instrument/')
        # path = 'E:/Eswar/Trading/chromedriver-win64/chromedriver.exe'
        # ser = Service(path)
        # # driver = webdriver.Chrome(service=ser)

        # upstoxurl = "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"
        # # driver.get(upstoxurl)
        # chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument("--headless")
        # chrome_options.add_argument('--no-sandbox')
        # preferences = {
        #             "download.default_directory": instrument ,
        #             "directory_upgrade": False,
        #             "safebrowsing.enabled": False }
        # chrome_options.add_experimental_option("prefs", preferences)
        # driver = webdriver.Chrome(service=ser, options=chrome_options)
        # driver.get(upstoxurl)
        # time.sleep(5)
        zip_files = glob.glob(os.path.join(instrument, '*.gz'))        
        zip_files.sort(key=os.path.getmtime, reverse=True)
        import ipdb ; ipdb.set_trace()

        for name in zip_files:
            print(name)
            tf = tarfile.open(name)
            tf.extractall(instrument)
            print('-- Done') 
        # file =  zip_files[0]
        # unzip_file(file, instrument)


  
        
