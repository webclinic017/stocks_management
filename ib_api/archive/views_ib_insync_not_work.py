import time
import logging
import asyncio

from django.shortcuts import render, HttpResponse, redirect
from eventkit import Event
# from .decoder import Decoder
from ib_insync.decoder import Decoder
from ib_insync import *

import pandas as pd

def stock_data(request):
    context = {}
    return render(request, 'ib_api/stock_data.html', context)


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

class IBPoop(IB):
    def __init__(self):
        # super().__init__()
        self._createEvents()
        self.wrapper = Wrapper(self)        
        self.client = ClientPoop(self.wrapper)
        self.client.apiEnd += self.disconnectedEvent
        self._logger = logging.getLogger('ib_insync.ib')

class ClientPoop(Client):
    def __init__(self, wrapper):
        # super().__init__(wrapper)
        self.wrapper = wrapper
        self.decoder = Decoder(wrapper, None)
        self.apiStart = Event('apiStart')
        self.apiEnd = Event('apiEnd')
        self.apiError = Event('apiError')
        self.throttleStart = Event('throttleStart')
        self.throttleEnd = Event('throttleEnd')
        self._readyEvent = asyncio.Event()
        # self._loop = asyncio.get_event_loop()
        self._loop = asyncio.new_event_loop()
        self._logger = logging.getLogger('ib_insync.client')
        self.reset()

        # extra optional wrapper methods
        self._priceSizeTick = super.getattr(wrapper, 'priceSizeTick', None)
        self._tcpDataArrived = super.getattr(wrapper, 'tcpDataArrived', None)
        self._tcpDataProcessed = super.getattr(wrapper, 'tcpDataProcessed', None)

def run_api(stocks):            
    ib = IBPoop()    
    return
    # ib.connect('127.0.0.1', 7497, clientId=15)
    ib.connect('127.0.0.1', 4004, clientId=154)

    # contracts = [Forex(pair) for pair in ('EURUSD', 'USDJPY', 'GBPUSD', 'USDCHF', 'USDCAD', 'AUDUSD')]
    contracts = [Stock(symbol, 'SMART', 'USD') for symbol in stocks]
    ib.qualifyContracts(*contracts)

    for contract in contracts:
        ib.reqMktData(contract, '', False, False)


    df = pd.DataFrame(
        index=[c.symbol for c in contracts],
        columns=['bidSize', 'bid', 'ask', 'askSize', 'high', 'low', 'close'])


    ib.pendingTickersEvent += onPendingTickers
    ib.sleep(10)
    ib.pendingTickersEvent -= onPendingTickers

    for contract in contracts:
        ib.cancelMktData(contract)


def onPendingTickers(tickers):
    for t in tickers:
        df.loc[t.contract.symbol] = (
            t.bidSize, t.bid, t.ask, t.askSize, t.high, t.low, t.close)
        print(df)


def background_view(request):
    run_api(('AAPL', 'INTC', 'GE', 'UN', 'T'))    
    return render(request, 'ib_api/bg.html')