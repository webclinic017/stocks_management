from django.shortcuts import render, HttpResponse

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

from threading import Timer
from background_task import background

from ib_insync import *

from rest_framework import viewsets
from .api import *

# stock_price = []
# stock_ticker = []
stock_dick = dict()


def stock_data_api(request):
    # context = {}

    # context = {
    #     'tickers': stock_ticker,
    #     'prices': stock_price
    # }
    # context['stocks'] = stocks
    context = {
        'items': stock_dick.items()
    }
    return render(request, 'ib_api/stock_data_api.html', context)


def stock_data(request):
    context = {}
    add_stock = []
    if request.method == 'POST':
        add_stock.append(request.POST.get("stock_ticker"))
        background_view(request, add_stock)

    return render(request, 'ib_api/stock_data.html', context)

class TestApp(EClient, EWrapper):
        
    def __init__(self):
        EClient.__init__(self, self)
    
    def error(self, reqId, errorCode, errorString):
        print("Error: ", reqId, " ", errorCode, " ", errorString)

    def tickPrice(self, reqId, tickType, price, attrib):
        print("Ticker Price Data:  Ticket ID: ", reqId, " ","tickType: ", TickTypeEnum.to_str(tickType), "Price: ", price, end=" ")
        # stock_streaming_data = StockStreamingData()
        # stock_streaming_data.ticker = "AAPL"
        # stock_streaming_data.price = price
        # stock_streaming_data.save()
        # global stock_price
        # stock_price.append(price)

        # global stock_ticker
        # stock_ticker.append(reqId)
        stock_dick[reqId] = price

    def tickSize(self, reqId, tickType, size):
        print("Ticket ID: ", reqId, " ","tickType: ", TickTypeEnum.to_str(tickType), "Size: ", size)
        
    # def historicalData(self, reqId, bar):
    #     print("Historical Data:  Ticket ID: ", reqId, " Date: ", bar.date, " Open: ", bar.open, " Close: ", bar.close)          
    

    def stop(self):
        self.done = True
        self.disconnect

# Connecting the TWS, retreive data

def ib_stock_api(stocks): 
    app = TestApp()
    app.connect("127.0.0.1", 4004, clientId=0)
    # app.connect("127.0.0.1", 7497, clientId=17)
    contract = Contract()

    for i in range(len(stocks)):
        contract.symbol = stocks[i]
        # contract.symbol = stock
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract.primaryExchange = "NASDAQ"
        # FOREX
        # contract.symbol = 'EUR'
        # contract.secType = "CASH"
        # contract.exchange = "IDEALPRO"
        # contract.currency = "USD"

        app.reqMarketDataType(4)
        app.reqMktData(i, contract, "", False, False, [])

        # Timer(12, app.stop).start()
    app.run()

@background(schedule=5)
def hello():
	print("Hello World!!!!!!")


def background_view(request, stock_list=['AAPL']):
    # ib_stock_api('EUR.USD', 0, True)
    ib_stock_api(stock_list)
    return render(request, 'ib_api/bg.html')


def cancel_data(request):
    # cancel_stock = TestApp()
    wrapper = EWrapper()
    cancel_data  =EClient(wrapper)
    cancel_data.disconnect()
    return render(request, 'ib_api/cancel_data.html')
    # cancel_stock.cancelMktData(0)
