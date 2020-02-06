from django.shortcuts import render, HttpResponse

import subprocess
import pandas as pd

from subprocess import check_output

from threading import Thread
from time import sleep
from ib_insync import *

'''
IB-InSync Docs: https://ib-insync.readthedocs.io/notebooks.html
JN: https://nbviewer.jupyter.org/github/erdewit/ib_insync/blob/master/notebooks/tick_data.ipynb


Flow:
0) Get/update the list of stocks to display 

RESTART API/THREAD EACH STOCKS LIST UPDATE!!!

1) start reqMktData for the list of stocks
2) Collect the data from an API to a buffer (DF)
3) Store the last received values into a temporary variable
4) Display the values from the temp var onto the webpage.
5) Send the values to the calculators of the indicators
-) Stop the stream when disconnected

'''

def stock_data_api(request):
    context = {}

    # context = {
    #     'tickers': stock_ticker,
    #     'prices': stock_price
    # }
    # context['stocks'] = stocks

    return render(request, 'ib_api/stock_data_api.html', context)




def stock_data(request):
    context = {}
    return render(request, 'ib_api/stock_data.html', context)


def background_view(request):
    util.startLoop()
    ib_api(activation=True, stock_list=('AAPL', 'GE', 'INTC'))


def ib_api(activation, stock_list):
    pass    
    

