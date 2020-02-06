from django.shortcuts import render, HttpResponse

from .api import *


def stock_data(request):
    context = {}
    return render(request, 'ib_api/stock_data.html', context)


def stock_data_api(request):
    context = {}
 
    stocks_list = StockList.objects.last()
    print(f"***************{stocks_list}****************")

    # context = {
    #     'tickers': stock_ticker,
    #     'prices': stock_price
    # }
    # context['stocks'] = stocks
    StockList.objects.all().delete()

    return render(request, 'ib_api/stock_data_api.html', context)


class RunApp(TestWrapper, TestClient):
    def __init__(self, ipaddress, portid, clientid):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)

        self.connect(ipaddress, portid, clientid)

        thread = Thread(target = self.run)
        thread.start()

        setattr(self, "_thread", thread)

        self.init_error()



def run_api(stocks):

    app = RunApp("127.0.0.1", 4004, 0)

    ibcontract = IBcontract()
    for stock in stocks:
        ibcontract.symbol = stock
        ibcontract.secType = "STK"
        ibcontract.exchange = "SMART"
        ibcontract.currency = "USD"
        ibcontract.primaryExchange = "NASDAQ"

    print(f"***************0****************")

    resolved_ibcontract = app.resolve_ib_contract(ibcontract)

    tickerid = app.start_getting_IB_market_data(ibcontract)

    time.sleep(5)

    print(f"***************1****************")
    ## What have we got so far?
    market_data1 = app.get_IB_market_data(tickerid)
    print(f"***************2****************")

    print(market_data1[0])

    market_data1_as_df = market_data1.as_pdDataFrame()
    print(market_data1_as_df)

    time.sleep(5)

    ## stops the stream and returns all the data we've got so far
    market_data2 = app.stop_getting_IB_market_data(tickerid)

    app.disconnect()



def background_view(request):
    run_api(['AAPL', 'GE', 'INTC'])