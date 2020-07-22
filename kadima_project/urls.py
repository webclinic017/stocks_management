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
from django.contrib.auth import views as auth_views

from rest_framework import routers

from kadima import views as views_kadima
from ib_api import views as views_ib_api
from dashboard import views as views_dashboard


# Admin Header
admin.site.site_header = 'KADIMA'

urlpatterns = [
    
    path('', views_kadima.home, name='home'),
    # path('login/', views_kadima.login, name='login'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='kadima/login.html')),
    path('accounts/', include('django.contrib.auth.urls')),


    path('table_index=<table_index>/', views_kadima.home, name='table-2'),
    path('table_index=<table_index>/', views_kadima.home, name='table-3'),
    path('history/<int:table_index>', views_kadima.history, name='history'),
    path('history-all/', views_kadima.history_all, name='history-all'),
    path(r'export/', views_kadima.file_load_view, name='export_data'),

    # IB API URLS
    path('indeces-data/', views_ib_api.indeces_data, name='indeces-data'), 
    path('stocks-alarms-data/', views_ib_api.stocks_alarms_data, name='stocks-alarms-data'), 
    path('stock-data-api/<int:table_index>/', views_ib_api.stock_data_api, name='stock-data-api'),
    
    path('stock-alarms/', views_kadima.stock_alarms, name='stock-alarms'),
    path('alarm-stocks-selector/', views_kadima.alarm_stocks_selector, name='alarm-stocks-selector'),
    path('alarm-trigger/', views_kadima.alarm_trigger, name='alarm-trigger'),
    
    path('dashboard/', views_dashboard.dashboard, name='dashboard'),
    

    path('admin/', admin.site.urls),

]
