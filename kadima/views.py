import random
import json
import pandas as pd
import math
import matplotlib
import matplotlib.pyplot as plt
import numpy as np 
import datetime
import re
import arrow
import threading
from time import sleep
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

# from yahoo_earnings_calendar import YahooEarningsCalendar
import yfinance as yf

from ib_api.views import stock_data_api, alarm_trigger, api_connection_status,ib_api_wrapper
from kadima.k_utils import week_values, gap_1_check,date_obj_to_date, reset_email_alerts, week_color, reset_alarms

from .models import StockData, IndicesData, EmailSupport
from .forms import DateForm
from .ml_models import trends
from .value_updates import indexes_updates, update_values
from kadima.stock import Stock

# Create and configure logger
import logging

LOG_FORMAT = '%(levelname)s %(asctime)s - %(message)s'
logging.basicConfig(filename='./log.log',level=logging.INFO,format=LOG_FORMAT, filemode='w')
logger = logging.getLogger()

TODAY = datetime.datetime.today()
MAX_PAST = TODAY - timedelta(30)
UPADATE_STOCKS = 'update'
STOP_API = 'stop'

def alarm_stocks_selector(request):
    context = {}
    saved_alarms_stocks = StockData.objects.filter(stock_alarm=True)
    context['stocks'] = saved_alarms_stocks
    return render(request, 'kadima/partials/_alarm_stocks_selector.html', context)

def stock_alarms(request):
    context = {}
    alarmed_stocks = StockData.objects.filter(stock_alarm=True)
    context['stocks'] = alarmed_stocks

    ib_api_connected = api_connection_status()
    context['ib_api_connected'] = ib_api_connected

    if request.method  == 'POST':

        if 'connect_ib_api' in request.POST:
            api_connect(request)
            # context = {}
            ib_api_connected = api_connection_status()
            context['ib_api_connected'] = ib_api_connected
            return render(request, 'kadima/stock_alarms.html', context)

        elif 'disconnect_ib_api' in request.POST:
            api_disconnect(request)
            # context = {}
            ib_api_connected = api_connection_status()
            context['ib_api_connected'] = ib_api_connected
            return render(request, 'kadima/stock_alarms.html', context)


        if 'all_alarms_set' in request.POST or 'stock_delta_set' in request.POST:

            if request.POST.get('all_alarms_set') == 'set_all':
                current_alarm_stocks = StockData.objects.filter(stock_alarm=True)
                price_delta = float(request.POST.get(f'delta_select'))

                for stock in current_alarm_stocks:
                    stock.stock_initial_price = float(request.POST.get(f'stock_price_{stock.pk}'))
                    stock.stock_alarm_delta = float(request.POST.get(f'delta_select'))
                    stock.stock_alarm_trigger_set = True # Turn on trigger alarm

                    # Reset alarm values
                    stock.stock_price_down_alarm = False # reseting the up/down alerts
                    stock.stock_price_up_alarm = False
                    stock.stock_alarm_sound_on_off = False # Resetting the alarm sound

                    stock.save()

            else:
                stock_id = request.POST.get('stock_delta_set')
                
                try:
                    stock_data = StockData.objects.get(id=stock_id)
                except Exception as e:
                    messages.warning(request, 'Please select a stock ticker.')
                    print('No Ticker selected.')
                    return render(request, 'kadima/stock_alarms.html', context)

                stock_data.stock_initial_price = float(request.POST.get(f'stock_price_{stock_id}'))
                stock_data.stock_alarm_delta = float(request.POST.get(f"delta_select"))
                stock_data.stock_alarm_trigger_set = True # Turn on trigger alarm

                # Reset alarm values
                stock_data.stock_price_down_alarm = False # reseting the up/down alerts
                stock_data.stock_price_up_alarm = False
                stock_data.stock_alarm_sound_on_off = False # Resetting the alarm sound
            
                stock_data.save()

        elif 'stock_delta_reset' in request.POST:
            stock = StockData.objects.get(id=request.POST.get('stock_delta_reset'))
            reset_alarms(stock)

        elif 'stock_alarm_reset' in request.POST:
            saved_alarms_stocks = StockData.objects.filter(stock_alarm=True)
            for stock in saved_alarms_stocks:
                reset_alarms(stock)

        elif 'delete_all_alarms' in request.POST:
            alarm_stocks = StockData.objects.filter(stock_alarm=True)
            print(f'DELETING STOCKS: {request.POST}')
            for stock in alarm_stocks:
                stock.stock_alarm = False
                stock.save()

        elif 'stock_alarm_cancel' in request.POST:
            
            stock_id = request.POST.get('stock_alarm_cancel')
            stock = StockData.objects.get(id=stock_id)
            reset_alarms(stock)

            stock_trigger_status = False

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

        elif 'sort_gap' in request.POST:
            print('>> Gap Sorting <<')
            request.session['sort_by'] = 'gap_1'
            context['sort_by'] = request.session['sort_by']

        elif 'sort_week3' in request.POST:
            print('>> Week3 Sorting <<')
            request.session['sort_by'] = 'week_3'
            context['sort_by'] = request.session['sort_by']
       
        else:
            alarmed_stocks = StockData.objects.filter(stock_alarm=True)
            context['stocks'] = alarmed_stocks


            # return HttpResponseRedirect(request.path_info)


    return render(request, 'kadima/stock_alarms.html', context)


def history(request, table_index=1):
    context = {}
    saved_stocks = StockData.objects.filter(saved_to_history=True, table_index=table_index)
    context['email_enabled'] = EmailSupport.objects.all().first().enabled
    context['stocks'] = saved_stocks
    context['table_index'] = table_index
    request.session['table_index'] = table_index

    ib_api_connected = api_connection_status()
    context['ib_api_connected'] = ib_api_connected

    date_picker = DateForm()

    if request.method == 'POST':
        if 'connect_ib_api' in request.POST:
            api_connect(request)
            # context = {}
            ib_api_connected = api_connection_status()
            context['ib_api_connected'] = ib_api_connected
            return render(request, 'kadima/history.html', context)
 
        elif 'disconnect_ib_api' in request.POST:
            api_disconnect(request)
            # context = {}
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

        ## Enable email support
        elif 'email_enable' in request.POST:
            print('>> Enable Email <<')
            try:
                email_enable = EmailSupport.objects.all().first()
                if email_enable.enabled:
                    email_enable.enabled = False
                    context['email_enabled'] = False
                    email_enable.save()
                    
                    # Resetting all email alerts to False
                    reset_email_alerts()

                else:
                    email_enable.enabled = True
                    context['email_enabled'] = True
                    email_enable.save()
            except:
                email_enable = EmailSupport()
                email_enable.enabled = True
                context['email_enabled'] = True
                email_enable.save()

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
    context['ib_api_connected'] = ib_api_connected
    request.session['table_index'] = table_index

    try:
        context['email_enabled'] = EmailSupport.objects.all().first().enabled
        print(f'EM: {context["email_enabled"]}')
    except:
        email_support = EmailSupport()
        email_support.enabled = False
        email_support.save()

    stock_ref = StockData.objects.all().last()

    # Check if there are any stocks in the DB
    if stock_ref:
        last_update = stock_ref.stock_date
    else:
        last_update = False

    # Checking current sample_ period
    try:
        sample_period = stock_ref.sample_period_14
    except:
        sample_period = None
        
    context['sample_period_14'] = sample_period

    current_running_threads = threading.active_count()
    print(f"ACTIVE THREADS: ***************{current_running_threads}****************")
    
    stocks = StockData.objects.filter(table_index=table_index)
    context['stocks'] = stocks

    # VALUES UPDATES
    #########################

    #TODO: Replace this update with current database data query.
    # Updating indexes data every time homepage rendered
    
    # indexes_update_done, indexes_info = indexes_updates(request)

    # if indexes_update_done:
    #     print('Finished updating indexes')
    #     context.update(indexes_info)
    # else:
    #     messages.error(request, 'Failed updating indexes.')
    #     logger.error('Failed updating indexes.')
    #     print('Failed updating indexes.')


    # Stock data will be updated at API connect
    if request.method == 'POST':
        if 'connect_ib_api' in request.POST:

            api_connect(request)

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

        elif 'sort_gap' in request.POST:
            print('>> Gap Sorting <<')
            request.session['sort_by'] = 'gap_1'
            context['sort_by'] = request.session['sort_by']

        elif 'sort_week3' in request.POST:
            print('>> Week3 Sorting <<')
            request.session['sort_by'] = 'week_3'
            context['sort_by'] = request.session['sort_by']

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

                # stock_data.stock_date = stock_df.index[-1]
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
                try:
                    earnings = yf.Ticker(stock).calendar['Value'][0]
                    arrow_object = arrow.get(earnings, 'US/Eastern')
                    stock_data.earnings_call = arrow_object.datetime
                    year = arrow_object.datetime.year
                    month = arrow_object.datetime.month
                    day = arrow_object.datetime.day
                    stock_data.earnings_call_displayed = str(f'{day}/{month}/{year}')
                    
                    # print(f'DELTA {stock}: {earnings - today}')
                    if (earnings - TODAY).days <= 7 and (earnings - TODAY).days >= 0:
                        stock_data.earnings_warning = 'blink-bg'
                    else:
                        stock_data.earnings_warning = ''

                except Exception as e:
                    messages.error(request, 'Stock does not have an earnings call date defined.')
                    print(f'Stock {stock} does not have an earnings call date defined.')
                    earnings = None    

                tan_deviation_angle = math.tan(math.radians(settings.DEVIATION_ANGLE))


                # Stock Trend - 30 days sample
                a_stock_30, a_macd_30, a_mfi_30, rsi, week1, week2, week3 = trends(stock,30)

                # a_stock_30 = stock_regression(stock, 30)
                stock_data.stock_trend_30 = round(a_stock_30,2)

                # MACD trend
                # a_macd_30 = trend_calculator(stock, 'MACD', period=30)
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
                # a_mfi_30 = trend_calculator(stock, 'MFI', period=30)
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
                a_stock_14, a_macd_14, a_mfi_14, rsi_14, week1, week2, week3= trends(stock,14) # rsi_14 is just for unpacking. it's not user.

                # a_stock_14 = stock_regression(stock, 14)
                stock_data.stock_trend_14 = round(a_stock_14,2)

                # MACD trend
                # a_macd_14 = trend_calculator(stock, 'MACD', period=14)
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
                # a_mfi_14 = trend_calculator(stock, 'MFI', period=14)
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

                # RSI
                # rsi = last_rsi(stock, period=30)
                stock_data.rsi = rsi
                if rsi > 0 and rsi <=30:
                    stock_data.rsi_color = 'red'
                elif rsi > 30 and rsi <= 65:
                    stock_data.rsi_color = 'orange'
                elif rsi > 65 and rsi <=100:
                    stock_data.rsi_color = 'green'
                else:
                    stock_data.rsi_color = ''

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
                    print(f'ERROR Adding Stock. Reason: {e}')
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

        ## Enable email support
        elif 'email_enable' in request.POST:
            print('>> Enable Email <<')
            try:
                email_enable = EmailSupport.objects.all().first()
                if email_enable.enabled:
                    email_enable.enabled = False
                    context['email_enabled'] = False
                    email_enable.save()

                    # Resetting all email alerts to False
                    reset_email_alerts()

                else:
                    email_enable.enabled = True
                    context['email_enabled'] = True
                    email_enable.save()
            except:
                email_enable = EmailSupport()
                email_enable.enabled = True
                context['email_enabled'] = True
                email_enable.save()

        # Update sample period for MACD and MFI calculations
        elif 'sample_period' in request.POST:
            print('>> Sampling <<')
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
        
        
        
        # Stock Delete
        elif 'delete_stock' in request.POST:
            print('>> Deleting <<')
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

        # Save stock to history
        elif 'save_stock' in request.POST:
            print('>> Saving <<')
            stock_id = request.POST['save_stock']
            stock_data = StockData.objects.get(id=stock_id)
            stock_data.saved_to_history = True  
            stock_data.save()
            messages.warning(request, f"Stock was saved. You can review it's data on the History page.")

            stocks = StockData.objects.filter(table_index=table_index).order_by('week_3')
            context['stocks'] = stocks
            return render(request, 'kadima/home.html', context)

        elif 'alarm_stock' in request.POST:
            print('>> Alarm Stock <<')
            stock_id = request.POST['alarm_stock']
            stock_data = StockData.objects.get(id=stock_id)
            stock_data.stock_alarm = True
            stock_data.stock_load_price = stock_data.stock_current_price
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

    # Laoad current stocks
    current_stocks = StockData.objects.all()
    current_stocks_list = dict()
    for stock in current_stocks:
        current_stocks_list[stock.id] = stock.ticker
    
    ib_api_wrapper(request, updated_stock_list=current_stocks_list, action=UPADATE_STOCKS)


    # Updating values
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
    # context = {}
    # print('Updating values before disconnecting')
    # update_values(request)

    # Resetting all email alerts to False
    reset_email_alerts()

    # Resetting the alarms
    reset_alarms()

    print('Stopping the IB API...')
    ib_api_wrapper(request,action=STOP_API )
    sleep(2)
    return 
