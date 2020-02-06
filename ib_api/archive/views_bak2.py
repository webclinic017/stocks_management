from django.shortcuts import render, HttpResponse

import threading
import time
import pandas as pd

from ibapi import wrapper
from ibapi.client import EClient
from ibapi.utils import iswrapper #just for decorator
from ibapi.common import *
from ibapi.contract import *
from ibapi.ticktype import *
#from OrderSamples import OrderSamples
from ib_insync import *

# ib = IB()
# ib.cancelMktData()



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

class TestApp(wrapper.EWrapper, EClient):
    def __init__(self):
        wrapper.EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self.started = False
        self.nextValidOrderId = 0
        self.reqData = {}       # store data returned by requests
        self.reqStatus = {}     # semaphore of requests - status End will indicate request is finished

    @iswrapper
    def tickPrice(self, reqId, tickType, price, attrib):
        print("Ticker Price Data:  Ticket ID: ", reqId, " ","tickType: ", TickTypeEnum.to_str(tickType), "Price: ", price, end=" ")

    @iswrapper
    def tickSize(self, reqId, tickType, size):
        print("Ticket ID: ", reqId, " ","tickType: ", TickTypeEnum.to_str(tickType), "Size: ", size)

    @iswrapper
    def nextValidId(self, orderId:int):
        print("setting nextValidOrderId: %d", orderId)
        self.nextValidOrderId = orderId


    @iswrapper
    def error(self, reqId:TickerId, errorCode:int, errorString:str):
        print("Error. Id: " , reqId, " Code: " , errorCode , " Msg: " , errorString)

    @iswrapper
    # ! [contractdetails]
    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
        super().contractDetails(reqId, contractDetails)
        # store response in reqData dict, for each request several objects are appended into list
        if not reqId in self.reqData:
            self.reqData[reqId] = []
        self.reqData[reqId].append(contractDetails) # put returned data into data storage dict
        # ! [contractdetails]

    @iswrapper
    # ! [contractdetailsend]
    def contractDetailsEnd(self, reqId: int):
        super().contractDetailsEnd(reqId)
        print("ContractDetailsEnd. ", reqId, "\n")  # just info
        self.reqStatus[reqId] = 'End'               # indicates the response is ready for further processing
        # ! [contractdetailsend]


def stock_data(request):
    return render(request, 'ib_api/stock_data.html')


def stock_data_api(request):
    # print(f"*******************************")
    # print(global_data)
    # print(f"*******************************")
    global_data = {'tickers': 'bandora'} 
    return render(request, 'ib_api/stock_data_api.html', global_data)

global_data = dict()

def run_api(stocks):
    global data

    app = TestApp()
    app.connect("127.0.0.1", 4004, clientId=123)
    print("serverVersion:%s connectionTime:%s" % (app.serverVersion(),
                                            app.twsConnectionTime()))

    thread1App = myThread(app, 1, "T1")  # define thread for running app
    thread1App.start()                         # start app.run(] as infitnite loop in separate thread

    contract = Contract()

    for i in range(len(stocks)):
        contract.symbol = stocks[i]
        # contract.symbol = stock
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract.primaryExchange = "NASDAQ"
        app.reqStatus[i] = 'Sent'   # set request status to "sent to TWS"
        
        app.reqMktData(i, contract, "", False, False, [])


    i = 0
    while i < 20:  # exit loop after 60
        print(f"***************IN LOOP****************")
        i += 1
        for reqId in app.reqStatus:
            if app.reqStatus[reqId] == 'End':
                for tickPrice in app.reqData[reqId]:
                    # print("ContractDetails. ReqId:", reqId, tickPrice.price,tickPrice.reqId)
                    global_data = {
                        'tickers': reqId,
                        'prices': tickPrice.price
                    }                  
                app.reqStatus[reqId] = 'Processed'
        time.sleep(1)
    app.done = True  # this stops app.run() loop


def background_view(request):
    run_api(['AAPL', 'INTC', 'GE', 'UN', 'T'])
    return render(request, 'ib_api/bg.html')


def onPendingTickers(tickers):
    for t in tickers:
        df.loc[t.contract.symbol] = (
            t.bidSize, t.bid, t.ask, t.askSize, t.high, t.low, t.close)
        print(df)
