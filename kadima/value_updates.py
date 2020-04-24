import datetime
import time
import json
from time import sleep
from datetime import timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor


from django.conf import settings
from django.utils import timezone
from django.contrib import messages

from pandas_datareader import data as fin_data
from yahoo_earnings_calendar import YahooEarningsCalendar


from .models import IndicesData, StockData
from .k_utils import change_check, gap_1_check, date_obj_to_date
from .stock import Stock


# Create and configure logger
import logging
LOG_FORMAT = '%(levelname)s %(asctime)s - %(message)s'
logging.basicConfig(filename='./log.log',level=logging.INFO,format=LOG_FORMAT, filemode='w')
logger = logging.getLogger()

TODAY = datetime.datetime.today()
MAX_PAST = TODAY - timedelta(30)
WORKERS = 15

def update_values(request):

    context = {}
    errors = {}

    # Indexes update
    indexes_update_done, indexes_info = indexes_updates()

    if indexes_update_done:
        context.update(indexes_info)
    else:
        errors['indexes'] = True


    start_run = time.perf_counter()
    # Stocks Update
    # Get the list of current stocks list

    current_stocks = StockData.objects.all()

    # messages.info(request, 'Updading values...')

    for stock in current_stocks:
        stock_to_update = Stock(ticker=stock.ticker, table_index=stock.table_index)
        
        print(f'Updating Stock: {stock.ticker}')
        stock_to_update.update_stock()
        print(f'Finished updating Stock: {stock.ticker}')
        
        stock.stock_displayed_date = stock_to_update.displayed_date
        stock.stock_price = stock_to_update.stock_price

        stock.week_1 = stock_to_update.week_1
        stock.week_1_min = stock_to_update.week_1_min
        stock.week_1_max = stock_to_update.week_1_max
        stock.week_1_color = stock_to_update.week_1_color

        stock.week_2 = stock_to_update.week_2
        stock.week_2_min = stock_to_update.week_2_min
        stock.week_2_max = stock_to_update.week_2_max
        stock.week_2_color = stock_to_update.week_2_color

        stock.week_3 = stock_to_update.week_3
        stock.week_3_min = stock_to_update.week_3_min
        stock.week_3_max = stock_to_update.week_3_max
        stock.week_3_color = stock_to_update.week_3_color

        stock.week_5 = stock_to_update.week_5
        stock.week_5_min = stock_to_update.week_5_min
        stock.week_5_max = stock_to_update.week_5_max
        stock.week_5_color = stock_to_update.week_5_color

        stock.gap_1 = stock_to_update.gap_1
        stock.gap_1_color = stock_to_update.gap_1_color

        # stock.earnings_call = stock_to_update.earnings_call
        # stock.earnings_call_displayed = stock_to_update.earnings_call_displayed
        stock.earnings_warning = stock_to_update.earnings_warning
                
        stock.stock_trend_30 = stock_to_update.trend_30
        
        stock.macd_trend_30 = stock_to_update.macd_30
        stock.macd_30_clash = stock_to_update.macd_30_clash
        stock.macd_30_color = stock_to_update.macd_30_color

        stock.macd_trend_14 = stock_to_update.macd_14
        stock.macd_14_clash = stock_to_update.macd_14_clash
        stock.macd_14_color = stock_to_update.macd_14_color

        stock.money_flow_trend_30 = stock_to_update.mfi_30
        stock.mfi_30_clash = stock_to_update.mfi_30_clash
        stock.mfi_30_color = stock_to_update.mfi_30_color

        stock.money_flow_trend_14 = stock_to_update.mfi_14
        stock.mfi_14_clash = stock_to_update.mfi_14_clash
        stock.mfi_14_color = stock_to_update.mfi_14_color

        stock.save()

    finish_run = time.perf_counter()
    print(f'''
    >>>>>>>>>>
    Finished updating {len(current_stocks)} stocks gaps. Durations: {round(finish_run - start_run,2)} seconds.
    >>>>>>>>>>
    ''')
    return True

def indexes_updates():
    indexes_context = {}
    indeces = ['^IXIC', '^GSPC', '^DJI', '^RUT', '^VIX'] 
    try:
        index_df = fin_data.get_data_yahoo(indeces , start=TODAY - timedelta(5), end=TODAY)
        historical = False
 
    except:
        try:
            historical = True
            historical_index_data = []
            indeces_history_data = IndicesData.objects.all()
            for idx in indeces_history_data:
                historical_index_data.append(idx.index_prev_close) 
            
        except Exception as e:
            logger.error(f'Failed getting data from Yahoo.')
            print(f'Failed getting data from Yahoo. Reason: {e}')
            return False, e

    # Setting the previsous day close value for the indices.
    try:
        nasdaq_data = IndicesData()
        nasdaq_data.index_symbol = 'Nasdaq'
        # nasdaq_data.index_prev_close = round(float(nasdaq_df['Close'].iloc[-2]),2)
        if index_df.index[-1].day == TODAY.day:
            nasdaq_data.index_prev_close = round(index_df['Close']['^IXIC'][-2],2)
        else:
            nasdaq_data.index_prev_close = round(index_df['Close']['^IXIC'][-1],2)

        nasdaq_data.index_api_id = 55555
        nasdaq_data.save()

        snp_data = IndicesData()
        snp_data.index_symbol = 'S&P'
        # snp_data.index_prev_close = round(float(snp_df['Close'].iloc[-2]),2)

        if index_df.index[-1].day == TODAY.day:
            snp_data.index_prev_close = round(index_df['Close']['^GSPC'][-2],2)
        else:
            snp_data.index_prev_close = round(index_df['Close']['^GSPC'][-1],2)
        
        snp_data.index_api_id = 88888
        snp_data.save()

        dow_data = IndicesData()
        dow_data.index_symbol = 'Dow-Jones'
        # dow_data.index_prev_close = round(float(dow_df['Close'].iloc[-2]),2)
        if index_df.index[-1].day == TODAY.day:
            dow_data.index_prev_close = round(index_df['Close']['^DJI'][-2],2)
        else:
            dow_data.index_prev_close = round(index_df['Close']['^DJI'][-1],2)
        
        dow_data.index_api_id = 77777
        dow_data.save()

        vix_data = IndicesData()
        vix_data.index_symbol = 'VIX'
        if index_df.index[-1].day == TODAY.day:
            vix_data.index_prev_close = round(index_df['Close']['^VIX'][-2],2)
        else:
            vix_data.index_prev_close = round(index_df['Close']['^VIX'][-1],2)
        
        vix_data.index_api_id = 11111
        vix_data.save()

        r2k_data = IndicesData()
        r2k_data.index_symbol = 'Russell-2k'
        # dow_data.index_prev_close = round(float(dow_df['Close'].iloc[-2]),2)
        if index_df.index[-1].day == TODAY.day:
            r2k_data.index_prev_close = round(index_df['Close']['^RUT'][-2],2)
        else:
            r2k_data.index_prev_close = round(index_df['Close']['^RUT'][-1],2)
        
        r2k_data.index_api_id = 22222
        r2k_data.save()


    except Exception as e:
        logger.error(f'Failed saving indexes data to DB.')
        print(f'Failed daving indexes data to DB')
        messages.error('Failed to update DB with Indeces data.')
        # return False, e

    nasdaq_change = 0 if historical else round(index_df['Close']['^IXIC'].pct_change()[1],2)
    snp_change = 0 if historical else round(index_df['Close']['^GSPC'].pct_change()[1],2)
    dow_change = 0 if historical else round(index_df['Close']['^DJI'].pct_change()[1],2)
    vix_change = 0 if historical else round(index_df['Close']['^VIX'].pct_change()[1],2)
    r2k_change = 0 if historical else round(index_df['Close']['^RUT'].pct_change()[1],2)

    indexes_context['nas_value'] = historical_index_data[0] if historical else round(index_df['Close']['^IXIC'][1],2)
    indexes_context['snp_value'] = historical_index_data[1] if historical else round(index_df['Close']['^GSPC'][1],2)
    indexes_context['dow_value'] = historical_index_data[2] if historical else round(index_df['Close']['^DJI'][1],2)
    indexes_context['vix_value'] = historical_index_data[2] if historical else round(index_df['Close']['^VIX'][1],2)
    indexes_context['r2k_value'] = historical_index_data[2] if historical else round(index_df['Close']['^RUT'][1],2)

    indexes_context['nas_color'] = change_check(nasdaq_change)
    indexes_context['snp_color'] = change_check(snp_change)
    indexes_context['dow_color'] = change_check(dow_change)
    indexes_context['vix_color'] = change_check(vix_change)
    indexes_context['r2k_color'] = change_check(r2k_change)

    indexes_context['nas_change'] = float("%0.2f"%(nasdaq_change * 100))
    indexes_context['snp_change'] = float("%0.2f"%(snp_change * 100))
    indexes_context['dow_change'] = float("%0.2f"%(dow_change * 100))
    indexes_context['vix_change'] = float("%0.2f"%(vix_change * 100))
    indexes_context['r2k_change'] = float("%0.2f"%(r2k_change * 100))

    return True, indexes_context

# def update_stock_LOCAL(ticker):
#     stock = StockData.objects.get(ticker=ticker)

#     if stock: # Stock is in the table thus continue to update or...
#         pass
#     else:
#         stock = StockData() # Create a new stock entry
    
#     stock_df = fin_data.get_data_yahoo(str(stock), start=MAX_PAST, end=TODAY)

#     stock.prev_close = round(stock_df.loc[stock_df.index[-2]]['Close'],2)
#     stock.todays_open = round(stock_df.loc[stock_df.index[-1]]['Open'],2)
#     stock.stock_date = stock_df.index[-1]

#     gap_1, gap_1_color = gap_1_check(stock.prev_close, stock.todays_open)
#     stock.gap_1 = gap_1
#     stock.gap_1_color = gap_1_color

# def update_gaps_wrapper():
#     current_stocks = StockData.objects.all()
#     stocks_tickers = []
#     for t in current_stocks:
#         stocks_tickers.append(t.ticker)

#     with ThreadPoolExecutor(max_workers=WORKERS) as executor:
#         futures = [executor.submit(update_stock_gaps, ticker) for ticker in stocks_tickers]
#         for future in as_completed(futures):
#             # print(f'{future.result()}')
#             pass
    
#     return True,len(current_stocks)

# def update_stock_gaps(ticker):
#     stock = StockData.objects.get(ticker=ticker)
#     stock_df = fin_data.get_data_yahoo(str(stock), start=MAX_PAST, end=TODAY)
    
#     stock.prev_close = round(stock_df.loc[stock_df.index[-2]]['Close'],2)
#     stock.todays_open = round(stock_df.loc[stock_df.index[-1]]['Open'],2)
#     # stock.stock_date = stock_df.index[-1]

#     gap_1, gap_1_color = gap_1_check(stock.prev_close, stock.todays_open)
#     stock.gap_1 = gap_1
#     stock.gap_1_color = gap_1_color

#     # Canceling the flag for updating the gaps
#     stock.updading_gap_1_flag = False
    
#     stock.save()
#     sleep(2)
    
#     msg = f'>>> Updating {ticker}'

#     return msg

# def stock_earnings_update(ticker):
#     print(f'Updating earnings for {ticker}')
#     try:
#         yec = YahooEarningsCalendar()

#         # Updating the DB
#         stock_to_update = StockData.objects.get(ticker=ticker)

#         try:
#             timestmp = yec.get_next_earnings_date(ticker)
#             earnings_date_obj = datetime.datetime.fromtimestamp(timestmp)
#             stock_to_update.earnings_call = earnings_date_obj
#         except Exception as e:
#             earnings_date_obj = None    

#         if earnings_date_obj:
#             stock_to_update.earnings_call_displayed = date_obj_to_date(earnings_date_obj, date_format='slash')
        
#             if (earnings_date_obj - TODAY).days <= 7 and (earnings_date_obj - TODAY).days >= 0:
#                 print(f"***************{(earnings_date_obj - TODAY).days}****************")
#                 stock_to_update.earnings_warning = 'blink-bg'
#             else:
#                 pass
#         else:
#             pass

#         stock_to_update.save()

#         return True
    
#     except Exception as e:
#         logger.error('Failed updating the earnings')
#         return False


# def earnings_update():
#     current_stocks = StockData.objects.all()
#     try:
#         yec = YahooEarningsCalendar()

#         for stock in current_stocks:
 
#             try:
#                 timestmp = yec.get_next_earnings_date(stock)
#                 earnings_date_obj = datetime.datetime.fromtimestamp(timestmp)
#                 stock.earnings_call = earnings_date_obj
#             except Exception as e:
#                 earnings_date_obj = None    

#             if earnings_date_obj:
#                 stock.earnings_call_displayed = date_obj_to_date(earnings_date_obj, date_format='slash')
            
#                 if (earnings_date_obj - TODAY).days <= 7 and (earnings_date_obj - TODAY).days >= 0:
#                     print(f"***************{(earnings_date_obj - TODAY).days}****************")
#                     stock.earnings_warning = 'blink-bg'
#                 else:
#                     pass
#             else:
#                 pass

#             stock.save()

#         return True
    
#     except Exception as e:
#         logger.error('Failed updating the earnings')
#         return False

        
