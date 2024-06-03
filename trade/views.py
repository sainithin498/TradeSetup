from django.shortcuts import render
from fyers_api import fyersModel
import os
from rest_framework.decorators import api_view
from django.http import FileResponse, HttpResponse, JsonResponse
from rest_framework import parsers, renderers, serializers, status, viewsets

# Create your views here.

@api_view(["GET", "POST"])
def buyOrder(request):
    print(request.POST)
    eshwar_data = {
    "symbol":"NSE:YESBANK-EQ",
    "qty":1,
    "type":1,
    "side":1,
    "productType":"CNC",
    "limitPrice":25,
    "stopPrice":0,
    "validity":"DAY",
    "disclosedQty":0,
    "offlineOrder":True,
    "orderTag":"tag1"
    }
    
    eshwar_id = "ISORT89TOC-100"
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhcGkuZnllcnMuaW4iLCJpYXQiOjE3MTczMjYwNTUsImV4cCI6MTcxNzM3NDY1NSwibmJmIjoxNzE3MzI2MDU1LCJhdWQiOlsieDowIiwieDoxIiwieDoyIiwiZDoxIiwiZDoyIiwieDoxIiwieDowIl0sInN1YiI6ImFjY2Vzc190b2tlbiIsImF0X2hhc2giOiJnQUFBQUFCbVhGRG5WdGZ0bWRhMGpuSE94dlNMaVk0NmZfd2h6ZEJUZ19xcUV4VnFCSnIwU09odFVtTFpyV2VCSVh1QURxUWJnMnY5U0lxeThzVThjb3hrX1J1RVpiMHN6MC1BT1B0YjJnMlVyVXhRR3dsVU9zZz0iLCJkaXNwbGF5X25hbWUiOiJNQVZVUlUgRVNXQVIgUkFPIiwib21zIjoiSzEiLCJoc21fa2V5IjoiM2JhMGM3MTZhNGU4MzI3ZTdkNTcxYTZlMjY0OTc3NDM1MjYxNjEwOTdlYTEwNTRjODk0NzkzZDciLCJmeV9pZCI6IlhNMTgyNDYiLCJhcHBUeXBlIjoxMDAsInBvYV9mbGFnIjoiTiJ9.FQMypxAIr9NRptDHUVZF2eLBJwa4-ZhXwrxqx174zVY"
    eshwar = fyersModel.FyersModel(client_id=eshwar_id, token=token, log_path="")
    try:
        eshwar_response = eshwar.place_order(data=eshwar_data)
        print(eshwar_response)
    except Exception as e:
        print("Some error occured in Eshwar account:", e)
            
            
    return JsonResponse({'message':'Order placed successfully','success':True},status=status.HTTP_200_OK)

@api_view(["GET", "POST"])
def sellOrder(request):
    eshwar_data = {
    "symbol":"NSE:YESBANK-EQ",
    "qty":1,
    "type":1,
    "side":-1,
    "productType":"CNC",
    "limitPrice":25,
    "stopPrice":0,
    "validity":"DAY",
    "disclosedQty":0,
    "offlineOrder":True,
    "orderTag":"tag1"
    }
    
    eshwar_id = "ISORT89TOC-100"
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhcGkuZnllcnMuaW4iLCJpYXQiOjE3MTczMjYwNTUsImV4cCI6MTcxNzM3NDY1NSwibmJmIjoxNzE3MzI2MDU1LCJhdWQiOlsieDowIiwieDoxIiwieDoyIiwiZDoxIiwiZDoyIiwieDoxIiwieDowIl0sInN1YiI6ImFjY2Vzc190b2tlbiIsImF0X2hhc2giOiJnQUFBQUFCbVhGRG5WdGZ0bWRhMGpuSE94dlNMaVk0NmZfd2h6ZEJUZ19xcUV4VnFCSnIwU09odFVtTFpyV2VCSVh1QURxUWJnMnY5U0lxeThzVThjb3hrX1J1RVpiMHN6MC1BT1B0YjJnMlVyVXhRR3dsVU9zZz0iLCJkaXNwbGF5X25hbWUiOiJNQVZVUlUgRVNXQVIgUkFPIiwib21zIjoiSzEiLCJoc21fa2V5IjoiM2JhMGM3MTZhNGU4MzI3ZTdkNTcxYTZlMjY0OTc3NDM1MjYxNjEwOTdlYTEwNTRjODk0NzkzZDciLCJmeV9pZCI6IlhNMTgyNDYiLCJhcHBUeXBlIjoxMDAsInBvYV9mbGFnIjoiTiJ9.FQMypxAIr9NRptDHUVZF2eLBJwa4-ZhXwrxqx174zVY"
    eshwar = fyersModel.FyersModel(client_id=eshwar_id, token=token, log_path="")
    try:
        eshwar_response = eshwar.place_order(data=eshwar_data)
        print(eshwar_response)
    except Exception as e:
        print("Some error occured in Eshwar account:", e)
            
            
    return JsonResponse({'message':'Order sell successfully','success':True},status=status.HTTP_200_OK)

