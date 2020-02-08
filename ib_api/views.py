from django.shortcuts import render, HttpResponse

import threading
import json
from time import sleep

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.ticktype import TickTypeEnum
from ibapi.utils import iswrapper #just for decorator

from threading import Timer

from kadima.models import StockData
# Create and configure logger
import logging
LOG_FORMAT = '%(levelname)s %(asctime)s - %(message)s'
logging.basicConfig(filename='./log.log',level=logging.INFO,format=LOG_FORMAT, filemode='w')
logger = logging.getLogger()

stock_dick = dict()
connection_status = False

def api_connection_status():
    return connection_status

def indeces_data(request):
    context = {
        'dow_value': stock_dick[77777], 
        'snp_value': stock_dick[88888],
        # 'nsq_value': stock_dick[55555],
        'connection_stattus': connection_status
    }
    return render(request, 'ib_api/indeces.html', context)


def stock_data_api(request):

    stocks_db = StockData.objects.filter(table_index=0)

    stocks_db_dict = {}
    # for i in range(len(stocks_db)):
    for stock in stocks_db:
        stocks_db_dict[stock.id] = {
            'ticker': stock.ticker,
            'stock_price': stock_dick[stock.id],
            'table_index': stock.table_index,
            'stock_date': stock.stock_date,
            'stock_displayed_date': stock.stock_displayed_date,
            'stock_trend':   stock.stock_trend, 
            'macd_trend':  stock.macd_trend, 
            'money_flow_trend':  stock.money_flow_trend,
            'week_1': stock.week_1,
            'week_2': stock.week_2,
            'week_3': stock.week_3,
            'week_5': stock.week_5,
            'week_1_color': stock.week_1_color,
            'week_2_color': stock.week_2_color,
            'week_3_color': stock.week_3_color,
            'week_5_color': stock.week_5_color,
            'gap_1': stock.gap_1,
            'gap_2': stock.gap_2,
            'gap_3': stock.gap_3,
            'gap_1_color': stock.gap_1_color,
            'gap_2_color': stock.gap_2_color,
            'gap_3_color': stock.gap_3_color,
            'earnings_call': stock.earnings_call,
            'earnings_call_displayed': stock.earnings_call_displayed,
            'earnings_warning': stock.earnings_warning,
            'macd_clash': stock.macd_clash,
            'mfi_clash': stock.mfi_clash,
            'macd_color': stock.macd_color,
            'mfi_color': stock.mfi_color
        }

    context = {
        # 'stocks_streaming': stock_dick.items(), 
        'dow_value': stock_dick[77777], 
        'snp_value': stock_dick[88888],
        # 'nsq_value': stock_dick[55555],
        'connection_stattus': connection_status,
        'stocks_processed': stocks_db_dict.items()
    }

    print(f'CONNECTION STATUS: {connection_status}')
    # with open('ib_api/stocks_data.json', 'w+') as fd:
    #     json.dump(stock_dick, fd)


    return render(request, 'ib_api/stock_data_api.html', context)


STOP_API = 'stop'
UPADATE_STOCKS = 'update'
RUN_API = 'run'

def streaming_stock_data(request, stocks_list=['AAPL']):
    context = {}
    add_stock = []
    if request.method == 'POST':

        if 'start_api' in request.POST:
            action = RUN_API
        else:
            action = UPADATE_STOCKS
            # stocks_arr = request.POST.get("stock_ticker").split(',')
            # for s in stocks_arr:
            #     add_stock.append(s.strip())
            add_stock.append(request.POST.get("stock_ticker"))

         
        ib_api_wrapper(
            request=request, 
            stock_list=stocks_list, 
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
    def isConnected(self):
        """Call this function to check if there is a connection with TWS"""

        connConnected = self.conn and self.conn.isConnected()
        logger.debug("%s isConn: %s, connConnected: %s" % (id(self),
            self.connState, str(connConnected)))
        
        global connection_status
        connection_status = connConnected

        return EClient.CONNECTED == self.connState and connConnected

    @iswrapper
    def stop(self):
        print('Stopping APP...')
        self.done = True
        self.disconnect

# Connecting the TWS, retreive data


contract = Contract()
app = TestApp()

def ib_stock_api(old_stocks_list, stocks, action): 

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

        # for c in range(len(stocks)):
        for stock_id in old_stocks_list:
            print(f"STOPPING: ***************{stock_id}****************")
            app.cancelMktData(stock_id)

        print(f"*************** Loading Indeces... ****************")

        contract.symbol = "NDX"
        contract.secType = "IND"
        contract.currency = "USD"
        contract.exchange = "NASDAQ"
        app.reqMktData(55555, contract, "", False, False, [])

        contract.symbol = "SPX"
        contract.secType = "IND"
        contract.currency = "USD"
        contract.exchange = "CBOE"
        app.reqMktData(88888, contract, "", False, False, [])

        contract.symbol = "DJX"
        contract.secType = "IND"
        contract.currency = "USD"
        contract.exchange = "CBOE"
        app.reqMktData(77777, contract, "", False, False, [])

        sleep(2)

        rStatus = 200

        for stock_id, symbol in stocks.items():
            print(f"UPDATING: *************** {symbol}: {stock_id} ****************")
            contract.symbol = symbol
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"
            contract.primaryExchange = "NASDAQ"


            app.reqStatus[rStatus] = 'Sent'
            app.reqMktData(stock_id, contract, "", False, False, [])


        # for i in range(len(stocks)):
        #     contract.symbol = stocks[i]
        #     contract.secType = "STK"
        #     contract.exchange = "SMART"
        #     contract.currency = "USD"
        #     contract.primaryExchange = "NASDAQ"

        return
    
    elif action == STOP_API:
        print(f"***************Stopping app****************")
        # app.stop()
        app.disconnect()

        return


    else:
        print('ERROR: Wrong action entered.')
        return

def ib_api_wrapper(request, old_stocks_list=[], updated_stock_list=['AAPL'], action=RUN_API):

    ib_stock_api(old_stocks_list, updated_stock_list, action)

    return render(request, 'ib_api/bg.html')

