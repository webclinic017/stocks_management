from ib_api.views import api_connection_status, trading_status
from kadima.k_utils import update_gaps
from .models import StockData

def apiConnectionStatus(request):
    context = {}
    ib_api_connected = api_connection_status()
    context['ib_api_connected'] = ib_api_connected
    return context

def updaingGaps(request):
    context = {}
    stock_data = StockData.objects.all()
    for stock in stock_data:
        if stock.updading_gap_1_flag:
            context['updating_gaps'] = True
            return context
    
    context['updating_gaps'] = False
    
    return context

def isTrading(request):
    context = {}
    context['is_trading'] = trading_status()
    return context
    