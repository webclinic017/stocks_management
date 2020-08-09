import os
import subprocess
import sys
import requests
import json

from django.core.mail import EmailMultiAlternatives
from django.template import RequestContext, TemplateDoesNotExist
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail

from .models import StockData
from pandas_datareader import data as fin_data
import datetime
from datetime import timedelta
from time import sleep
from threading import Thread
from scraper.views import YahooScraper

from ib_api.views import *

TODAY = datetime.datetime.today()
MAX_PAST = TODAY - timedelta(30)

def send_email_alert(subject, email_template_name,
              context, to_email, html_email_template_name=None, request=None, from_email=None):
    """
    Sends a django.core.mail.EmailMultiAlternatives to `to_email`.
    """

    print(f'''
    subject: {subject}
    html email template name: {html_email_template_name}
    context: {context}
    to email: {to_email}
    request: {request}
    from email: {from_email}
    ''')
    ctx_dict = {}
    if request is not None:
        ctx_dict = RequestContext(request, ctx_dict)
    # update ctx_dict after RequestContext is created
    # because template context processors
    # can overwrite some of the values like user
    # if django.contrib.auth.context_processors.auth is used
    if context:
        ctx_dict.update(context)

    # Email subject *must not* contain newlines
    from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL')
    if email_template_name:
        message_txt = render_to_string(email_template_name,
                                       ctx_dict)

        email_message = EmailMultiAlternatives(subject, message_txt,
                                               from_email, to_email)
    else:
        try:
            message_html = render_to_string(
                html_email_template_name, ctx_dict)
            email_message = EmailMultiAlternatives(subject, message_html,
                                                   from_email, to_email)
            email_message.content_subtype = 'html'
        except TemplateDoesNotExist:
            pass


    try:
        email_message.send()
    except Exception as e:
        if settings.DEBUG:
            print(f'ERROR: email not sent (utils/utils.py). Reason: {e}')
            print(sys.exc_info())


def date_obj_to_date(date_obj, date_format):
    if date_format == 'slash':
        str_date_arr = str(date_obj).split(' ')[0].split('-')
        year = str_date_arr[0].strip()
        month = str_date_arr[1].strip()
        day = str_date_arr[2].strip()
        date = f'{day}/{month}/{year}'
    else:
        str_date_arr = str(date_obj).split(' ')[0].split('/')
        year = str_date_arr[0].strip()
        month = str_date_arr[1].strip()
        day = str_date_arr[2].strip()

        date = f'{year}-{month}-{day}'


    return date


def change_check(index_change):
    if index_change >= 0.003:
        return 'green'
    elif index_change < 0.003 and index_change >= -0.003:
        return 'orange'
    else:
        return 'red'

RED_OVER_93 = '#FF1000'

def week_color(week_value, week3=False):
    if week_value <= 33:
        if week3:
            return 'green'
        else:
            return '#6cbf6c'
    elif week_value > 33 and week_value <= 65:
        if week3:
            return 'orange'
        else:
            return '#f1b55f'
    elif week_value > 65 and week_value <= 93:
        if week3:
            return 'red'
        else:
            return '#dc6460'
    else:
        if week3:
            return RED_OVER_93
        else:
            return '#dc6460'


def gap_check(stock_df, api_connected=False, realtime_price=None):
    days_back = 1
    gap_count = 0
    gaps = []
    gaps_colors = []
    
    while gap_count < 4 and days_back < len(stock_df)/2:
        if api_connected:
            open_value = realtime_price
        else:
            open_value = stock_df.loc[stock_df.index[-days_back]]['Open']
        
        close_value = stock_df.loc[stock_df.index[-days_back-1]]['Close']
        delta_price = open_value - close_value
        delta_rate = (delta_price / close_value) * 100
        if delta_rate > 1.26:
            gaps.append(float("%0.2f"%delta_rate))
            
            if gap_count == 0:
                gaps_colors.append('green')
            else:
                gaps_colors.append('#6cbf6c')
            
            gap_count +=1
            days_back += 1
        
        elif delta_rate >= 1:
            gaps.append(float("%0.2f"%delta_rate))

            if gap_count == 0:
                gaps_colors.append('orange')
            else:
                gaps_colors.append('#f1b55f')
            
            gap_count +=1
            days_back += 1
        
        elif delta_rate > 0.75:
            gaps.append(float("%0.2f"%delta_rate))
        
            if gap_count == 0:
                gaps_colors.append('red')    
            else:
                gaps_colors.append('#dc6460')
            
            gap_count +=1
            days_back += 1        
        
        else:
            days_back += 1        

    print(f'gaps: {gaps} \n gaps_colors: {gaps_colors}')

    return gaps, gaps_colors

def gap_1_check (prev_close, todays_open):

    delta_price = todays_open - prev_close
    gap_1 = (delta_price / prev_close) * 100
    
    if gap_1 > 1.25:
        gap_1_color = 'green'
            
    elif (gap_1 <=1.25 and gap_1 >= 0.75) or (gap_1 <= -0.75 and gap_1 >= -1.25):
        gap_1_color = 'orange'
        
    elif gap_1 < -1.25:
        gap_1_color = 'red'
    else:
        gap_1_color = ''
        
    return round(gap_1,2), gap_1_color

def week_values(stock_df, week_index):

    last_max = stock_df['High'][-week_index:].values.max()
    last_min = stock_df['Low'][-week_index:].values.min()
    current_price = stock_df['Close'].values[-1]

    relative_value = (100  / ( last_max - last_min)) * (current_price - last_min)

    last_max = float("%0.2f"%last_max)
    last_min = float("%0.2f"%last_min)
    
    relative_value_tmp = float("%0.2f"%relative_value)
    relative_value = 100 if relative_value_tmp > 100 else relative_value_tmp

    return relative_value, last_min, last_max

def send_mail(subject, email_template_name,
              context, to_email, html_email_template_name=None, request=None, from_email=None):
    """
    Sends a django.core.mail.EmailMultiAlternatives to `to_email`.
    """

    print(f'''
    subject: {subject}
    html email template name: {html_email_template_name}
    context: {context}
    to email: {to_email}
    request: {request}
    from email: {from_email}
    ''')
    ctx_dict = {}
    if request is not None:
        ctx_dict = RequestContext(request, ctx_dict)
    # update ctx_dict after RequestContext is created
    # because template context processors
    # can overwrite some of the values like user
    # if django.contrib.auth.context_processors.auth is used
    if context:
        ctx_dict.update(context)

    # Email subject *must not* contain newlines
    from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL')
    if email_template_name:
        message_txt = render_to_string(email_template_name,
                                       ctx_dict)

        email_message = EmailMultiAlternatives(subject, message_txt,
                                               from_email, to_email)
    else:
        try:
            message_html = render_to_string(
                html_email_template_name, ctx_dict)
            email_message = EmailMultiAlternatives(subject, message_html,
                                                   from_email, to_email)
            email_message.content_subtype = 'html'
        except TemplateDoesNotExist:
            pass


    try:
        email_message.send()
    except Exception as e:
        if settings.DEBUG:
            print(f'ERROR: email not sent (utilities.py). Reason: {e}')
            print(sys.exc_info())

def reset_email_alerts():
    # Resetting all email alerts to False
    stocks = StockData.objects.all()
    for stock in stocks:
        stock.stock_email_alert = False
        stock.save()

def reset_alarms(stock):
    
    stock.stock_alarm_trigger_set = False
    stock.stock_price_down_alarm = False # reseting the up/down alerts
    stock.stock_price_up_alarm = False
    stock.stock_alarm_sound_on_off = False # Resetting the alarm sound
    stock.stock_alarm_delta = 0.0
    stock.stock_initial_price = None

    stock.stock_alarm_1 = None
    stock.stock_alarm_2 = None
    stock.stock_alarm_3 = None
    stock.stock_alarm_4 = None
    stock.stock_alarm_5 = None
    stock.stock_alarm_6 = None
    stock.stock_alarm_7 = None
    stock.stock_alarm_8 = None
    stock.stock_alarm_9 = None
    stock.stock_alarm_10 = None

    stock.stock_alarm_1_color = None
    stock.stock_alarm_2_color = None
    stock.stock_alarm_3_color = None
    stock.stock_alarm_4_color = None
    stock.stock_alarm_5_color = None
    stock.stock_alarm_6_color = None
    stock.stock_alarm_7_color = None
    stock.stock_alarm_8_color = None
    stock.stock_alarm_9_color = None
    stock.stock_alarm_10_color = None

    # stock.stock_load_price = None

    stock.save()
    
    return

def indices_scrapers(stop=False):
    pass
    # NAS = 55555
    # DOW = 77777
    # SNP = 88888
    # VIX = 11111
    # R2K = 22222

    # dow = {
    #     'url': 'https://finance.yahoo.com/quote/YM=F?p=YM=F',
    #     'index_api_id': DOW
    # }
    # vix = {
    #     'url':'https://finance.yahoo.com/quote/%5EVIX?p=^VIX&.tsrc=fin-srch',
    #     'index_api_id': VIX
    # }

    # snp = {
    #     'url':'https://finance.yahoo.com/quote/ES=F?p=ES=F',
    #     'index_api_id': SNP
    # }

    # nas = {
    #     'url':'https://finance.yahoo.com/quote/NQ=F?p=NQ=F',
    #     'index_api_id': NAS
    # }
    # r2k = {
    #     'url':'https://finance.yahoo.com/quote/RTY=F?p=RTY=F',
    #     'index_api_id': R2K
    # }

    # dow_scraper = YahooScraper(dow)
    # nas_scraper = YahooScraper(nas)
    # snp_scraper = YahooScraper(snp)
    # vix_scraper = YahooScraper(vix)
    # r2k_scraper = YahooScraper(r2k)

    # t_dow = Thread(target=dow_scraper.run)
    # t_nas = Thread(target=nas_scraper.run)
    # t_snp = Thread(target=snp_scraper.run)
    # t_vix = Thread(target=vix_scraper.run)
    # t_r2k = Thread(target=r2k_scraper.run)

    # if stop:
    #     print('#### Stopping scrapers....')
    #     current_running_threads = threading.active_count()
    #     print(f"ACTIVE THREADS AFTER STOPPING: ***{current_running_threads}**")
    # else:
    #     t_dow.start()
    #     t_nas.start()
    #     t_snp.start()
    #     t_vix.start()
    #     t_r2k.start()
    #     current_running_threads = threading.active_count()
    #     print(f"ACTIVE THREADS WITH SCRAPERS: ***************{current_running_threads}****************")
    #     print('SCRAPERS RUNNING...')

def tws_start():
    tws = subprocess.Popen(settings.SCRIPTS_PATH + '/tws_start.sh')
    print(f'>>>>>START TWS: {tws}')

def tws_stop():
    tws = subprocess.Popen(settings.SCRIPTS_PATH + '/tws_stop.sh')
    print(f'>>>>>STOPPING TWS: {tws}')
