import time
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

from kadima.models import StockData, IndicesData, EmailSupport
from kadima.k_utils import week_color, change_check, send_email_alert

# Create and configure logger
import logging
LOG_FORMAT = '%(levelname)s %(asctime)s - %(message)s'
logging.basicConfig(filename='./views_ib_api.log',level=logging.INFO,format=LOG_FORMAT, filemode='w')
logger = logging.getLogger()

TODAY = datetime.datetime.today()

NAS = 55555
DOW = 77777
SNP = 88888
VIX = 11111
R2K = 22222

stock_dick = dict()
stock_open = dict()

connection_status = False

def trading_status():
    if -1.0 in stock_dick.values():
        return False
    else:
        return True

# async def get_current_price(stock_id):
#     await current_price = stock_dick[stock_id]
#         print(f'>>>>>>>>>>>CURRENT: {current_price}')
#         return current_price
#     except Exception as e:
#         print(f'ERROR LOAD PRICE: {e}')
#         return -1

def api_connection_status():
    return connection_status

def alarm_trigger(request):
    context = {}
    stocks_in_alarm = StockData.objects.filter(stock_alarm_trigger_set=True)
    
    for stock in stocks_in_alarm:

        if stock.stock_price_up_alarm:
            # messages.success(request, f'UP TRIGGER: {stock.ticker}')

            if stock.stock_alarm_sound_on_off:
                pass
            else:
                context['play_sound'] = 'up'
                stock.stock_alarm_sound_on_off = True
                stock.save()
        
        elif stock.stock_price_down_alarm:
            # messages.warning(request, f'DOWN TRIGGER: {stock.ticker}')

            if stock.stock_alarm_sound_on_off:
                pass
            else:
                context['play_sound'] = 'down'
                stock.stock_alarm_sound_on_off = True
                stock.save()
        
        else:
            pass
    
    return render(request,'kadima/alarm_trigger.html', context)


def stocks_alarms_data(request):
    context = {}
    saved_alarms_stocks = StockData.objects.filter(stock_alarm=True)

    price_up = False
    price_down = False

    stocks_db_alarms_dict = {}
    stocks_db_dict_list = []

    stock_alarms = []
    stock_alarms_colors = []

    for stock in saved_alarms_stocks:
    
        # Extract the current alarm values:

        stock_alarms.append(stock.stock_alarm_1)
        stock_alarms.append(stock.stock_alarm_2)
        stock_alarms.append(stock.stock_alarm_3)
        stock_alarms.append(stock.stock_alarm_4)
        stock_alarms.append(stock.stock_alarm_5)
        stock_alarms.append(stock.stock_alarm_6)
        stock_alarms.append(stock.stock_alarm_7)
        stock_alarms.append(stock.stock_alarm_8)
        stock_alarms.append(stock.stock_alarm_9)
        stock_alarms.append(stock.stock_alarm_10)

        # Extract the current alarm colors:
        stock_alarms_colors.append(stock.stock_alarm_1_color)
        stock_alarms_colors.append(stock.stock_alarm_2_color)
        stock_alarms_colors.append(stock.stock_alarm_3_color)
        stock_alarms_colors.append(stock.stock_alarm_4_color)
        stock_alarms_colors.append(stock.stock_alarm_5_color)
        stock_alarms_colors.append(stock.stock_alarm_6_color)
        stock_alarms_colors.append(stock.stock_alarm_7_color)
        stock_alarms_colors.append(stock.stock_alarm_8_color)
        stock_alarms_colors.append(stock.stock_alarm_9_color)
        stock_alarms_colors.append(stock.stock_alarm_10_color)

        try:
            week3, w3_color = week_check(stock.week_3_min, stock.week_3_max, stock_dick[stock.id], week3=True)

            # Week1 <=> 90 days
            week1, w1_color = week_check(stock.week_1_min, stock.week_1_max, stock_dick[stock.id], week3=True)

            # Checking alarm trigger
            trigger_alarm_set = stock.stock_alarm_trigger_set
            alarm_delta = stock.stock_alarm_delta
            initial_stock_price = stock.stock_initial_price
            current_stock_price = stock_dick[stock.id]

            if trigger_alarm_set:

                if current_stock_price > (initial_stock_price + alarm_delta):
                    
                    price_up = True
                    price_down = False
                    stock.stock_price_up_alarm = True

                    stock_alarms.append(current_stock_price)
                    stock_alarms_colors.append('green')
                    stock.stock_initial_price = current_stock_price
                    

                elif current_stock_price < (initial_stock_price - alarm_delta):

                    price_up = False
                    price_down = True
                    stock.stock_price_down_alarm = True

                    stock_alarms.append(current_stock_price)
                    stock_alarms_colors.append('red')
                    stock.stock_initial_price = current_stock_price

                else:
                    price_up = False
                    price_down = False
            else:
                price_up = False
                price_down = False

            stock_alarms = stock_alarms[-10:]
            stock.stock_alarm_1 = stock_alarms[0]
            stock.stock_alarm_2 = stock_alarms[1]
            stock.stock_alarm_3 = stock_alarms[2]
            stock.stock_alarm_4 = stock_alarms[3]
            stock.stock_alarm_5 = stock_alarms[4]
            stock.stock_alarm_6 = stock_alarms[5]
            stock.stock_alarm_7 = stock_alarms[6]
            stock.stock_alarm_8 = stock_alarms[7]
            stock.stock_alarm_9 = stock_alarms[8]
            stock.stock_alarm_10 = stock_alarms[9]

            stock_alarms_colors = stock_alarms_colors[-10:]
            stock.stock_alarm_1_color = stock_alarms_colors[0]
            stock.stock_alarm_2_color = stock_alarms_colors[1]
            stock.stock_alarm_3_color = stock_alarms_colors[2]
            stock.stock_alarm_4_color = stock_alarms_colors[3]
            stock.stock_alarm_5_color = stock_alarms_colors[4]
            stock.stock_alarm_6_color = stock_alarms_colors[5]
            stock.stock_alarm_7_color = stock_alarms_colors[6]
            stock.stock_alarm_8_color = stock_alarms_colors[7]
            stock.stock_alarm_9_color = stock_alarms_colors[8]
            stock.stock_alarm_10_color = stock_alarms_colors[9]

            stock.save()


            stocks_db_alarms_dict[stock.id] = {
                'pk': stock.id,
                'ticker': stock.ticker,
                'stock_load_price' : stock.stock_load_price,
                'stock_initial_price' : stock.stock_initial_price,
                'stock_price': stock_dick[stock.id],
                'stock_date': stock.stock_date,
                'stock_displayed_date': stock.stock_displayed_date,
                'week_1': week1,
                'week_1_color': w1_color,
                'week_3': week3,
                'week_3_color': w3_color,
                'gap_1': stock.gap_1,
                'gap_1_color': stock.gap_1_color,
                'rsi': stock.rsi,
                'rsi_color': stock.rsi_color,
                'dividend_date': stock.dividend_date,
                'dividend_warning': stock.dividend_warning,
                'earnings_call_displayed': stock.earnings_call_displayed,
                'earnings_warning': stock.earnings_warning,
                'stock_alarm_trigger_set': trigger_alarm_set,
                'stock_alarm_delta': alarm_delta,
                'price_up': price_up,
                'price_down': price_down,
                'stock_alarm_1': stock_alarms[0],
                'stock_alarm_2': stock_alarms[1],
                'stock_alarm_3': stock_alarms[2],
                'stock_alarm_4': stock_alarms[3],
                'stock_alarm_5': stock_alarms[4],
                'stock_alarm_6': stock_alarms[5],
                'stock_alarm_7': stock_alarms[6],
                'stock_alarm_8': stock_alarms[7],
                'stock_alarm_9': stock_alarms[8],
                'stock_alarm_10': stock_alarms[9],
                'stock_alarm_1_color': stock_alarms_colors[0],
                'stock_alarm_2_color': stock_alarms_colors[1],
                'stock_alarm_3_color': stock_alarms_colors[2],
                'stock_alarm_4_color': stock_alarms_colors[3],
                'stock_alarm_5_color': stock_alarms_colors[4],
                'stock_alarm_6_color': stock_alarms_colors[5],
                'stock_alarm_7_color': stock_alarms_colors[6],
                'stock_alarm_8_color': stock_alarms_colors[7],
                'stock_alarm_9_color': stock_alarms_colors[8],
                'stock_alarm_10_color': stock_alarms_colors[9]
            }

            stocks_db_dict_list.append(stocks_db_alarms_dict[stock.id])
        
        except Exception as e:
            print(f'ERROR: Failed loading stock: {stock} to alarm list. Reason: {e}')

    context = {
        # 'stocks_streaming': stock_dick.items(), 
        'ib_api_connected': connection_status,
        'stocks': stocks_db_dict_list
    }

    print(f'CONNECTION STATUS: {connection_status}')
    # with open('ib_api/stocks_data.json', 'w+') as fd:
    #     json.dump(stock_dick, fd)


    return render(request, 'ib_api/stock_alarms_streaming.html', context)

def indeces_data(request):

    snp = IndicesData.objects.get(index_api_id=SNP)
    dow = IndicesData.objects.get(index_api_id=DOW)
    nas = IndicesData.objects.get(index_api_id=NAS)
    vix = IndicesData.objects.get(index_api_id=VIX)
    r2k = IndicesData.objects.get(index_api_id=R2K)

    nas_close = IndicesData.objects.get(index_api_id=55555).index_prev_close
    nas_macd_color = IndicesData.objects.get(index_api_id=55555).index_macd_color
    nas_mfi_color = IndicesData.objects.get(index_api_id=55555).index_mfi_color

    dow_close = IndicesData.objects.get(index_api_id=77777).index_prev_close
    dow_macd_color = IndicesData.objects.get(index_api_id=77777).index_macd_color
    dow_mfi_color = IndicesData.objects.get(index_api_id=77777).index_mfi_color

    snp_close = IndicesData.objects.get(index_api_id=88888).index_prev_close
    snp_macd_color = IndicesData.objects.get(index_api_id=88888).index_macd_color
    snp_mfi_color = IndicesData.objects.get(index_api_id=88888).index_mfi_color

    r2k_close = IndicesData.objects.get(index_api_id=22222).index_prev_close
    r2k_macd_color = IndicesData.objects.get(index_api_id=22222).index_macd_color
    r2k_mfi_color = IndicesData.objects.get(index_api_id=22222).index_mfi_color

    vix_index = IndicesData.objects.get(index_api_id=11111)
    vix_close = vix_index.index_prev_close

    vix_week1, vix_w1_color = week_check(vix_index.index_week1_min, vix_index.index_week1_max, stock_dick[11111])
    vix_week2, vix_w2_color = week_check(vix_index.index_week2_min, vix_index.index_week2_max, stock_dick[11111])
    vix_week3, vix_w3_color = week_check(vix_index.index_week3_min, vix_index.index_week3_max, stock_dick[11111], week3=True)

    if trading_status():
        # Updating new minimum prices to the DB
        if vix_week1 == 0:
            stock.index_week1_min = stock_dick[11111]
        if vix_week2 == 0:
            stock.index_week2_min = stock_dick[11111]
        if vix_week3 == 0:
            stock.index_week3_min = stock_dick[11111]

        vix_index.save()


    try:
        dow_value = dow.index_current_value
        # dow_change = dow.index_change
        dow_change = round(100 * (dow_value - dow_close) / dow_close,2)
    except Exception as e:
        # logger.error(f'Failed calculating dow_change. Reason: {e}')
        print(f'Failed calculating dow_change. Reason: {e}')
        dow_value = -1.0
        dow_change = -1.0

    try:
        snp_value = snp.index_current_value
        # snp_change = snp.index_change
        snp_change = round(100 * (snp_value - snp_close) / snp_close,2)
    except Exception as e:
        print(f'Failed calculating snp_change. Reason: {e}')
        snp_change = -1.0

    try:
        nas_value = nas.index_current_value
        # nas_change = nas.index_change
        nas_change = round(100 * (nas_value - nas_close) / nas_close,2)
    except Exception as e:
        print(f'Failed calculating nas_change. Reason: {e}')
        nas_value = -1.0
        nas_change = -1.0

    try:
        vix_value = vix.index_current_value
        # vix_change = vix.index_change
        vix_change = round(100 * (vix_value - vix_close) / vix_close,2)
    except Exception as e:
        print(f'Failed calculating vix_change. Reason: {e}')
        vix_value = -1.0
        vix_change = -1.0

    try:
        r2k_value = r2k.index_current_value
        # r2k_change = r2k.index_change
        r2k_change = round(100 * (r2k_value - r2k_close) / r2k_close,2)
    except Exception as e:
        print(f'Failed calculating r2k_change. Reason: {e}')
        r2k_value = -1.0
        r2k_change = -1.0


    context = {
        'dow_value': round(dow_value,2), 
        'snp_value': round(snp_value,2),
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

        'dow_macd_color': dow_macd_color,
        'dow_mfi_color': dow_mfi_color,
        'nas_macd_color': nas_macd_color,
        'nas_mfi_color': nas_mfi_color,
        'snp_macd_color': snp_macd_color,
        'snp_mfi_color': snp_mfi_color,
        'r2k_macd_color': r2k_macd_color,
        'r2k_mfi_color': r2k_mfi_color,

        'vix_week1': vix_week1,
        'vix_week2': vix_week2,
        'vix_week3': vix_week3,

        'vix_w1_color': vix_w1_color,
        'vix_w2_color': vix_w2_color,
        'vix_w3_color': vix_w3_color,

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

def check_conditions_alerts(request):
    stocks = StockData.objects.all()
    email_support = EmailSupport.objects.all().first().enabled
    stock_alert = ''

    for stock in stocks:
        week3_color = stock.week_3_color
        gap1_color = stock.gap_1_color
        rsi_color = stock.rsi_color
        email_flag = stock.stock_email_alert
        email_alert = False

        if not email_flag:
            if week3_color == 'green' and gap1_color == 'red':
                print(f'stock: {stock.ticker}. w3: {week3_color}  g1: {gap1_color}')
                stock_alert = 'condition_1'
                email_alert = True
            elif week3_color == '#FF1000' and gap1_color == 'green':
                stock_alert = 'condition_2'
                email_alert = True
            elif  week3_color == 'green' and gap1_color == 'red' and rsi_color == 'red':
                stock_alert = 'condition_3'
                email_alert = True
            elif week3_color == '#FF1000' and gap1_color == 'green' and rsi_color == 'green':
                stock_alert = 'condition_4'
                email_alert = True
            else:
                stock_alert = ''
                email_alert = False

        if email_support and email_alert:
            mail_context = {
                'domain': request._current_scheme_host,
                'stock': stock.ticker,
                'week3_color': week3_color,
                'gap1_color': gap1_color,
                'rsi_color': rsi_color
            }

            send_email_alert(subject='KADIMA Stock Alert', email_template_name=None,
                            context=mail_context, to_email=[settings.EMAIL_DEFAULT_TO], 
                            html_email_template_name='kadima/email_stock_alert.html')
            # send_email_alert(request,email_body,[settings.EMAIL_DEFAULT_TO])

            stock.stock_email_alert = True
            stock.save()
        else:
            pass
    
    return stock_alert

def stock_data_api(request, table_index=1, sort=None):

    stock_alert = check_conditions_alerts(request)
    request.session['stock_alert'] = stock_alert

    stocks_db = StockData.objects.filter(table_index=table_index)
    stocks_db_dict = {}
    stocks_db_dict_list = []
    # for i in range(len(stocks_db)):
    for stock in stocks_db:

        try:
            week1, w1_color = week_check(stock.week_1_min, stock.week_1_max, stock_dick[stock.id], week3=True)
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

                stock.stock_current_price = stock_dick[stock.id]

                stock.save()

            else:
                # No Trading 
                pass
            
            stocks_db_dict[stock.id] = {
                'id': stock.id,
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
                'dividend_warning': stock.dividend_warning,
                'dividend': stock.dividend,
                'updading_gap_1_flag': stock.updading_gap_1_flag
            }

            stocks_db_dict_list.append(stocks_db_dict[stock.id])
        except Exception as e:
            print(f'(ERROR: Failed loading stock {stock}  to API. Reason: {e}')

    if sort == 'gap':
        sorted_list = sorted(stocks_db_dict_list, key=lambda k: k['gap_1'])
        print(f'SORTED: {sorted_list}')

    elif sort == 'week3':
        sorted_list = sorted(stocks_db_dict_list, key=lambda k: k['week_3'])
        print(f'WEEK SORTED: {sorted_list}')
    else:
        sorted_list = sorted(stocks_db_dict_list, key=lambda k: k['week_3'])
    
    context = {
        # 'stocks_streaming': stock_dick.items(), 
        'ib_api_connected': connection_status,
        'stock_alert': stock_alert,
        # 'stocks_processed': stocks_db_dict.items()
        'stocks': sorted_list
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
        # print(f"Ticket ID: {reqId} tickType: {TickTypeEnum.to_str(tickType)} Price: {price}", end="\n")

        stock_dick[reqId] = price

        # print only indeces data
        '''
        NAS = 55555
        DOW = 77777
        SNP = 88888
        VIX = 11111
        R2K = 22222
        '''
        # if reqId > 10000:
        #     if tickType == 9 or tickType == 37 or tickType == 4: # 37 = MARK_PRICE, 4 = LAST_PRICE, 9 = CLOSE
        #         print("Ticker Price Data:  Ticket ID: ", reqId, " ","tickType: ", TickTypeEnum.to_str(tickType), "Price: ", price, end="\n")

        # Tick types: https://interactivebrokers.github.io/tws-api/tick_types.html

        # Extracting Previous Close price
        if tickType == 9:
            # stock_close[reqId] = price
            if reqId < 10000:
                stock = StockData.objects.get(id=reqId)
                stock.prev_close = price
                stock.save()
            # Updating Indices DB
            else:
                index = IndicesData.objects.get(index_api_id=reqId)
                # print(f'INDEX: {reqId} PREV_PRICE: {price}')
                index.index_prev_close = price
                index.save()
        
        # REPLACED WITH SCRAPER --
        # Setting last value to index 
        # if tickType == 37 and reqId > 10000:
        if tickType == 4 and reqId > 10000:
            index = IndicesData.objects.get(index_api_id=reqId)
            # print(f'INDEX: {reqId} CURRENT_PRICE: {price}')
            index.index_current_value = price
            index.save()

        # Extracting Open price
        if tickType == 14:
            if reqId < 10000:
                stock = StockData.objects.get(id=reqId)
                stock.todays_open = price
                stock.save()


    def tickByTickAllLast(self, reqId: int, tickType: int, time: int, price: float,
                size: int,tickAttribLast, exchange: str, specialConditions: str):
        
        super().tickByTickAllLast(reqId, tickType, time, price, size, tickAttribLast,exchange, specialConditions)
        if tickType == 1:
            print("Last.", end='\n')
        else:
            print("AllLast.", end='')
            print(" ReqId:", reqId,
                  "Time:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"),
                  "Spec Cond:", specialConditions, "PastLimit:", tickAttribLast.pastLimit, "Unreported:", tickAttribLast.unreported)

    @iswrapper
    def tickByTickMidPoint(self, reqId: int, time: int, midPoint: float):
        super().tickByTickMidPoint(reqId, time, midPoint)
        print("Midpoint. ReqId:", reqId, "Time:", 
            datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"),"MidPoint:", midPoint)

    @iswrapper
    def tickString(self, reqId, tickType, value):
        # Extracting IB_DIVIDENDS
        if tickType == 59:
            stock = StockData.objects.get(id=reqId)
            current_dividend_date = stock.dividend_date
            
            # print(f'>>>>>>>>>>>>>> Stock: {reqId} TickType: {tickType} Dividend: {value} ')

            # Calculating new dividend date
            # divindend_date_obj = datetime.datetime.fromtimestamp(int(value))
            dividend_date_string = str(value).split(',')[2]
            dividend_data = str(value).split(',')[1]
            dividend = dividend_data if dividend_data != '' else 0

            year = dividend_date_string[0:4]
            month = dividend_date_string[4:6]
            day = dividend_date_string[6:8]
            divindend_date = day + '/' + month + '/' + year
            # print(f'>>>>>>>>>>>>>> Stock: {reqId} TickType: {tickType} Dividend: {value}  DATE: {divindend_date} LEN: {len(value)}')
            if len(value) > 5:
                stock.dividend_date = divindend_date
                stock.dividend = dividend
                stock.save()
            else:
                stock.dividend = dividend
                stock.save()
                

    # @iswrapper
    # def tickSize(self, reqId, tickType, size):
    #     print("Ticket ID: ", reqId, " ","tickType: ", TickTypeEnum.to_str(tickType), "Size: ", size)

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

        '''
        NASDAQ = 55555
        DOW = 77777
        SNP = 88888
        VIX = 11111
        R2K = 22222
        '''

        # NASDAQ
        contract.symbol = "NDX"
        contract.secType = "IND"
        contract.currency = "USD"
        contract.exchange = "NASDAQ"

        # RTVolume - contains the last trade price, last trade size, last trade time, total volume, VWAP, and single trade flag. - Gives 0
        # Reference: https://tinyurl.com/y73tg4t8
        # app.reqMktData(55555, contract, 233, False, False, []) 
        
        # Mark Price (used in TWS P&L computations) - no change
        app.reqMktData(NAS, contract, 221, False, False, []) 

        # S&P
        contract.symbol = "SPX"
        contract.secType = "IND"
        contract.currency = "USD"
        contract.exchange = "CBOE"
        app.reqMktData(SNP, contract, 221, False, False, [])
        
        app.reqTickByTickData(SNP, contract, "Last", 0, False);

        # DOW JONES
        contract.symbol = "INDU"
        contract.secType = "IND"
        contract.currency = "USD"
        contract.exchange = "CME"
        app.reqMktData(DOW, contract, 221, False, False, [])

        app.reqTickByTickData(DOW, contract, "Last", 0, False);


        contract.symbol = "VIX"
        contract.secType = "IND"
        contract.currency = "USD"
        contract.exchange = "CBOE"
        app.reqMktData(VIX, contract, 221, False, False, [])

        app.reqTickByTickData(VIX, contract, "Last", 0, False);

        contract.symbol = "RUT"
        contract.secType = "IND"
        contract.currency = "USD"
        contract.exchange = "RUSSELL"
        app.reqMktData(R2K, contract, 221, False, False, [])

        app.reqTickByTickData(R2K, contract, "Last", 0, False);


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
            app.reqMktData(stock_id, contract, "456", False, False, [])

            app.reqTickByTickData(stock_id, contract, "Last", 0, False);

            # app.fundamentalData(stock_id, contract)


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
