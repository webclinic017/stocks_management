import datetime
import time
import json
import pandas as pd
import numpy as np
from pandas_datareader import data as fin_data
from time import sleep
from datetime import timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
from sklearn.linear_model import LinearRegression

from django.conf import settings
from django.utils import timezone

# 3rd Party APIs
from yahoo_earnings_calendar import YahooEarningsCalendar
import yfinance as yf
from finta import TA


from .models import IndicesData, StockData
from .k_utils import change_check, gap_1_check, date_obj_to_date, week_values, week_color

class Stock():

    def __init__(self, ticker, table_index):
        self.today = datetime.datetime.today()
        self.ticker = ticker
        self.table_index = 1
        self.date = ''
        self.displayed_date = ''

        self.stock_price = None
        self.prev_close = None
        self.todays_open = None

        self.trend = None
        self.macd = None
        self.mfi = None

        self.week_1 = None
        self.week_1_min = None
        self.week_1_max = None

        self.week_2 = None
        self.week_2_min = None
        self.week_2_max = None

        self.week_3 = None
        self.week_3_min = None
        self.week_3_max = None

        self.week_5 = None
        self.week_5_min =None
        self.week_5_max = None

        self.week_1_color = ''
        self.week_2_color = ''
        self.week_3_color = ''
        self.week_5_color = ''

        self.gap_1 = None
        self.gap_1_color = ''
        # updading_gap_1_flag = models.BooleanField(default=False, null=True)

        self.macd_clash = False
        self.mfi_clash = False
        self.macd_color = ''
        self.mfi_color = ''

        self.earnings_call = None
        self.earnings_call_displayed = ''
        self.earnings_warning = ''

        self.dividend_date = ''
        self.dividend = None
    
    def update_stock(self):
    
        self.stock_df = fin_data.get_data_yahoo(str(self.ticker), start=self.today - timedelta(44), end=self.today)

        self.stock_price = round(self.stock_df.loc[self.stock_df.index[-1]]['Close'],2)
        self.prev_close = round(self.stock_df.loc[self.stock_df.index[-2]]['Close'],2)
        self.todays_open = round(self.stock_df.loc[self.stock_df.index[-1]]['Open'],2)
        self.date = self.stock_df.index[-1]

        self.gap_1, self.gap_1_color = gap_1_check(self.prev_close, self.todays_open)
        
        self.date = self.stock_df.index[-1]
        self.displayed_date = date_obj_to_date(pd.Timestamp("today"), date_format='slash')

        self.week_1, self.week_1_min, self.week_1_max = week_values(self.stock_df, 5)
        self.week_2, self.week_2_min, self.week_2_max = week_values(self.stock_df, 10)
        self.week_3, self.week_3_min, self.week_3_max = week_values(self.stock_df, 15)
        self.week_5, self.week_5_min, self.week_5_max = week_values(self.stock_df, 25)

        self.week_1_color = week_color(self.week_1)
        self.week_2_color = week_color(self.week_2)
        self.week_3_color = week_color(self.week_3, week3=True)
        self.week_5_color = week_color(self.week_5)

        self.trend = self.stock_regression()
        self.macd = self.macd_regression()
        self.mfi = self.mfi_regression()

        if (self.trend > 0 and self.macd < 0) or (self.trend < 0 and self.macd > 0):
            self.macd_clash = True
            self.macd_color = 'red'
        else:
            self.macd_clash = False
            self.macd_color = 'green'

        if (self.trend > 0 and self.mfi < 0) or (self.trend < 0 and self.mfi > 0):
            self.mfi_clash = True
            self.mfi_color = 'red'
        else:
            self.mfi_clash = False
            self.mfi_color = 'green'
        
        self.earnings_call, self.earnings_call_displayed, self.earnings_warning = self.get_earnings()

    def stock_regression(self):
        
        df = self.stock_df.copy().reset_index()
        prices = df['Close'].tolist()
        dates = df.index.tolist()
        dates = np.reshape(dates, (len(dates),1))
        prices = np.reshape(prices, (len(prices),1))
        regressor = LinearRegression().fit(dates, prices)

        # Slop of Y = ax + b    
        a = regressor.coef_[0]
        return a
    
    def macd_regression(self):
        df = self.stock_df.copy().reset_index()
        dates = df.index.tolist()
        dates = np.reshape(dates, (len(dates),1))
        df_ohlc = df.rename(columns={"High": "high", "Low": "low", 'Open':'open', 'Close':'close', 'Volume':'volume', 'Adj Close':'adj close'})
        df_macd = TA.MACD(df_ohlc)
        df_macd_list = df_macd['MACD'].tolist()
        df_macd_points = np.reshape(df_macd_list, (len(df_macd_list),1))

        macd_regressor = LinearRegression().fit(dates,df_macd_points)

        macd_a = macd_regressor.coef_[0]
        macd_b = macd_regressor.intercept_

        return macd_a
    
    def mfi_regression(self):
        df = self.stock_df.copy().reset_index()
        dates = df.index.tolist()
        dates = np.reshape(dates, (len(dates),1))
        df_ohlc = df.rename(columns={"High": "high", "Low": "low", 'Open':'open', 'Close':'close', 'Volume':'volume', 'Adj Close':'adj close'})
        df_mfi = TA.MFI(df_ohlc,14)
        df_mfi.fillna(0, inplace=True)

        mfi_regressor = LinearRegression().fit(dates[14:],df_mfi.values[14:])
        
        mfi_a = mfi_regressor.coef_[0]
        mfi_b = mfi_regressor.intercept_
        return mfi_a

    def get_earnings(self):
        yec = YahooEarningsCalendar()
        try:
            timestmp = yec.get_next_earnings_date(self.ticker)
            earnings_date_obj = datetime.datetime.fromtimestamp(timestmp)
            earnings_call = earnings_date_obj
        except Exception as e:
            earnings_date_obj = None    

        if earnings_date_obj:
            earnings_call_displayed = date_obj_to_date(earnings_date_obj, date_format='slash')
        
            if (earnings_date_obj - self.today).days <= 7 and (earnings_date_obj - self.today).days >= 0:
                earnings_warning = 'blink-bg'
            else:
                earnings_warning = ''
        else:
            earnings_call_displayed = None
            earnings_call = None
            earnings_warning = ''

        
        return earnings_call, earnings_call_displayed, earnings_warning

    def get_dividened(self):
        try:
            st = yf.Ticker(self.ticker).dividends.tail(1)
            stock_data.dividend = float(st.values)
            date_arr = str(st.index[0]).split(' ')[0].split('-')
            year = date_arr[0]
            month = date_arr[1]
            day = date_arr[2]
            self.dividend_date = day + '/' + month + '/' + year
        except:
            stock_data.dividend = None
            stock_data.dividend_date = None