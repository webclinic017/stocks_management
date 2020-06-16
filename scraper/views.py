import requests
from bs4 import BeautifulSoup as bs
from datetime import datetime
import re
from time import sleep

from django.shortcuts import render

from kadima.models import IndicesData
from ib_api import views as ib_api_views 

class YahooScraper():
    def __init__(self, index:dict):
        self.index = index
        self.price = None
        self.change = None
        self.stop = False

    def get_index_price(self, url):
        page = requests.get(url)
        soup = bs(page.content, 'html.parser')
        price_text = soup.find(id='quote-header-info').get_text()
        price_array = re.search('USD(.*)AS*', price_text).group().split(' ')
        
        price = float(price_array[0].split('+')[0].replace('USD','').split('.')[0].replace(',',''))
        
        change_text = re.search(r'\((.*)\)',price_array[1]).group()
        change_list = re.findall(r'\d+',change_text)
        if '-' in change_text:
            change = float(''.join(change_list[:-1]) + '.' + change_list[-1]) * (-1)
        else:
            change = float(''.join(change_list[:-1]) + '.' + change_list[-1]) 
        
        return (price, change)


    def run(self):
        index_ = self.index
        stop = self.stop
        while ib_api_views.api_connection_status():
            current_price, change = self.get_index_price(index_['url'])
            index_model = IndicesData.objects.get(index_api_id=index_['index_api_id'])
            index_model.index_current_value = current_price
            index_model.index_change = change
            index_model.save()
            print(f'>>> INDEX {index_["index_api_id"]} Price: {current_price}  CHANGE: {change}')
            sleep(5)


    def stop(self):
        self.stop = True