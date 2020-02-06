import random
import json
import pandas as pd
import math
import matplotlib
import matplotlib.pyplot as plt
import numpy as np 
import datetime
import re

from math import *
from numpy import round

from datetime import timedelta
from pandas_datareader import data

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseBadRequest, HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse_lazy, reverse
from django.contrib import messages

from yahoo_earnings_calendar import YahooEarningsCalendar

from ib_api.views import *
from kadima.k_utils import *

from .models import StockData
from .forms import DateForm
from .ml_models import *

# Create and configure logger
import logging

LOG_FORMAT = '%(levelname)s %(asctime)s - %(message)s'
logging.basicConfig(filename='./log.log',level=logging.INFO,format=LOG_FORMAT, filemode='w')
logger = logging.getLogger()

TODAY = datetime.datetime.today()
MAX_PAST = TODAY - timedelta(30)
UPADATE_STOCKS = 'update'


def history(request):
    context = {}
    saved_stocks = StockData.objects.filter(saved_to_history=True)
    context['stocks'] = saved_stocks

    date_picker = DateForm()

    if request.method == 'POST':
        if 'update_stock' in str(request.POST):

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

            filtered_stocks = StockData.objects.filter(saved_to_history=True, stock_date__range=[start, end])
            context['stocks'] = filtered_stocks

            # return HttpResponseRedirect(request.path_info)
            return render(request, 'kadima/history.html', context)

        else:
            saved_stocks = StockData.objects.filter(saved_to_history=True)
            context['stocks'] = saved_stocks
            
            return render(request, 'kadima/history.html', context)
    
    return render(request, 'kadima/history.html', context)

def home(request):
    table_index = 0
    context = {}

    if request.session['api_connection'] == True:
        context['api_status'] = 'active'

    indeces = ['^IXIC', '^GSPC', '^DJI']
    today = datetime.datetime.today()
    start_date = TODAY - timedelta(5) 
    end_date = TODAY

    nasdaq_df = data.get_data_yahoo(indeces[0], start=start_date, end=end_date)
    snp_df = data.get_data_yahoo(indeces[1], start=start_date, end=end_date)
    dow_df = data.get_data_yahoo(indeces[2], start=start_date, end=end_date)

    nasdaq_df['change'] = nasdaq_df['Close'].pct_change()
    snp_df['change'] = snp_df['Close'].pct_change()
    dow_df['change'] = dow_df['Close'].pct_change()

    nasdaq_change = nasdaq_df['change'].iloc[-1]
    snp_change = snp_df['change'].iloc[-1]
    dow_change = dow_df['change'].iloc[-1]

    context['nas_value'] = float("%0.2f"%nasdaq_df['Close'].iloc[-1])
    context['snp_value'] = float("%0.2f"%snp_df['Close'].iloc[-1])
    context['dow_value'] = float("%0.2f"%dow_df['Close'].iloc[-1])

    context['nas_color'] = change_check(nasdaq_change)
    context['snp_color'] = change_check(snp_change)
    context['dow_color'] = change_check(dow_change)

    context['nas_change'] = float("%0.2f"%(nasdaq_change * 100))
    context['snp_change'] = float("%0.2f"%(snp_change * 100))
    context['dow_change'] = float("%0.2f"%(dow_change * 100))


    if request.method == 'POST':

        if 'connect_ib_api' in request.POST:
            print('Connecting API...')
            
            ib_api_wrapper(request)
            
            timer = 1
            while timer < 3:
                sleep(1)
                print('Sleeping...')
                timer += 1 

            current_stocks = StockData.objects.filter(table_index=table_index)
            current_stocks_list = dict()
            for stock in current_stocks:
                current_stocks_list[stock.id] = stock.ticker
            
            ib_api_wrapper(request, updated_stock_list=current_stocks_list, action=UPADATE_STOCKS)

            request.session['api_connection'] = True
            print(f'API STATUS: {request.session["api_connection"]}')
            context['api_status'] = 'active'

            stocks = StockData.objects.filter(table_index=table_index)
            context['stocks'] = stocks

            return render(request, 'kadima/home.html', context)


        elif 'add_stock' in request.POST:
            stock  = request.POST.get('stock')
            print(f'Stock: {stock}')
            context['stock'] = stock
            try:
                stock_df = data.get_data_yahoo(stock, start=MAX_PAST, end=today)
            except Exception as e:
                messages.info(request, 'Stock does not exists')
                return render(request, 'kadima/home.html', context)

            stock_data = StockData()
            
            stock_data.table_index = table_index

            stock_data.stock_date = stock_df.index[-1]
            stock_data.stock_displayed_date = date_obj_to_date(pd.Timestamp("today"), date_format='slash')

            stock_data.ticker = stock.upper()
            stock_data.stock_price = float("%0.2f"%stock_df['Close'].iloc[-1])

            stock_data.week_1 = float("%0.2f"%week_values(stock_df, 1))
            stock_data.week_2 = float("%0.2f"%week_values(stock_df, 2))
            stock_data.week_3 = float("%0.2f"%week_values(stock_df, 3))
            stock_data.week_5 = float("%0.2f"%week_values(stock_df, 5))

            stock_data.week_1_color = week_color(stock_data.week_1)
            stock_data.week_2_color = week_color(stock_data.week_2)
            stock_data.week_3_color = week_color(stock_data.week_3)
            stock_data.week_5_color = week_color(stock_data.week_5)

            gaps, gaps_colors = gap_check(stock_df)

            if len(gaps) == 3:
                stock_data.gap_1 = gaps[0]
                stock_data.gap_2 = gaps[1]
                stock_data.gap_3 = gaps[2]

                stock_data.gap_1_color = gaps_colors[0]
                stock_data.gap_2_color = gaps_colors[1]
                stock_data.gap_3_color = gaps_colors[2]
            elif len(gaps) == 2:
                stock_data.gap_1 = gaps[0]
                stock_data.gap_2 = gaps[1]

                stock_data.gap_1_color = gaps_colors[0]
                stock_data.gap_2_color = gaps_colors[1]

            elif len(gaps) == 1:
                stock_data.gap_1 = gaps[0]

                stock_data.gap_1_color = gaps_colors[0]
            else:
                pass


            # Earning dates
            yec = YahooEarningsCalendar()
            try:
                timestmp = yec.get_next_earnings_date(stock)
                earnings_date_obj = datetime.datetime.fromtimestamp(timestmp)
                stock_data.earnings_call = earnings_date_obj
            except Exception as e:
                messages.error(request, 'Stock does not have an earnings call date defined.')
                earnings_date_obj = today                

            stock_data.earnings_call_displayed = date_obj_to_date(earnings_date_obj, date_format='slash')
            
            if (earnings_date_obj - today).days <= 7:
                stock_data.earnings_warning = 'blink-bg'
            else:
                pass


            # Stock Trend 
            a_stock = stock_regression(stock)
            stock_data.stock_trend = round(a_stock,2)

            # MACD trend
            a_macd = trend_calculator(stock, 'MACD')
            stock_data.macd_trend = round(a_macd,2)

            if (a_stock > 0 and a_macd < 0) or (a_stock < 0 and a_macd > 0):
                stock_data.macd_clash = True
                stock_data.macd_color = 'red'
            else:
                stock_data.macd_clash = False
                stock_data.macd_color = 'green'

            # MFI trend
            a_mfi = trend_calculator(stock, 'MFI')
            stock_data.money_flow_trend = round(a_mfi,2)

            if (a_stock > 0 and a_mfi < 0) or (a_stock < 0 and a_mfi > 0):
                stock_data.mfi_clash = True
                stock_data.mfi_color = 'red'
            else:
                stock_data.mfi_clash = False
                stock_data.mfi_color = 'green'


            old_stocks = StockData.objects.filter(table_index=table_index)
            old_stocks_list = []
            for stock in old_stocks:
                old_stocks_list.append(stock.id)

            ## Adding the stock saving to DB
            stock_data.save()
            new_stocks = StockData.objects.filter(table_index=table_index)
            context['stocks'] = new_stocks

            
            ## Updating the streaming IB API data with added stock
            new_stocks_list = dict()
            for stock in new_stocks:
                new_stocks_list[stock.id] = stock.ticker
            
            ib_api_wrapper(request,old_stocks_list, new_stocks_list, action=UPADATE_STOCKS)


            return render(request, 'kadima/home.html', context)
        
        elif 'delete_stock' in request.POST:
            old_stocks = StockData.objects.filter(table_index=table_index)
            old_stocks_list = []
            for stock in old_stocks:
                old_stocks_list.append(stock.id)

            # Deleting a stock from DB
            StockData.objects.filter(id=request.POST['delete_stock']).delete()
            new_stocks = StockData.objects.filter(table_index=table_index)
            context['stocks'] = new_stocks

            ## Updating the streaming IB API data with deleted stock
            new_stocks_list = dict()
            for stock in new_stocks:
                new_stocks_list[stock.id] = stock.ticker
            
            ib_api_wrapper(request,old_stocks_list, new_stocks_list, action=UPADATE_STOCKS)
            # ib_api_wrapper(request,old_stocks_list=old_stocks_list, updated_stock_list=new_stocks_list, action=UPADATE_STOCKS)


            return render(request, 'kadima/home.html', context)

        elif 'save_stock' in request.POST:
            stock_id = request.POST['save_stock']
            stock_data = StockData.objects.get(id=stock_id)
            stock_data.saved_to_history = True  
            stock_data.save()
            messages.warning(request, f"Stock was saved. You can review it's data in the history page.")

            stocks = StockData.objects.filter(table_index=table_index)
            context['stocks'] = stocks
            return render(request, 'kadima/home.html', context)

        elif 'sort_by_date' in request.POST:
            saved_stocks = StockData.objects.filter(table_index=table_index).order_by('stock_date')
            context['stocks'] = saved_stocks
            return render(request, 'kadima/home.html', context)

        elif 'sort_by_stock' in request.POST:
            saved_stocks = StockData.objects.filter(table_index=table_index).order_by('ticker')
            context['stocks'] = saved_stocks
            return render(request, 'kadima/home.html', context)

        elif 'sort_by_price' in request.POST:
            saved_stocks = StockData.objects.filter(table_index=table_index).order_by('stock_price')
            context['stocks'] = saved_stocks
            return render(request, 'kadima/home.html', context)

        elif 'sort_by_week3' in request.POST:
            saved_stocks = StockData.objects.filter(table_index=table_index).order_by('-week_3')
            context['stocks'] = saved_stocks
            return render(request, 'kadima/home.html', context)

        elif 'sort_by_gap1' in request.POST:
            saved_stocks = StockData.objects.filter(table_index=table_index).order_by('-gap_1')
            context['stocks'] = saved_stocks
            return render(request, 'kadima/home.html', context)

        else:
            stocks = StockData.objects.filter(table_index=table_index)
            context['stocks'] = stocks

            return render(request, 'kadima/home.html', context)


    else:
        stocks = StockData.objects.filter(table_index=table_index)
        context['stocks'] = stocks

        return render(request, 'kadima/home.html', context)

def week_values(stock_df, week_index):
    if week_index == 1:
        last_5_max = stock_df['Close'][-5:].values.max()
        last_5_min = stock_df['Close'][-5:].values.min()
        current_price = stock_df['Close'][-5:].values[-1]

        relative_value = ((current_price - last_5_min) / (last_5_max - last_5_min)) * 100

    elif week_index == 2:
        last_10_max = stock_df['Close'][-10:].values.max()
        last_10_min = stock_df['Close'][-10:].values.min()
        current_price = stock_df['Close'][-10:].values[-1]

        relative_value = ((current_price - last_10_min) / (last_10_max - last_10_min)) * 100

    elif week_index == 3:
        last_15_max = stock_df['Close'][-15:].values.max()
        last_15_min = stock_df['Close'][-15:].values.min()
        current_price = stock_df['Close'][-15:].values[-1]

        relative_value = ((current_price - last_15_min) / (last_15_max - last_15_min)) * 100

    elif week_index == 5:
        last_25_max = stock_df['Close'][-25:].values.max()
        last_25_min = stock_df['Close'][-25:].values.min()
        current_price = stock_df['Close'][-25:].values[-1]

        relative_value = ((current_price - last_25_min) / (last_25_max - last_25_min)) * 100
    
    else:
        last_5_max = stock_df['Close'][-5:].values.max()
        last_5_min = stock_df['Close'][-5:].values.min()
        current_price = stock_df['Close'][-5:].values[-1]

        relative_value = ((current_price - last_5_min) / (last_5_max - last_5_min)) * 100

    return relative_value

def gap_check(stock_df):
    days_back = 1
    gap_count = 0
    gaps = []
    gaps_colors = []
    
    while gap_count < 4 and days_back < len(stock_df)/2:
        open_value = stock_df.loc[stock_df.index[-days_back]]['Open']
        close_value = stock_df.loc[stock_df.index[-days_back-1]]['Close']
        delta_price = open_value - close_value
        delta_rate = (delta_price / close_value) * 100
        if delta_rate > 1.26:
            gap_count +=1
            gaps.append(float("%0.2f"%delta_rate))
            gaps_colors.append('green')
            days_back += 1
        elif delta_rate >= 1:
            gap_count +=1
            gaps.append(float("%0.2f"%delta_rate))
            gaps_colors.append('orange')
            days_back += 1
        elif delta_rate > 0.75:
            gap_count +=1
            gaps.append(float("%0.2f"%delta_rate))
            gaps_colors.append('red')
            days_back += 1        
        else:
            days_back += 1        

    print(f'gaps: {gaps} \n gaps_colors: {gaps_colors}')

    return gaps, gaps_colors

def table_2(request):

    table_index = 2
    context = {}
    indeces = ['^IXIC', '^GSPC', '^DJI']
    today = datetime.datetime.today()
    start_date = TODAY - timedelta(5) 
    end_date = TODAY

    nasdaq_df = data.get_data_yahoo(indeces[0], start=start_date, end=end_date)
    snp_df = data.get_data_yahoo(indeces[1], start=start_date, end=end_date)
    dow_df = data.get_data_yahoo(indeces[2], start=start_date, end=end_date)

    nasdaq_df['change'] = nasdaq_df['Close'].pct_change()
    snp_df['change'] = snp_df['Close'].pct_change()
    dow_df['change'] = dow_df['Close'].pct_change()

    nasdaq_change = nasdaq_df['change'].iloc[-1]
    snp_change = snp_df['change'].iloc[-1]
    dow_change = dow_df['change'].iloc[-1]

    context['nas_value'] = float("%0.2f"%nasdaq_df['Close'].iloc[-1])
    context['snp_value'] = float("%0.2f"%snp_df['Close'].iloc[-1])
    context['dow_value'] = float("%0.2f"%dow_df['Close'].iloc[-1])

    context['nas_color'] = change_check(nasdaq_change)
    context['snp_color'] = change_check(snp_change)
    context['dow_color'] = change_check(dow_change)

    context['nas_change'] = float("%0.2f"%(nasdaq_change * 100))
    context['snp_change'] = float("%0.2f"%(snp_change * 100))
    context['dow_change'] = float("%0.2f"%(dow_change * 100))


    if request.method == 'POST':
        if 'add_stock' in request.POST:
            stock  = request.POST.get('stock')
            print(f'Stock: {stock}')
            context['stock'] = stock
            try:
                stock_df = data.get_data_yahoo(stock, start=MAX_PAST, end=today)
            except Exception as e:
                messages.info(request, 'Stock does not exists')

                stocks = StockData.objects.filter(table_index=table_index)
                context['stocks'] = stocks

                return render(request, 'kadima/table-2.html', context)

            stock_data = StockData()
            
            stock_data.table_index = table_index

            stock_data.stock_date = stock_df.index[-1]
            stock_data.stock_displayed_date = date_obj_to_date(pd.Timestamp("today"), date_format='slash')

            stock_data.ticker = stock.upper()
            stock_data.stock_price = float("%0.2f"%stock_df['Close'].iloc[-1])

            stock_data.week_1 = float("%0.2f"%week_values(stock_df, 1))
            stock_data.week_2 = float("%0.2f"%week_values(stock_df, 2))
            stock_data.week_3 = float("%0.2f"%week_values(stock_df, 3))
            stock_data.week_5 = float("%0.2f"%week_values(stock_df, 5))

            stock_data.week_1_color = week_color(stock_data.week_1)
            stock_data.week_2_color = week_color(stock_data.week_2)
            stock_data.week_3_color = week_color(stock_data.week_3)
            stock_data.week_5_color = week_color(stock_data.week_5)

            gaps, gaps_colors = gap_check(stock_df)

            if len(gaps) == 3:
                stock_data.gap_1 = gaps[0]
                stock_data.gap_2 = gaps[1]
                stock_data.gap_3 = gaps[2]

                stock_data.gap_1_color = gaps_colors[0]
                stock_data.gap_2_color = gaps_colors[1]
                stock_data.gap_3_color = gaps_colors[2]
            elif len(gaps) == 2:
                stock_data.gap_1 = gaps[0]
                stock_data.gap_2 = gaps[1]

                stock_data.gap_1_color = gaps_colors[0]
                stock_data.gap_2_color = gaps_colors[1]

            elif len(gaps) == 1:
                stock_data.gap_1 = gaps[0]

                stock_data.gap_1_color = gaps_colors[0]
            else:
                pass


            # Earning dates
            yec = YahooEarningsCalendar()
            try:
                timestmp = yec.get_next_earnings_date(stock)
                earnings_date_obj = datetime.datetime.fromtimestamp(timestmp)
                stock_data.earnings_call = earnings_date_obj
            except Exception as e:
                messages.error(request, 'Stock does not have an earnings call date defined.')
                earnings_date_obj = today                

            stock_data.earnings_call_displayed = date_obj_to_date(earnings_date_obj, date_format='slash')
            
            if (earnings_date_obj - today).days <= 7:
                stock_data.earnings_warning = 'blink-bg'
            else:
                pass


            # Stock Trend 
            a_stock = stock_regression(stock)
            stock_data.stock_trend = round(a_stock,2)

            # MACD trend
            a_macd = trend_calculator(stock, 'MACD')
            stock_data.macd_trend = round(a_macd,2)

            if (a_stock > 0 and a_macd < 0) or (a_stock < 0 and a_macd > 0):
                stock_data.macd_clash = True
                stock_data.macd_color = 'red'
            else:
                stock_data.macd_clash = False
                stock_data.macd_color = 'green'

            # MFI trend
            a_mfi = trend_calculator(stock, 'MFI')
            stock_data.money_flow_trend = round(a_mfi,2)

            if (a_stock > 0 and a_mfi < 0) or (a_stock < 0 and a_mfi > 0):
                stock_data.mfi_clash = True
                stock_data.mfi_color = 'red'
            else:
                stock_data.mfi_clash = False
                stock_data.mfi_color = 'green'

            stock_data.save()

            stocks = StockData.objects.filter(table_index=table_index)
            context['stocks'] = stocks
            # context['stock_date'] = st_date

            return render(request, 'kadima/table-2.html', context)
        
        elif 'delete_stock' in request.POST:
            StockData.objects.filter(id=request.POST['delete_stock']).delete()

            stocks = StockData.objects.filter(table_index=table_index)
            context['stocks'] = stocks

            return render(request, 'kadima/table-2.html', context)

        elif 'save_stock' in request.POST:
            stock_id = request.POST['save_stock']
            stock_data = StockData.objects.get(id=stock_id)
            stock_data.saved_to_history = True  
            stock_data.save()
            messages.warning(request, f"Stock was saved. You can review it's data in the history page.")

            stocks = StockData.objects.filter(table_index=table_index)
            context['stocks'] = stocks
            return render(request, 'kadima/table-2.html', context)

        elif 'sort_by_date' in request.POST:
            saved_stocks = StockData.objects.filter(table_index=table_index).order_by('stock_date')
            context['stocks'] = saved_stocks
            return render(request, 'kadima/table-2.html', context)

        elif 'sort_by_stock' in request.POST:
            saved_stocks = StockData.objects.filter(table_index=table_index).order_by('ticker')
            context['stocks'] = saved_stocks
            return render(request, 'kadima/table-2.html', context)

        elif 'sort_by_price' in request.POST:
            saved_stocks = StockData.objects.filter(table_index=table_index).order_by('stock_price')
            context['stocks'] = saved_stocks
            return render(request, 'kadima/table-2.html', context)

        elif 'sort_by_week3' in request.POST:
            saved_stocks = StockData.objects.filter(table_index=table_index).order_by('-week_3')
            context['stocks'] = saved_stocks
            return render(request, 'kadima/table-2.html', context)

        elif 'sort_by_gap1' in request.POST:
            saved_stocks = StockData.objects.filter(table_index=table_index).order_by('-gap_1')
            context['stocks'] = saved_stocks
            return render(request, 'kadima/table-2.html', context)

        else:
            stocks = StockData.objects.filter(table_index=table_index)
            context['stocks'] = stocks

            return render(request, 'kadima/table-2.html', context)


    else:
        stocks = StockData.objects.filter(table_index=table_index)
        context['stocks'] = stocks

        return render(request, 'kadima/table-2.html', context)
