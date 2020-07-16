from django.conf import settings
from ib_api.views import api_connection_status, trading_status
# from kadima.value_updates import update_gaps_wrapper
from .models import StockData

def apiConnectionStatus(request):
    context = {}
    ib_api_connected = api_connection_status()
    context['ib_api_connected'] = ib_api_connected
    return context

def tableIndex(request):
    context = {}
    try:
        context['table_index'] = request.session['table_index']
    except:
        context['table_index'] = 1
    return context

def stockAlert(request):
    context = {}
    try:
        context['stock_alert'] = request.session['stock_alert']
    except:
        context['stock_alert'] = ''
    return context

def tableSort(request):
    context = {}
    try:
        context['sort_by'] = request.session['sort_by']
    except:
        context['sort_by'] = 'week_3'
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

def indecesSection(request):
    context = {}
    context['show_indeces'] = settings.INDICES
    return context