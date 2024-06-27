from fyers_api import fyersModel
import os
import threading
from tokens import *
from data import *


def revathi():
	
	revathi_data = {
    "symbol":instrument1,
    "qty":revathi_qty,
    "type":ordertype1,
    "side":decision1,
    "productType":segment1,
    "limitPrice":price1,
    "stopPrice":0,
    "validity":"DAY",
    "disclosedQty":0,
    "offlineOrder":amo,
    "orderTag":"tag1"
	}
	
	
	
	revathi = fyersModel.FyersModel(client_id=revathi_id, token=revathi_token, log_path="")
	try:
		revathi_response = revathi.place_order(data=revathi_data)
		print(revathi_response)
	except Exception as e:
		print("Some error occured in revathi account:", e)


def sita():
	
	sita_data = {
    "symbol":instrument1,
    "qty":sita_qty,
    "type":ordertype1,
    "side":decision1,
    "productType":segment1,
    "limitPrice":price1,
    "stopPrice":0,
    "validity":"DAY",
    "disclosedQty":0,
    "offlineOrder":amo,
    "orderTag":"tag1"
	}

	sita = fyersModel.FyersModel(client_id=sita_id, token=sita_token, log_path="")
	try:
		sita_response = sita.place_order(data=sita_data)
		print(sita_response)
	except Exception as e:
		print("Some error occured in sita account:", e)

def eshwar():
	
	eshwar_data = {
    "symbol":instrument1,
    "qty":eshwar_qty,
    "type":ordertype1,
    "side":decision1,
    "productType":segment1,
    "limitPrice":price1,
    "stopPrice":0,
    "validity":"DAY",
    "disclosedQty":0,
    "offlineOrder":amo,
    "orderTag":"tag1"
	}
	
	eshwar = fyersModel.FyersModel(client_id=eshwar_id, token=eshwar_token, log_path="")
	try:
		eshwar_response = eshwar.place_order(data=eshwar_data)
		print(eshwar_response)
	except Exception as e:
		print("Some error occured in eshwar account:", e)

def kanaka():

	kanaka_data = {
    "symbol":instrument1,
    "qty":kanaka_qty,
    "type":ordertype1,
    "side":decision1,
    "productType":segment1,
    "limitPrice":price1,
    "stopPrice":0,
    "validity":"DAY",
    "disclosedQty":0,
    "offlineOrder":amo,
    "orderTag":"tag1"
	}
	
	kanaka = fyersModel.FyersModel(client_id=kanaka_id, token=kanaka_token, log_path="")
	try:
		kanaka_response = kanaka.place_order(data=kanaka_data)
		print(kanaka_response)
	except Exception as e:
		print("Some error occured in kanaka durga account:", e)


def dinesh():

	dinesh_data = {
    "symbol":instrument1,
    "qty":dinesh_qty,
    "type":ordertype1,
    "side":decision1,
    "productType":segment1,
    "limitPrice":price1,
    "stopPrice":0,
    "validity":"DAY",
    "disclosedQty":0,
    "offlineOrder":amo,
    "orderTag":"tag1"
	}
	
	dinesh = fyersModel.FyersModel(client_id=dinesh_id, token=dinesh_token, log_path="")
	try:
		dinesh_response = dinesh.place_order(data=dinesh_data)
		print(dinesh_response)
	except Exception as e:
		print("Some error occured in Dinesh Shravan account:", e)

def kiran():

	kiran_data = {
    "symbol":instrument1,
    "qty":kiran_qty,
    "type":ordertype1,
    "side":decision1,
    "productType":segment1,
    "limitPrice":price1,
    "stopPrice":0,
    "validity":"DAY",
    "disclosedQty":0,
    "offlineOrder":amo,
    "orderTag":"tag1"
	}
	
	kiran = fyersModel.FyersModel(client_id=kiran_id, token=kiran_token, log_path="")
	try:
		kiran_response = kiran.place_order(data=kiran_data)
		print(kiran_response)
	except Exception as e:
		print("Some error occured in kiran account:", e)


def srinivas():

	srinivas_data = {
    "symbol":instrument1,
    "qty":srinivas_qty,
    "type":ordertype1,
    "side":decision1,
    "productType":segment1,
    "limitPrice":price1,
    "stopPrice":0,
    "validity":"DAY",
    "disclosedQty":0,
    "offlineOrder":amo,
    "orderTag":"tag1"
	}
	
	srinivas = fyersModel.FyersModel(client_id=srinivas_id, token=srinivas_token, log_path="")
	try:
		srinivas_response = srinivas.place_order(data=srinivas_data)
		print(srinivas_response)
	except Exception as e:
		print("Some error occured in srinivas account:", e)


#t1 = threading.Thread(target=revathi, name='t1')
t2 = threading.Thread(target=sita, name='t2')
#t3 = threading.Thread(target=eshwar, name='t3')
#t4 = threading.Thread(target=kanaka, name='t4')
t5 = threading.Thread(target=dinesh, name='t5')
t6 = threading.Thread(target=kiran, name='t6')
t7 = threading.Thread(target=srinivas, name='t7')

#t1.start()
t2.start()
#t3.start()
#t4.start()
t5.start()
t6.start()
t7.start()

#t1.join()
t2.join()
#t3.join()
#t4.join()
t5.join()
t6.join()
t7.join()