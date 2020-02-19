from .models import StockData
from pandas_datareader import data as fin_data
import datetime
from datetime import timedelta
from time import sleep

TODAY = datetime.datetime.today()
MAX_PAST = TODAY - timedelta(30)


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


def update_gaps():
    current_stocks = StockData.objects.all()

    for stock in current_stocks:
        stock_df = fin_data.get_data_yahoo(str(stock), start=MAX_PAST, end=TODAY)
        stock.prev_close = round(stock_df.loc[stock_df.index[-2]]['Close'],2)
        stock.todays_open = round(stock_df.loc[stock_df.index[-1]]['Open'],2)
        stock.stock_date = stock_df.index[-1]
        stock.save()
        sleep(2)

    
    print(f"*************** FINISHED UPDATING GAPS ****************")
    return


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
    
    if gap_1 > 1.26:
        gap_1_color = 'green'
            
    elif gap_1 >= 1:
        gap_1_color = 'orange'
        
    elif gap_1 > 0.75:
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
