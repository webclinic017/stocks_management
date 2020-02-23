from ib_api.views import api_connection_status

def apiConnectionStatus(request):
    context = {}
    ib_api_connected = api_connection_status()
    context['ib_api_connected'] = ib_api_connected
    return context

