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
from yahoo_earnings_calendar import YahooEarningsCalendar
from finta import TA

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

today = datetime.datetime.today()
START = today - timedelta(30) 
END = today

def stock_regression(stock):
    df = data.get_data_yahoo(stock.upper(), start=START, end=END)
    df = df.copy().reset_index()
    prices = df['Close'].tolist()
    dates = df.index.tolist()
    dates = np.reshape(dates, (len(dates),1))
    prices = np.reshape(prices, (len(prices),1))
    regressor = LinearRegression().fit(dates, prices)

    # Slop of Y = ax + b    
    a = regressor.coef_
    return a
    
def macd_regression(stock):
    df = data.get_data_yahoo(stock.upper(), start=START, end=END)
    df = df.copy().reset_index()
    dates = df.index.tolist()
    dates = np.reshape(dates, (len(dates),1))
    df_ohlc = df.rename(columns={"High": "high", "Low": "low", 'Open':'open', 'Close':'close', 'Volume':'volume', 'Adj Close':'adj close'})
    df_macd = TA.MACD(df_ohlc)
    df_macd_list = df_macd['MACD'].tolist()
    df_macd_points = np.reshape(df_macd_list, (len(df_macd_list),1))

    macd_regressor = LinearRegression().fit(dates,df_macd_points)

    a = macd_regressor.coef_
    b = macd_regressor.intercept_
    print(a,b)
    return macd_regressor

def mfi_regression(stock):
    df = data.get_data_yahoo(stock.upper(), start=START, end=END)
    df = df.copy().reset_index()
    dates = df.index.tolist()
    dates = np.reshape(dates, (len(dates),1))
    df_ohlc = df.rename(columns={"High": "high", "Low": "low", 'Open':'open', 'Close':'close', 'Volume':'volume', 'Adj Close':'adj close'})
    df_mfi = TA.MFI(df_ohlc,14)
    df_mfi.fillna(0, inplace=True)

    mfi_regressor = LinearRegression().fit(dates,df_mfi.values)
    
    a = mfi_regressor.coef_
    b = mfi_regressor.intercept_
    print(a,b)
    return mfi_regressor


def trend_calculator(stock, indicator):

    if indicator == 'MFI':
        regressor = mfi_regression(stock)
    elif indicator == 'MACD':
        regressor = macd_regression(stock)

    # Slop of Y = ax + b    
    a = regressor.coef_
    
    return a