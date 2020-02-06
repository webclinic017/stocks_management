from django.shortcuts import render, HttpResponse

import threading
import socket


'''
Docs:
EClient: https://interactivebrokers.github.io/tws-api/classIBApi_1_1EClient.html
Ewrapper: https://interactivebrokers.github.io/tws-api/interfaceIBApi_1_1EWrapper.html
Market Data: https://interactivebrokers.github.io/tws-api/top_data.html
Cancel MKT data: https://interactivebrokers.github.io/tws-api/md_cancel.html


Flow:
0) Get/update the list of stocks to display
1) start reqMktData for the list of stocks
2) Collect the data from an API to a buffer (DF)
3) Store the last received values into a temporary variable
4) Display the values from the temp var onto the webpage.
5) Send the values to the calculators of the indicators
-) Stop the stream when disconnected

'''
from time import sleep

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.ticktype import TickTypeEnum
from ibapi.utils import iswrapper #just for decorator

from threading import Timer
from background_task import background

from ib_insync import *

from rest_framework import viewsets
from .api import *

stock_dick = dict()


def stock_data_api(request):

    context = {
        'items': stock_dick.items()
    }
    return render(request, 'ib_api/stock_data_api.html', context)


STOP_API = 'stop'
UPADATE_STOCKS = 'update'
RUN_API = 'run'

def stock_data(request):
    context = {}
    add_stock = []
    if request.method == 'POST':

        # action = 'update'
        if 'start_api' in request.POST:
            action = RUN_API
        else:
            action = UPADATE_STOCKS
            add_stock.append(request.POST.get("stock_ticker"))

        
        background_view(
            request=request, 
            stock_list=add_stock, 
            action=action)

    
    return render(request, 'ib_api/stock_data.html')


class myThread (threading.Thread):
   def __init__(self, app, threadID, name):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.app = app

   def run(self):
      print ("Starting application in separate thread:", self.name,     "threadID:", self.threadID  )
      self.app.run()
      print ("Exiting " + self.name)


class TestApp(EClient, EWrapper):
        
    def __init__(self):
        EClient.__init__(self, self)
        self.reqStatus = {}     # semaphore of requests - status End will indicate request is finished
    
    @iswrapper
    def error(self, reqId, errorCode, errorString):
        print("Error: ", reqId, " ", errorCode, " ", errorString)

    @iswrapper
    def tickPrice(self, reqId, tickType, price, attrib):
        print("Ticker Price Data:  Ticket ID: ", reqId, " ","tickType: ", TickTypeEnum.to_str(tickType), "Price: ", price, end=" ")

        stock_dick[reqId] = price
    
    @iswrapper
    def tickSize(self, reqId, tickType, size):
        print("Ticket ID: ", reqId, " ","tickType: ", TickTypeEnum.to_str(tickType), "Size: ", size)

    @iswrapper
    def stop(self):
        print('Stopping APP...')
        self.done = True
        self.disconnect

# Connecting the TWS, retreive data


contract = Contract()
app = TestApp()

def ib_stock_api(stocks, action): 

    if action == RUN_API:
        print(f"*************** START API RUN ****************")
        global app
        app = TestApp()
        
        app.connect("127.0.0.1", 4004, clientId=0)
        # app.connect("127.0.0.1", 7497, clientId=17)


        thread1App = myThread(app, 1, "T1") # define thread for running app
        thread1App.start()  # start app.run(] as infitnite loop in separate thread
    
    elif action == UPADATE_STOCKS:
        
        global contract

        for c in range(len(stocks)):
            app.cancelMktData(c)

        contract = Contract()

        rStatus = 200

        for i in range(len(stocks)):
            contract.symbol = stocks[i]
            print(f"*************** UPDATE: {stocks[i]} ****************")
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"
            contract.primaryExchange = "NASDAQ"


            app.reqStatus[rStatus] = 'Sent'
            app.reqMktData(i, contract, "", False, False, [])


        # app.done = True             # this stops app.run() loop

        return
    
    elif action == STOP_API:
        print(f"***************Stopping app****************")
        app.stop()
        # app.disconnect()

        return


    else:
        print('ERROR: Wrong action entered.')
        return

def background_view(request, stock_list=['AAPL'], action=RUN_API):
    # ib_stock_api('EUR.USD', 0, True)

    ib_stock_api(stock_list, action)
    print(f"***************BACK IN BG ****************")
    return render(request, 'ib_api/bg.html')
