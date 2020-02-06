
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


def week_color(week_value):
    if week_value <= 33:
        return 'green'
    elif week_value > 33 and week_value <= 65:
        return 'orange'
    else:
        return 'red'
