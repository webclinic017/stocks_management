import datetime
from datetime import timedelta
from pandas_datareader import data as fin_data

import threading
import json
from time import sleep

from django.shortcuts import render, HttpResponse
from django.conf import settings

# import ibapi

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.ticktype import TickTypeEnum
from ibapi.utils import iswrapper #just for decorator
from django.contrib import messages

from threading import Timer

from kadima.models import StockData, IndicesData
from kadima.k_utils import week_color, change_check

# Create and configure logger
import logging
LOG_FORMAT = '%(levelname)s %(asctime)s - %(message)s'
logging.basicConfig(filename='./views_ib_api.log',level=logging.INFO,format=LOG_FORMAT, filemode='w')
logger = logging.getLogger()

TODAY = datetime.datetime.today()


stock_dick = dict()
connection_status = False


def trading_status():
    if -1.0 in stock_dick.values():
        return False
    else:
        return True

def api_connection_status():
    return connection_status

def alarm_trigger(request):
    context = {}
    stocks_in_alarm = StockData.objects.filter(stock_alarm_trigger_set=True)
    
    for stock in stocks_in_alarm:

        if stock.stock_price_up_alarm:
            messages.success(request, f'UP TRIGGER: {stock.ticker}')

            if stock.stock_alarm_sound_on_off:
                pass
            else:
                context['play_sound'] = 'up'
                stock.stock_alarm_sound_on_off = True
                stock.save()
        
        elif stock.stock_price_down_alarm:
            messages.warning(request, f'DOWN TRIGGER: {stock.ticker}')

            if stock.stock_alarm_sound_on_off:
                pass
            else:
                context['play_sound'] = 'down'
                stock.stock_alarm_sound_on_off = True
                stock.save()
        
        else:
            pass
    
    return render(request,'kadima/alarm_trigger.html', context)


def stock_alarms_data(request):
    context = {}
    saved_alarms_stocks = StockData.objects.filter(stock_alarm=True)
    
    price_up = False
    price_down = False

    stocks_db_alarms_dict = {}
    stocks_db_dict_list = []

    for stock in saved_alarms_stocks:
        
        try:
            week3, w3_color = week_check(stock.week_3_min, stock.week_3_max, stock_dick[stock.id], week3=True)

            # Checking alarm trigger
            trigger_alarm_set = stock.stock_alarm_trigger_set
            alarm_delta = stock.stock_alarm_delta
            initial_stock_price = stock.stock_initial_price
            current_stock_price = stock_dick[stock.id]

            if trigger_alarm_set:

                if current_stock_price > (initial_stock_price + alarm_delta):
                    
                    price_up = True
                    stock.stock_price_up_alarm = True
                    stock.save()

                    price_down = False

                elif current_stock_price < (initial_stock_price - alarm_delta):
                    price_up = False

                    price_down = True
                    stock.stock_price_down_alarm = True
                    stock.save()

            else:
                price_up = False
                price_down = False
            
            

            stocks_db_alarms_dict[stock.id] = {
                'stock_id': stock.id,
                'ticker': stock.ticker,
                'stock_initial_price' : stock.stock_initial_price,
                'stock_price': stock_dick[stock.id],
                'stock_date': stock.stock_date,
                'stock_displayed_date': stock.stock_displayed_date,
                'week_3': week3,
                'week_3_color': w3_color,
                'gap_1': stock.gap_1,
                'gap_1_color': stock.gap_1_color,
                'stock_alarm_trigger_set': trigger_alarm_set,
                'stock_alarm_delta': alarm_delta,
                'price_up': price_up,
                'price_down': price_down
            }

            stocks_db_dict_list.append(stocks_db_alarms_dict[stock.id])
        except Exception as e:
            print(f'ERROR: Failed loading stock: {stock} to alarm list. Reason: {e}')

    context = {
        # 'stocks_streaming': stock_dick.items(), 
        'ib_api_connected': connection_status,
        'stocks_processed': stocks_db_dict_list
    }

    print(f'CONNECTION STATUS: {connection_status}')
    # with open('ib_api/stocks_data.json', 'w+') as fd:
    #     json.dump(stock_dick, fd)


    return render(request, 'ib_api/stock_alarms_streaming.html', context)

def indeces_data(request):

    snp = IndicesData.objects.get(index_api_id=88888)

    try:
        if stock_dick[88888] > 0:
            snp.index_current_value = stock_dick[88888]
            snp.save()
            snp_current_value = stock_dick[88888]
        elif snp.index_current_value:
            snp_current_value = snp.index_current_value
        else:
            snp.index_current_value = snp.index_prev_close
            snp_current_value = snp.index_prev_close
            snp.save()
    except Exception as e:
        snp_current_value = -1.0
        pass

    dow_close = IndicesData.objects.get(index_api_id=77777).index_prev_close

    snp_close = IndicesData.objects.get(index_api_id=88888).index_prev_close

    nas_close = IndicesData.objects.get(index_api_id=55555).index_prev_close

    vix_close = IndicesData.objects.get(index_api_id=11111).index_prev_close

    r2k_close = IndicesData.objects.get(index_api_id=22222).index_prev_close

    try:
        dow_value = stock_dick[77777]
        dow_change = round(100 * (stock_dick[77777] - dow_close) / dow_close,2)
    except Exception as e:
        # logger.error(f'Failed calculating dow_change. Reason: {e}')
        print(f'Failed calculating dow_change. Reason: {e}')
        dow_value = -1.0
        dow_change = -1.0

    try:
        snp_change = round(100 * (snp_current_value - snp_close) / snp_close,2)
    except Exception as e:
        # logger.error(f'Failed calculating snp_change. Reason: {e}')
        print(f'Failed calculating snp_change. Value: {snp_current_value}  snp_close: {snp_close}. Reason: {e}')
        snp_change = -1.0

    try:
        nas_value = stock_dick[55555]
        nas_change = round(100 * (stock_dick[55555] - nas_close) / nas_close,2)
    except Exception as e:
        print(f'Failed calculating nas_change. Reason: {e}')
        nas_value = -1.0
        nas_change = -1.0

    try:
        vix_value = stock_dick[11111]
        vix_change = round(100 * (stock_dick[11111] - vix_close) / vix_close,2)
    except Exception as e:
        print(f'Failed calculating vix_change. Reason: {e}')
        vix_value = -1.0
        vix_change = -1.0

    try:
        r2k_value = stock_dick[22222]
        r2k_change = round(100 * (stock_dick[22222] - r2k_close) / r2k_close,2)
    except Exception as e:
        print(f'Failed calculating r2k_change. Reason: {e}')
        r2k_value = -1.0
        r2k_change = -1.0


    context = {
        'dow_value': round(dow_value,2), 
        'snp_value': round(snp_current_value,2),
        'nas_value': round(nas_value,2),
        'vix_value': round(vix_value,2),
        'r2k_value': round(r2k_value,2),

        'dow_change': dow_change,
        'snp_change': snp_change,
        'nas_change': nas_change,
        'vix_change': vix_change,
        'r2k_change': r2k_change,

        'snp_color': change_check(snp_change),
        'dow_color': change_check(dow_change),
        'nas_color': change_check(nas_change),
        'vix_color': change_check(vix_change),
        'r2k_color': change_check(r2k_change),

        'ib_api_connected': connection_status
    }
    return render(request, 'ib_api/indeces.html', context)

def week_check(history_min, history_max ,realtime_price, week3=False):

    if realtime_price > history_min:
        relative_value_tmp = round(float((100  / ( history_max - history_min)) * (realtime_price - history_min)),2)
    else:
        relative_value_tmp = 0

    relative_value = 100 if relative_value_tmp > 100 else relative_value_tmp

    w_color = week_color(relative_value, week3)

    return relative_value, w_color 

def stock_data_api(request, table_index=1, sort=None):

    stocks_db = StockData.objects.filter(table_index=table_index)
    stocks_db_dict = {}
    stocks_db_dict_list = []
    # for i in range(len(stocks_db)):
    for stock in stocks_db:

        try:
            week1, w1_color = week_check(stock.week_1_min, stock.week_1_max, stock_dick[stock.id])
            week2, w2_color = week_check(stock.week_2_min, stock.week_2_max, stock_dick[stock.id])
            week3, w3_color = week_check(stock.week_3_min, stock.week_3_max, stock_dick[stock.id], week3=True)
            week5, w5_color = week_check(stock.week_5_min, stock.week_5_max, stock_dick[stock.id])

            if trading_status():
                # Updating new minimum prices to the DB
                if week1 == 0:
                    stock.week_1_min = stock_dick[stock.id]
                if week2 == 0:
                    stock.week_2_min = stock_dick[stock.id]
                if week3 == 0:
                    stock.week_3_min = stock_dick[stock.id]
                if week5 == 0:
                    stock.week_5_min = stock_dick[stock.id]

                stock.save()

            else:
                # No Trading 
                pass
            
            stocks_db_dict[stock.id] = {
                'stock_id': stock.id,
                'ticker': stock.ticker,
                'stock_price': stock_dick[stock.id],
                'table_index': stock.table_index,
                'stock_date': stock.stock_date,
                'stock_displayed_date': stock.stock_displayed_date,
                'stock_trend_30':   stock.stock_trend_30, 
                'stock_trend_14':   stock.stock_trend_14, 
                'macd_trend_30':  stock.macd_trend_30, 
                'macd_trend_14':  stock.macd_trend_14, 
                'money_flow_trend_30':  stock.money_flow_trend_30,
                'money_flow_trend_14':  stock.money_flow_trend_14,
                'week_1': week1,
                'week_2': week2,
                'week_3': week3,
                'week_5': week5,
                'week_1_color': w1_color,
                'week_2_color': w2_color,
                'week_3_color': w3_color,
                'week_5_color': w5_color,
                'gap_1': stock.gap_1,
                'gap_2': stock.gap_2,
                'gap_3': stock.gap_3,
                'gap_1_color': stock.gap_1_color,
                'gap_2_color': stock.gap_2_color,
                'gap_3_color': stock.gap_3_color,
                'earnings_call': stock.earnings_call,
                'earnings_call_displayed': stock.earnings_call_displayed,
                'earnings_warning': stock.earnings_warning,
                'macd_30_clash': stock.macd_30_clash,
                'macd_14_clash': stock.macd_14_clash,
                'mfi_30_clash': stock.mfi_30_clash,
                'mfi_14_clash': stock.mfi_14_clash,
                'macd_30_color': stock.macd_30_color,
                'macd_14_color': stock.macd_14_color,
                'mfi_30_color': stock.mfi_30_color,
                'mfi_14_color': stock.mfi_14_color,
                'sample_period_14': stock.sample_period_14,
                'rsi': stock.rsi,
                'rsi_color': stock.rsi_color,
                'dividend_date':stock.dividend_date,
                'dividend': stock.dividend,
                'updading_gap_1_flag': stock.updading_gap_1_flag
            }

            stocks_db_dict_list.append(stocks_db_dict[stock.id])
        except Exception as e:
            print(f'(ERROR: Failed loading stock {stock}  to API. Reason: {e}')

    sorted_list = sorted(stocks_db_dict_list, key=lambda k: k['week_3'])
    
    context = {
        # 'stocks_streaming': stock_dick.items(), 
        'ib_api_connected': connection_status,
        # 'stocks_processed': stocks_db_dict.items()
        'stocks_processed': sorted_list
    }

    print(f'CONNECTION STATUS: {connection_status}')

    return render(request, 'ib_api/stock_data_api.html', context)


STOP_API = 'stop'
UPADATE_STOCKS = 'update'
RUN_API = 'run'

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
        
        app.connect("127.0.0.1", settings.IB_PORT, clientId=settings.IB_CLIENT_ID)
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

        contract.symbol = "NQ"
        contract.secType = "IND"
        contract.currency = "USD"
        contract.exchange = "GLOBEX"
        # app.reqMarketDataType(3)
        
        # RTVolume - contains the last trade price, last trade size, last trade time, total volume, VWAP, and single trade flag. - Gives 0
        # app.reqMktData(55555, contract, 233, False, False, []) 
        
        # Mark Price (used in TWS P&L computations) - no change
        app.reqMktData(55555, contract, 221, False, False, []) 

        contract.symbol = "SPX"
        contract.secType = "IND"
        contract.currency = "USD"
        contract.exchange = "CBOE"
        app.reqMktData(88888, contract, 221, False, False, [])

        contract.symbol = "INDU"
        contract.secType = "IND"
        contract.currency = "USD"
        contract.exchange = "CME"
        app.reqMktData(77777, contract, 221, False, False, [])

        contract.symbol = "VIX"
        contract.secType = "IND"
        contract.currency = "USD"
        contract.exchange = "CBOE"
        app.reqMktData(11111, contract, 221, False, False, [])

        contract.symbol = "RUT"
        contract.secType = "IND"
        contract.currency = "USD"
        contract.exchange = "RUSSELL"
        app.reqMktData(22222, contract, 221, False, False, [])


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
            app.reqMarketDataType(4)
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
