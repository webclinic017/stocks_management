"""kadima_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from kadima import views as views_kadima
from ib_api import views as views_ib_api

from rest_framework import routers

urlpatterns = [
    
    path('', views_kadima.home, name='home'),
    path('table_index=<table_idx>/', views_kadima.home, name='table-2'),
    path('history/', views_kadima.history, name='history'),

    # IB API URLS
    # path('stock-data/', views_ib_api.streaming_stock_data, name='streaming-stock-data'), 
    path('indeces-data/', views_ib_api.indeces_data, name='indeces-data'), 
    path('history-data/', views_ib_api.history_data, name='history-data'), 
    path('stock-data-api/<int:table_index>', views_ib_api.stock_data_api, name='stock-data-api'),
    
    # path('bg/', views_ib_api.background_view, name='bg'),

    path('admin/', admin.site.urls),

]
