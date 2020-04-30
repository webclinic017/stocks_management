import pandas as pd
import math
import matplotlib
import matplotlib.pyplot as plt
import numpy as np 
import datetime
import lxml

from math import *
from datetime import timedelta
from pandas_datareader import data
# from yahoo_earnings_calendar import YahooEarningsCalendar
from finta import TA

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

from .k_utils import week_values, week_color

today = datetime.datetime.today()
START = today - timedelta(30) 
END = today

def stock_regression(stock, period):
    df = data.get_data_yahoo(stock.upper(), start=datetime.datetime.today() - timedelta(44), end=datetime.datetime.today())
    df = df.tail(period).copy().reset_index()
    prices = df['Close'].tolist()
    dates = df.index.tolist()
    dates = np.reshape(dates, (len(dates),1))
    prices = np.reshape(prices, (len(prices),1))
    regressor = LinearRegression().fit(dates, prices)

    # Slop of Y = ax + b    
    a = regressor.coef_[0]
    return a
    
def macd_regression(stock,period):
    df = data.get_data_yahoo(stock.upper(), start=datetime.datetime.today() - timedelta(44), end=datetime.datetime.today())
    df = df.tail(period).copy().reset_index()
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

def mfi_regression(stock, period):
    df = data.get_data_yahoo(stock.upper(), start=START-timedelta(14), end=END)
    df = df.tail(period+14).copy().reset_index()
    dates = df.index.tolist()
    dates = np.reshape(dates, (len(dates),1))
    df_ohlc = df.rename(columns={"High": "high", "Low": "low", 'Open':'open', 'Close':'close', 'Volume':'volume', 'Adj Close':'adj close'})
    df_mfi = TA.MFI(df_ohlc,14)
    df_mfi.fillna(0, inplace=True)

    mfi_regressor = LinearRegression().fit(dates[-14:],df_mfi.values[-14:])
    
    mfi_a = mfi_regressor.coef_[0]
    mfi_b = mfi_regressor.intercept_
    return mfi_a

def last_rsi(stock, period):
    df = data.get_data_yahoo(stock.upper(), start=START-timedelta(14), end=END)
    df = df.tail(period+14).copy().reset_index()
    dates = df.index.tolist()
    dates = np.reshape(dates, (len(dates),1))
    df_ohlc = df.rename(columns={"High": "high", "Low": "low", 'Open':'open', 'Close':'close', 'Volume':'volume', 'Adj Close':'adj close'})
    df_rsi = TA.RSI(df_ohlc,14)
    return round(df_rsi.tail(1).values[0],2)


def trend_calculator(stock, indicator, period):

    # Slop of Y = ax + b    

    if indicator == 'MFI':
        a = mfi_regression(stock, period)
    elif indicator == 'MACD':
        a = macd_regression(stock, period)
    else:
        a = stock_regression(stock, period)

    return a

def trends(stock,period, draw=False):
    stock_df = data.get_data_yahoo(stock.upper(), start=datetime.datetime.today()-timedelta(44), end=datetime.datetime.today())    
    df = stock_df.tail(period).copy().reset_index()
    prices = df['Close'].tolist()
    dates = df.index.tolist()
    dates = np.reshape(dates, (len(dates),1))
    prices = np.reshape(prices, (len(prices),1))
    regressor = LinearRegression().fit(dates, prices)
    a_trend = regressor.coef_[0]

    df_ohlc = df.rename(columns={"High": "high", "Low": "low", 'Open':'open', 'Close':'close', 'Volume':'volume', 'Adj Close':'adj close'})
    df_macd = TA.MACD(df_ohlc)
    df_macd_list = df_macd['MACD'].tolist()
    df_macd_points = np.reshape(df_macd_list, (len(df_macd_list),1))
    macd_regressor = LinearRegression().fit(dates,df_macd_points)
    macd_a = macd_regressor.coef_[0]

    df_mfi = df.tail(period+14).copy().reset_index()
    dates = df_mfi.index.tolist()
    dates = np.reshape(dates, (len(dates),1))
    df_ohlc_mfi = df_mfi.rename(columns={"High": "high", "Low": "low", 'Open':'open', 'Close':'close', 'Volume':'volume', 'Adj Close':'adj close'})
    df_mfi = TA.MFI(df_ohlc_mfi,14)
    df_mfi.fillna(0, inplace=True)
    mfi_regressor = LinearRegression().fit(dates[-14:],df_mfi.values[-14:])    
    mfi_a = mfi_regressor.coef_[0]

    df_rsi = TA.RSI(df_ohlc,14)
    last_rsi = round(df_rsi.tail(1).values[0],2)

    week1 = dict()
    week2 = dict()
    week3 = dict()

    week1['relative_value'], week1['last_min'], week1['last_max'] = week_values(stock_df, 5)
    week2['relative_value'], week2['last_min'], week2['last_max'] = week_values(stock_df, 10)
    week3['relative_value'], week3['last_min'], week3['last_max'] = week_values(stock_df, 15)

    week1['week_1_color'] = week_color(week1['relative_value'])
    week2['week_2_color'] = week_color(week2['relative_value'])
    week3['week_3_color'] = week_color(week3['relative_value'], week3=True)

    return a_trend, macd_a, mfi_a, last_rsi, week1, week2, week3