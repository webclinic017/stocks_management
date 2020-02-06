from django.shortcuts import render, HttpResponse

'''
Docs:
EClient: https://interactivebrokers.github.io/tws-api/classIBApi_1_1EClient.html
Ewrapper: https://interactivebrokers.github.io/tws-api/interfaceIBApi_1_1EWrapper.html
Market Data: https://interactivebrokers.github.io/tws-api/top_data.html
Cancel MKT data: https://interactivebrokers.github.io/tws-api/md_cancel.html


Flow:
0) Get/update the list of stocks to display 

RESTART API/THREAD EACH STOCKS LIST UPDATE!!!

1) start reqMktData for the list of stocks
2) Collect the data from an API to a buffer (DF)
3) Store the last received values into a temporary variable
4) Display the values from the temp var onto the webpage.
5) Send the values to the calculators of the indicators
-) Stop the stream when disconnected

'''
import threading

from time import sleep

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.ticktype import TickTypeEnum

from threading import Timer
from background_task import background

from ib_insync import *

from rest_framework import viewsets
from .api import *
from .models import StockList

stock_price = []
stock_ticker = []


def stock_data_api(request):
    context = {}
 
    stocks_list = StockList.objects.last()
    print(f"***************{stocks_list}****************")

    # context = {
    #     'tickers': stock_ticker,
    #     'prices': stock_price
    # }
    # context['stocks'] = stocks
    StockList.objects.all().delete()

    return render(request, 'ib_api/stock_data_api.html', context)


def stock_data(request):
    context = {}
    return render(request, 'ib_api/stock_data.html', context)

class TestApp(EClient, EWrapper):
        
    def __init__(self):
        EClient.__init__(self, self)        
        self.reqId = None
        self.price = None
    
    def error(self, reqId, errorCode, errorString):
        print("Error: ", reqId, " ", errorCode, " ", errorString)

    def tickPrice(self, reqId, tickType, price, attrib):
        print("Ticker Price Data:  Ticket ID: ", reqId, " ","tickType: ", TickTypeEnum.to_str(tickType), "Price: ", price, end=" ")        
        self.reqId = reqId
        self.price = price
        # stock_list = StockList()

        # stock_list.stock_symbol = reqId
        # stock_list.stock_price = price
        # stock_list.save()

        # tmp_price = []
        # tmp_price.append(price)
        
        # global stock_price
        # stock_price = tmp_price

        # tmp_ticker = []
        # tmp_ticker.append(reqId)
        
        # global stock_ticker
        # stock_ticker = tmp_ticker

    def tickSize(self, reqId, tickType, size):
        print("Ticket ID: ", reqId, " ","tickType: ", TickTypeEnum.to_str(tickType), "Size: ", size)

    # def historicalData(self, reqId, bar):
    #     print("Historical Data:  Ticket ID: ", reqId, " Date: ", bar.date, " Open: ", bar.open, " Close: ", bar.close)          
    

    # def stop(self):
    #     self.done = True
    #     self.disconnect

# Connecting the TWS, retreive data

def ib_stock_api(stocks, stock_index): 
    # app.connect("127.0.0.1", 4004, clientId=0) # REAL ACCOUNT

    # TEST 1
    app = TestApp()
    # app.connect("127.0.0.1", 7497, clientId=17)
    app.connect("127.0.0.1", 4004, clientId=0) # REAL ACCOUNT

    # TEST 2
    # app = TestApp1("127.0.0.1", 7497, 17)

    contract = Contract()

    for i in range(len(stocks)):
        contract.symbol = stocks[i]
        # contract.symbol = stock
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract.primaryExchange = "NASDAQ"

        # resolved_ibcontract = app.resolve_ib_contract(contract)

        # print(f"*************** Start Stream {stocks[i]} ****************")
        # tickerid = app.start_getting_IB_market_data(resolved_ibcontract, i)

        # time.sleep(5)

        # print(f"*************** Get data {stocks[i]}****************")
        # market_data1 = app.get_IB_market_data(tickerid)
        # print(market_data1)

        app.reqMarketDataType(4)
        app.reqMktData(i, contract, "", False, False, [])



    t = threading.Thread(target=lambda app: worker(app), args=([app]))
    t.start()
    app.run()
    reqId = app.reqId
    price = app.price
    print(f'kaka and pipi {reqId} {price}')
    

def worker(app: TestApp):
    """thread worker function"""
    print('Waiting')
    time.sleep(10)      
    print('Done Waiting')
    app.disconnect()
    # FOREX
    # contract.symbol = 'EUR'
    # contract.secType = "CASH"
    # contract.exchange = "IDEALPRO"
    # contract.currency = "USD"

    # app.reqMarketDataType(4)
    # app.reqMktData(0, contract, "", False, False, [])

    # # Timer(12, app.stop).start()
    # app.run()



    # TEST 2
    # contract.symbol = 'AAPL'
    # contract.secType = "STK"
    # contract.exchange = "SMART"
    # contract.currency = "USD"
    # contract.primaryExchange = "NASDAQ"


    # resolved_ibcontract = app.resolve_ib_contract(contract)

    # print(f"*************** Start Stream ****************")
    # tickerid = app.start_getting_IB_market_data(resolved_ibcontract)

    # time.sleep(5)

    # print(f"*************** Get data ****************")
    # market_data1 = app.get_IB_market_data(tickerid)
    # print(market_data1)

    # print(f"*************** Stop stream ****************")
    # market_data2 = app.stop_getting_IB_market_data(tickerid)

    # print(f"*************** Disconnect ****************")
    # app.disconnect()


@background(schedule=5)
def hello():
	print("Hello World!!!!!!")


def background_view(request):
    # hello()
    # stam()
    # ib_stock_api('EUR.USD', 0, True)
    ib_stock_api(['AAPL', 'GE', 'INTC'], 0)
    # streaming('AAPL')
    # check()
    # return HttpResponse('Hey there')

def cancel_data(request):
    # cancel_stock = TestApp()
    wrapper = EWrapper()
    cancel_data  =EClient(wrapper)
    cancel_data.disconnect()
    return render(request, 'ib_api/cancel_data.html')
    # cancel_stock.cancelMktData(0)
