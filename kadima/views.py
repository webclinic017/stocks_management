import random
import json
import pandas as pd
import math
import matplotlib
import matplotlib.pyplot as plt
import numpy as np 
import datetime
import re
from threading import Thread

from math import *
from numpy import round

from datetime import timedelta
from pandas_datareader import data as fin_data

from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseBadRequest, HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone

from yahoo_earnings_calendar import YahooEarningsCalendar
import yfinance as yf

from ib_api.views import *
from kadima.k_utils import week_values, gap_1_check,date_obj_to_date

from .models import StockData, IndicesData
from .forms import DateForm
from .ml_models import *
from .value_updates import indexes_updates, earnings_update, update_values
# Create and configure logger
import logging

LOG_FORMAT = '%(levelname)s %(asctime)s - %(message)s'
logging.basicConfig(filename='./log.log',level=logging.INFO,format=LOG_FORMAT, filemode='w')
logger = logging.getLogger()

TODAY = datetime.datetime.today()
MAX_PAST = TODAY - timedelta(30)
UPADATE_STOCKS = 'update'
STOP_API = 'stop'

def stock_alarms(request):
    context = {}
    alarmed_stocks = StockData.objects.filter(stock_alarm=True)
    context['stocks'] = alarmed_stocks

    ib_api_connected = api_connection_status()
    context['ib_api_connected'] = ib_api_connected

    if request.method  == 'POST':
        if 'connect_ib_api' in request.POST:
            api_connect(request)
            context = {}
            ib_api_connected = api_connection_status()
            context['ib_api_connected'] = ib_api_connected
            return render(request, 'kadima/stock_alarms.html', context)

        elif 'disconnect_ib_api' in request.POST:
            api_disconnect(request)
            context = {}
            ib_api_connected = api_connection_status()
            context['ib_api_connected'] = ib_api_connected
            return render(request, 'kadima/stock_alarms.html', context)

        if 'stock_alarm_set' in request.POST:
            stock_id = request.POST.get('stock_alarm_select')
            
            try:
                stock_data = StockData.objects.get(id=stock_id)
            except Exception as e:
                messages.warning(request, 'Please select a stock ticker.')
                print('No Ticker selected.')
                return render(request, 'kadima/stock_alarms.html', context)

            stock_trigger_status = stock_data.stock_alarm_trigger_set

            if ib_api_connected: # Do the same but display the real time if connected 
                stock_data.stock_initial_price = float(request.POST.get(f'stock_price_{stock_id}'))
                stock_data.stock_alarm_delta = float(request.POST.get(f'delta_select'))
                stock_data.stock_alarm_trigger_set = True # Turn on trigger alarm

                # Reset alarm values
                stock_data.stock_price_down_alarm = False # reseting the up/down alerts
                stock_data.stock_price_up_alarm = False
                stock_data.stock_alarm_sound_on_off = False # Resetting the alarm sound

            else:
                stock_data.stock_initial_price = float(request.POST.get(f'stock_price_{stock_id}'))
                stock_data.stock_alarm_delta = float(request.POST.get(f'delta_select'))
                stock_data.stock_alarm_trigger_set = True # Turn on trigger alarm

                # Reset alarm values
                stock_data.stock_price_down_alarm = False # reseting the up/down alerts
                stock_data.stock_price_up_alarm = False
                stock_data.stock_alarm_sound_on_off = False # Resetting the alarm sound
        
            stock_data.save()

        elif 'stock_alarm_cancel' in request.POST:
            
            stock_id = request.POST.get('stock_alarm_cancel')
            stock_data = StockData.objects.get(id=stock_id)
            stock_data.stock_alarm_trigger_set = False # Turn off the trigger alarm
            stock_data.stock_price_down_alarm = False # reseting the up/down alerts
            stock_data.stock_price_up_alarm = False
            stock_data.stock_alarm_sound_on_off = False # Resetting the alarm sound
            stock_data.stock_alarm_delta = 0.0
            stock_data.stock_initial_price = None

            stock_trigger_status = stock_data.stock_alarm_trigger_set
            
            stock_data.save()

            context['trigger_set'] = stock_trigger_status

        elif 'delete_stock' in request.POST:
            stock_id = request.POST['delete_stock']
            stock_data = StockData.objects.get(id=stock_id)
            stock_data.stock_alarm = False 
            stock_data.stock_price_down_alarm = False # reseting the up/down alerts
            stock_data.stock_price_up_alarm = False
            stock_data.stock_alarm_sound_on_off = False # Resetting the alarm sound
            stock_data.stock_alarm_trigger_set = False # Turn off the trigger alarm
            stock_data.stock_alarm_delta = 0.0
            stock_data.stock_initial_price = None
            stock_data.save()

            alarmed_stocks = StockData.objects.filter(stock_alarm=True)
            context['stocks'] = alarmed_stocks
        
        else:
            alarmed_stocks = StockData.objects.filter(stock_alarm=True)
            context['stocks'] = alarmed_stocks


            # return HttpResponseRedirect(request.path_info)


    return render(request, 'kadima/stock_alarms.html', context)


def history(request, table_index=1):
    context = {}
    saved_stocks = StockData.objects.filter(saved_to_history=True, table_index=table_index)
    context['stocks'] = saved_stocks
    context['table_index'] = table_index

    ib_api_connected = api_connection_status()
    context['ib_api_connected'] = ib_api_connected


    date_picker = DateForm()

    if request.method == 'POST':
        if 'connect_ib_api' in request.POST:
            api_connect(request)
            context = {}
            ib_api_connected = api_connection_status()
            context['ib_api_connected'] = ib_api_connected
            return render(request, 'kadima/history.html', context)
 
        elif 'disconnect_ib_api' in request.POST:
            api_disconnect(request)
            context = {}
            ib_api_connected = api_connection_status()
            context['ib_api_connected'] = ib_api_connected
            return render(request, 'kadima/history.html', context)
    
        elif 'update_stock' in str(request.POST):

            for k in request.POST.keys():
                if 'update_stock' in k:
                    stock_id = k.split('_')[-1]
                else:
                    print(f'ERROR:failed getting stock ID')
                    logger.error(f'ERROR:failed getting stock ID')

            stock_data = StockData.objects.get(id=stock_id)

            stock_data.stocks_bought = int(request.POST.get(f'stocks_bought_{stock_id}'))
            stock_data.purchase_price = float(request.POST.get(f'stock_purchase_price_{stock_id}'))
            stock_data.stocks_sold = int(request.POST.get(f'stocks_sold_{stock_id}'))
            stock_data.selling_price = float(request.POST.get(f'selling_price_{stock_id}'))

            stock_data.profit = (stock_data.stocks_sold * stock_data.selling_price) - (stock_data.stocks_bought * stock_data.purchase_price)

            try:
                stock_data.dividends = float(request.POST.get(f'dividends_{stock_id}'))
            except:
                pass

            stock_data.total_profit = stock_data.profit + stock_data.dividends
            stock_data.save()

            context['stocks'] = saved_stocks


        elif 'delete_stock' in request.POST:
            stock_id = request.POST['delete_stock']
            stock_data = StockData.objects.get(id=stock_id)
            stock_data.saved_to_history = False 
            stock_data.save()

            saved_stocks = StockData.objects.filter(saved_to_history=True)
            context['stocks'] = saved_stocks

            return HttpResponseRedirect(request.path_info)


        # Filter history stocks according to dates range
        elif 'date_picker' in request.POST:
            start_date = request.POST['datetimepicker1']
            end_date = request.POST['datetimepicker2']

            start = date_obj_to_date(start_date,'dash')
            end = date_obj_to_date(end_date,'dash')

            print(f"START: ***************{start}****************")

            filtered_stocks = StockData.objects.filter(saved_to_history=True, stock_date_range=[start, end])
            context['stocks'] = filtered_stocks

            # return HttpResponseRedirect(request.path_info)
            return render(request, 'kadima/history.html', context)

        else:
            saved_stocks = StockData.objects.filter(saved_to_history=True)
            context['stocks'] = saved_stocks
            
            return render(request, 'kadima/history.html', context)
    
    return render(request, 'kadima/history.html', context)

def home(request, table_index=1):
    context = {}
    context['table_index'] = table_index
    ib_api_connected = api_connection_status()

    try:
        sample_period = StockData.objects.last().sample_period_14
    except:
        sample_period = None
        
    context['sample_period_14'] = sample_period

    context['ib_api_connected'] = ib_api_connected

    stock_ref = StockData.objects.all().last()

    # Check if there are any stocks in the DB
    if stock_ref:
        last_update = stock_ref.stock_date
    else:
        last_update = False

    current_running_threads = threading.active_count()
    print(f"ACTIVE THREADS: ***************{current_running_threads}****************")
    
    stocks = StockData.objects.filter(table_index=table_index)
    context['stocks'] = stocks

    # VALUES UPDATES
    #########################
    
    # Updating indexes data every time homepage rendered
    indexes_update_done, indexes_info = indexes_updates()

    if indexes_update_done:
        print('Finished updating indexes')
        context.update(indexes_info)
    else:
        messages.error(request, 'Failed updating indexes.')
        logger.error('Failed updating indexes.')
        print('Failed updating indexes.')


    # Stock data will be updated at API connect

    if request.method == 'POST':

        if 'connect_ib_api' in request.POST:

            api_connect(request)

            current_stocks = StockData.objects.all()
            current_stocks_list = dict()
            for stock in current_stocks:
                current_stocks_list[stock.id] = stock.ticker
            
            ib_api_wrapper(request, updated_stock_list=current_stocks_list, action=UPADATE_STOCKS)

            stocks = StockData.objects.filter(table_index=table_index)
            context['stocks'] = stocks
            
            ib_api_connected = api_connection_status()
            context['ib_api_connected'] = ib_api_connected
            
            return render(request, 'kadima/home.html', context)

        elif 'update_now' in request.POST:
            update_values(request)

        elif 'disconnect_ib_api' in request.POST:
            # print('Stopping the IB API...')
            # ib_api_wrapper(request,action=STOP_API )
            # sleep(2)
            api_disconnect(request)
            context['ib_api_connected'] = api_connection_status()
            return render(request, 'kadima/home.html', context)
            
        elif 'add_stock' in request.POST:
            
            stocks_to_add  = request.POST.get('stock').split(',')

            # Checking list of current stocks in the DB
            old_stocks = StockData.objects.all()
            old_stocks_list = []
            for stock in old_stocks:
                old_stocks_list.append(stock.id)

            for stock in stocks_to_add:
                
                stock = stock.strip()            
                
                print(f'Adding stock: {stock}')
                context['stock'] = stock
                try:
                    stock_df = fin_data.get_data_yahoo(stock, start=MAX_PAST, end=TODAY)
                except Exception as e:
                    messages.error(request, 'Stock does not exists')
                    # return render(request, 'kadima/home.html', context)
                    continue
                
                stock_data = StockData()
                
                stock_data.table_index = table_index

                stock_data.stock_date = stock_df.index[-1]
                stock_data.stock_displayed_date = date_obj_to_date(pd.Timestamp("today"), date_format='slash')

                stock_data.ticker = stock.upper()
                stock_data.stock_price = float("%0.2f"%stock_df['Close'].iloc[-1])

                stock_data.week_1, stock_data.week_1_min, stock_data.week_1_max = week_values(stock_df, 5)
                stock_data.week_2, stock_data.week_2_min, stock_data.week_2_max = week_values(stock_df, 10)
                stock_data.week_3, stock_data.week_3_min, stock_data.week_3_max = week_values(stock_df, 15)
                stock_data.week_5, stock_data.week_5_min, stock_data.week_5_max = week_values(stock_df, 25)

                stock_data.week_1_color = week_color(stock_data.week_1)
                stock_data.week_2_color = week_color(stock_data.week_2)
                stock_data.week_3_color = week_color(stock_data.week_3, week3=True)
                stock_data.week_5_color = week_color(stock_data.week_5)


                prev_close = round(stock_df.loc[stock_df.index[-2]]['Close'],2)
                todays_open = round(stock_df.loc[stock_df.index[-1]]['Open'],2)
                stock_data.prev_close = prev_close
                stock_data.todays_open = todays_open

                gap_1, gap_1_color = gap_1_check(prev_close, todays_open)
                stock_data.gap_1 = gap_1
                stock_data.gap_1_color = gap_1_color

                # Earning dates
                yec = YahooEarningsCalendar()
                try:
                    timestmp = yec.get_next_earnings_date(stock)
                    earnings_date_obj = datetime.datetime.fromtimestamp(timestmp)
                    stock_data.earnings_call = earnings_date_obj
                except Exception as e:
                    messages.error(request, 'Stock does not have an earnings call date defined.')
                    earnings_date_obj = None    

                if earnings_date_obj:
                    stock_data.earnings_call_displayed = date_obj_to_date(earnings_date_obj, date_format='slash')
                
                    if (earnings_date_obj - today).days <= 7 and (earnings_date_obj - today).days >= 0:
                        stock_data.earnings_warning = 'blink-bg'
                    else:
                        pass
                else:
                    pass


                tan_deviation_angle = math.tan(math.radians(settings.DEVIATION_ANGLE))


                # Stock Trend - 30 days sample
                a_stock_30 = stock_regression(stock, 30)
                stock_data.stock_trend_30 = round(a_stock_30,2)

                # MACD trend
                a_macd_30 = trend_calculator(stock, 'MACD', period=30)
                stock_data.macd_trend_30 = round(a_macd_30,2)

                if np.abs(a_macd_30) > tan_deviation_angle:                    
                
                    if (a_stock_30 > 0 and a_macd_30 < 0) or (a_stock_30 < 0 and a_macd_30 > 0):
                        stock_data.macd_30_clash = True
                        stock_data.macd_30_color = 'red'
                    elif (a_stock_30 < 0 and a_macd_30 < 0) or (a_stock_30 > 0 and a_macd_30 > 0):
                        stock_data.macd_30_clash = False
                        stock_data.macd_30_color = 'green'

                else:
                    stock_data.macd_30_clash = False
                    stock_data.macd_30_color = 'green'

                # MFI trend
                a_mfi_30 = trend_calculator(stock, 'MFI', period=30)
                stock_data.money_flow_trend_30 = round(a_mfi_30,2)


                if np.abs(a_mfi_30) > tan_deviation_angle:                    

                        if (a_stock_30 > 0 and a_mfi_30 < 0) or (a_stock_30 < 0 and a_mfi_30 > 0):
                            stock_data.mfi_30_clash = True
                            stock_data.mfi_30_color = 'red'
                        elif (a_stock_30 < 0 and a_mfi_30 < 0) or (a_stock_30 > 0 and a_mfi_30 > 0):
                            stock_data.mfi_30_clash = False
                            stock_data.mfi_30_color = 'green'
                else:
                    stock_data.mfi_30_clash = False
                    stock_data.mfi_30_color = 'green'

                # Stock Trend - 14 days sample
                a_stock_14 = stock_regression(stock, 14)
                stock_data.stock_trend_14 = round(a_stock_14,2)

                # MACD trend
                a_macd_14 = trend_calculator(stock, 'MACD', period=14)
                stock_data.macd_trend_14 = round(a_macd_14,2)

                if np.abs(a_macd_14) > tan_deviation_angle:                    
                
                    if (a_stock_14 > 0 and a_macd_14 < 0) or (a_stock_14 < 0 and a_macd_14 > 0):
                        stock_data.macd_14_clash = True
                        stock_data.macd_14_color = 'red'
                    elif (a_stock_14 < 0 and a_macd_14 < 0) or (a_stock_14 > 0 and a_macd_14 > 0):
                        stock_data.macd_14_clash = False
                        stock_data.macd_14_color = 'green'

                else:
                    stock_data.macd_14_clash = False
                    stock_data.macd_14_color = 'green'

                # MFI trend
                a_mfi_14 = trend_calculator(stock, 'MFI', period=14)
                stock_data.money_flow_trend_14 = round(a_mfi_14,2)


                if np.abs(a_mfi_30) > tan_deviation_angle:                    

                        if (a_stock_14 > 0 and a_mfi_14 < 0) or (a_stock_14 < 0 and a_mfi_14 > 0):
                            stock_data.mfi_14_clash = True
                            stock_data.mfi_14_color = 'red'
                        elif (a_stock_14 < 0 and a_mfi_14 < 0) or (a_stock_14 > 0 and a_mfi_14 > 0):
                            stock_data.mfi_14_clash = False
                            stock_data.mfi_14_color = 'green'
                else:
                    stock_data.mfi_14_clash = False
                    stock_data.mfi_14_color = 'green'


                # Getting the dividend
                try:
                    st = yf.Ticker(stock).dividends.tail(1)
                    stock_data.dividend = float(st.values)
                    date_arr = str(st.index[0]).split(' ')[0].split('-')
                    year = date_arr[0]
                    month = date_arr[1]
                    day = date_arr[2]
                    stock_data.dividend_date = day + '/' + month + '/' + year
                except:
                    stock_data.dividend = None
                    stock_data.dividend_date = None

                ## Adding the stock saving to DB
                try:
                    stock_data.save()
                except Exception as e:
                    messages.error(request, f'Stock {stock} was not added. Already in the list.')
                    return render(request, 'kadima/home.html', context)
                


            new_stocks = StockData.objects.filter(table_index=table_index).order_by('week_3')
            context['stocks'] = new_stocks
                
            ## Updating the streaming IB API data with added stock
            new_stocks_api = StockData.objects.all()
            new_stocks_list = dict()
            for stock in new_stocks_api:
                new_stocks_list[stock.id] = stock.ticker
            
            if api_connection_status():
                ib_api_wrapper(request,old_stocks_list, new_stocks_list, action=UPADATE_STOCKS)


            return render(request, 'kadima/home.html', context)
        
        elif 'update_sample_period' in request.POST:
            print('SAMPLING')
            stocks = StockData.objects.all()
            for stock in stocks:
                if request.POST['sample_period'] == '14':
                    stock.sample_period_14 = True
                    stock.save()
                    context['sample_period_14'] = True

                else:
                    stock.sample_period_14 = False
                    stock.save()
                    context['sample_period_14'] = False

        elif 'delete_stock' in request.POST:
            print('POP')
            old_stocks = StockData.objects.all()
            old_stocks_list = []
            for stock in old_stocks:
                old_stocks_list.append(stock.id)

            # Deleting a stock from DB
            StockData.objects.filter(id=request.POST['delete_stock']).delete()
            new_stocks = StockData.objects.filter(table_index=table_index).order_by('week_3')
            context['stocks'] = new_stocks

            ## Updating the streaming IB API data with deleted stock
            new_stocks_api = StockData.objects.all()
            new_stocks_list = dict()
            for stock in new_stocks_api:
                new_stocks_list[stock.id] = stock.ticker
            
            if api_connection_status():
                ib_api_wrapper(request,old_stocks_list, new_stocks_list, action=UPADATE_STOCKS)
            # ib_api_wrapper(request,old_stocks_list=old_stocks_list, updated_stock_list=new_stocks_list, action=UPADATE_STOCKS)


            return render(request, 'kadima/home.html', context)

        elif 'save_stock' in request.POST:
            stock_id = request.POST['save_stock']
            stock_data = StockData.objects.get(id=stock_id)
            stock_data.saved_to_history = True  
            stock_data.save()
            messages.warning(request, f"Stock was saved. You can review it's data on the History page.")

            stocks = StockData.objects.filter(table_index=table_index).order_by('week_3')
            context['stocks'] = stocks
            return render(request, 'kadima/home.html', context)

        elif 'alarm_stock' in request.POST:
            stock_id = request.POST['alarm_stock']
            stock_data = StockData.objects.get(id=stock_id)
            stock_data.stock_alarm = True  
            stock_data.save()
            messages.info(request, f"Stock {stock_data.ticker} was added to alarm page. You can trigger value alarms on the Alarms page.")

            stocks = StockData.objects.filter(table_index=table_index).order_by('week_3')
            context['stocks'] = stocks
            return render(request, 'kadima/home.html', context)

        else:
            stocks = StockData.objects.filter(table_index=table_index).order_by('week_3')
            context['stocks'] = stocks

            return render(request, 'kadima/home.html', context)


    else:
        stocks = StockData.objects.filter(table_index=table_index).order_by('week_3')
        context['stocks'] = stocks
        return render(request, 'kadima/home.html', context)

    return render(request, 'kadima/home.html', context)



def api_connect(request):
    print('Connecting API...')
            
    ib_api_wrapper(request)
    
    timer = 1
    while timer < 3:
        sleep(1)
        print('Sleeping...')
        timer += 1 

    # Updating valuse
    finish_updates = update_values(request)

    if finish_updates:
        print('Finished updating values.')
        messages.error(request, 'FINISHED updating values. ')
        logger.info('Finished updating values.')
    else:
        print('Failed updating values.')
        messages.error(request, 'Failed updating values. Contact support.')
        logger.error('Failed updating values.')

    return

def api_disconnect(request):
    # print('Updating values before disconnecting')
    # update_values(request)

    print('Stopping the IB API...')
    ib_api_wrapper(request,action=STOP_API )
    sleep(2)
    return