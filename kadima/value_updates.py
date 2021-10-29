import datetime
from os import execlp
import time
import logging
import math
import numpy as np
from time import sleep
from datetime import timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor


from django.conf import settings
from django.utils import timezone
from django.contrib import messages

from yahoo_earnings_calendar import YahooEarningsCalendar


from .models import IndicesData, StockData
from .k_utils import change_check, gap_1_check, date_obj_to_date
from .stock import Stock
from .ml_models import trend_calculator, trends
from ib_api.views import api_connection_status


# Create and configure logger
logger = logging.getLogger(__file__)


TODAY = datetime.datetime.today()
MAX_PAST = TODAY - timedelta(30)
WORKERS = 15


def update_values(request):

    context = {}
    errors = {}

    # Indexes update

    # TODO: Fix this when required
    # indexes_update_done, indexes_info = indexes_updates(request)

    # if indexes_update_done:
    #     context.update(indexes_info)
    # else:
    #     errors['indexes'] = True

    start_run = time.perf_counter()
    # Stocks Update
    # Get the list of current stocks list

    current_stocks = StockData.objects.all()

    # messages.info(request, 'Updading values...')

    for stock in current_stocks:
        stock_to_update = Stock(
            ticker=stock.ticker, stock_id=stock.id, table_index=stock.table_index
        )

        print(f"Updating Stock: {stock.ticker}")
        try:
            stock_to_update.update_stock()
        except Exception as e:
            print(f"Failed updating stock: {stock}. ERROR: {e}")
            logger.error(f"Failed updating stock: {stock}. ERROR: {e}")

        print(f"Finished updating Stock: {stock.ticker}")
        logger.info(f"Finished updating Stock: {stock.ticker}")

        stock.stock_displayed_date = stock_to_update.displayed_date
        stock.stock_price = stock_to_update.stock_price

        stock.week_1 = stock_to_update.week_1
        stock.week_1_min = stock_to_update.week_1_min
        stock.week_1_max = stock_to_update.week_1_max
        stock.week_1_color = stock_to_update.week_1_color

        stock.week_2 = stock_to_update.week_2
        stock.week_2_min = stock_to_update.week_2_min
        stock.week_2_max = stock_to_update.week_2_max
        stock.week_2_color = stock_to_update.week_2_color

        stock.week_3 = stock_to_update.week_3
        stock.week_3_min = stock_to_update.week_3_min
        stock.week_3_max = stock_to_update.week_3_max
        stock.week_3_color = stock_to_update.week_3_color

        stock.week_5 = stock_to_update.week_5
        stock.week_5_min = stock_to_update.week_5_min
        stock.week_5_max = stock_to_update.week_5_max
        stock.week_5_color = stock_to_update.week_5_color

        stock.gap_1 = stock_to_update.gap_1
        stock.gap_1_color = stock_to_update.gap_1_color

        # stock.earnings_call = stock_to_update.earnings_call
        stock.earnings_call_displayed = stock_to_update.earnings_call
        stock.earnings_warning = stock_to_update.earnings_warning

        if stock_to_update.earnings_warning == "PAST":
            stock.earnings_warning = ""
            stock.earnings_call_displayed = None
        else:
            stock.earnings_warning = stock_to_update.earnings_warning
            stock.earnings_call_displayed = stock_to_update.earnings_call

        if stock_to_update.dividend_warning == "PAST":
            stock.dividend_warning = ""
        else:
            stock.dividend_warning = stock_to_update.dividend_warning

        stock.stock_trend_30 = stock_to_update.trend_30

        stock.macd_trend_30 = stock_to_update.macd_30
        stock.macd_30_clash = stock_to_update.macd_30_clash
        stock.macd_30_color = stock_to_update.macd_30_color

        stock.macd_trend_14 = stock_to_update.macd_14
        stock.macd_14_clash = stock_to_update.macd_14_clash
        stock.macd_14_color = stock_to_update.macd_14_color

        stock.money_flow_trend_30 = stock_to_update.mfi_30
        stock.mfi_30_clash = stock_to_update.mfi_30_clash
        stock.mfi_30_color = stock_to_update.mfi_30_color

        stock.money_flow_trend_14 = stock_to_update.mfi_14
        stock.mfi_14_clash = stock_to_update.mfi_14_clash
        stock.mfi_14_color = stock_to_update.mfi_14_color

        stock.rsi = stock_to_update.rsi
        stock.rsi_color = stock_to_update.rsi_color

        try:
            stock.save()
        except Exception as e:
            print(f">>>>>>>>>>> FAILED saving stock <<<<<<<<<<< ")
            logger.error(f">>>>>>>>>>> FAILED saving stock <<<<<<<<<<< ")

    finish_run = time.perf_counter()
    print(
        f"""
    >>>>>>>>>>
    Finished updating {len(current_stocks)} stocks gaps. Durations: {round(finish_run - start_run,2)} seconds.
    >>>>>>>>>>
    """
    )
    logger.info(
        f"""
    >>>>>>>>>>
    Finished updating {len(current_stocks)} stocks gaps. Durations: {round(finish_run - start_run,2)} seconds.
    >>>>>>>>>>
    """
    )

    return True


def indexes_updates(request):
    indexes_context = {}
    indeces = ["^IXIC", "^GSPC", "^DJI", "^RUT", "^VIX"]
    tan_deviation_angle = math.tan(math.radians(settings.DEVIATION_ANGLE))

    try:
        # NASDAQ
        ####################################
        nas_data = IndicesData.objects.get(index_api_id=55555)

        # NASDAQ Indicators:
        (
            nas_index_trend,
            nas_index_macd,
            nas_index_mfi,
            nas_rsi,
            week1,
            week2,
            week3,
        ) = trends(
            "^IXIC", 30
        )  # rsi and week# are not used. Just for unpacking

        nas_data.index_trend = nas_index_trend
        nas_data.index_macd = nas_index_macd
        nas_data.index_mfi = nas_index_mfi

        if np.abs(nas_index_macd) > tan_deviation_angle:

            if (nas_index_trend > 0 and nas_index_macd < 0) or (
                nas_index_trend < 0 and nas_index_macd > 0
            ):
                nas_data.index_macd_clash = True
                nas_data.index_macd_color = "red"
            elif (nas_index_trend < 0 and nas_index_macd < 0) or (
                nas_index_trend > 0 and nas_index_macd > 0
            ):
                nas_data.index_macd_clash = False
                nas_data.index_macd_color = "green"

        else:
            nas_data.index_macd_clash = False
            nas_data.index_macd_color = "green"

        if np.abs(nas_index_mfi) > tan_deviation_angle:

            if (nas_index_trend > 0 and nas_index_mfi < 0) or (
                nas_index_trend < 0 and nas_index_mfi > 0
            ):
                nas_data.index_mfi_clash = True
                nas_data.index_mfi_color = "red"
            elif (nas_index_trend < 0 and nas_index_mfi < 0) or (
                nas_index_trend > 0 and nas_index_mfi > 0
            ):
                nas_data.index_mfi_clash = False
                nas_data.index_mfi_color = "green"

        else:
            nas_data.index_mfi_clash = False
            nas_data.index_mfi_color = "green"

        indexes_context["nas_macd"] = nas_index_macd
        indexes_context["nas_macd_color"] = nas_data.index_macd_color
        indexes_context["nas_mfi"] = nas_index_mfi
        indexes_context["nas_mfi_color"] = nas_data.index_mfi_color

        nas_data.save()

        # S&P
        ####################################
        snp_data = IndicesData.objects.get(index_api_id=88888)

        # SNP Indicators:
        (
            snp_index_trend,
            snp_index_macd,
            snp_index_mfi,
            snp_rsi,
            week1,
            week2,
            week3,
        ) = trends(
            "^GSPC", 30
        )  # rsi and week# are not used. Just for unpacking

        snp_data.index_trend = snp_index_trend
        snp_data.index_macd = snp_index_macd
        snp_data.index_mfi = snp_index_mfi

        if np.abs(snp_index_macd) > tan_deviation_angle:

            if (snp_index_trend > 0 and snp_index_macd < 0) or (
                snp_index_trend < 0 and snp_index_macd > 0
            ):
                snp_data.index_macd_clash = True
                snp_data.index_macd_color = "red"
            elif (snp_index_trend < 0 and snp_index_macd < 0) or (
                snp_index_trend > 0 and snp_index_macd > 0
            ):
                snp_data.index_macd_clash = False
                snp_data.index_macd_color = "green"

        else:
            snp_data.index_macd_clash = False
            snp_data.index_macd_color = "green"

        if np.abs(snp_index_mfi) > tan_deviation_angle:

            if (snp_index_trend > 0 and snp_index_mfi < 0) or (
                snp_index_trend < 0 and snp_index_mfi > 0
            ):
                snp_data.index_mfi_clash = True
                snp_data.index_mfi_color = "red"
            elif (snp_index_trend < 0 and snp_index_mfi < 0) or (
                snp_index_trend > 0 and snp_index_mfi > 0
            ):
                snp_data.index_mfi_clash = False
                snp_data.index_mfi_color = "green"

        else:
            snp_data.index_mfi_clash = False
            snp_data.index_mfi_color = "green"

        indexes_context["snp_macd"] = snp_index_macd
        indexes_context["snp_macd_color"] = snp_data.index_macd_color
        indexes_context["snp_mfi"] = snp_index_mfi
        indexes_context["snp_mfi_color"] = snp_data.index_mfi_color

        snp_data.save()

        # DOW Jones
        ####################################
        dow_data = IndicesData.objects.get(index_api_id=77777)

        # DOW Jones Indicators:
        (
            dow_index_trend,
            dow_index_macd,
            dow_index_mfi,
            dow_rsi,
            week1,
            week2,
            week3,
        ) = trends("^DJI", 30)

        dow_data.index_trend = dow_index_trend
        dow_data.index_macd = dow_index_macd
        dow_data.index_mfi = dow_index_mfi

        if np.abs(dow_index_macd) > tan_deviation_angle:

            if (dow_index_trend > 0 and dow_index_macd < 0) or (
                dow_index_trend < 0 and dow_index_macd > 0
            ):
                dow_data.index_macd_clash = True
                dow_data.index_macd_color = "red"
            elif (dow_index_trend < 0 and dow_index_macd < 0) or (
                dow_index_trend > 0 and dow_index_macd > 0
            ):
                dow_data.index_macd_clash = False
                dow_data.index_macd_color = "green"

        else:
            dow_data.index_macd_clash = False
            dow_data.index_macd_color = "green"

        if np.abs(dow_index_mfi) > tan_deviation_angle:

            if (dow_index_trend > 0 and dow_index_mfi < 0) or (
                dow_index_trend < 0 and dow_index_mfi > 0
            ):
                dow_data.index_mfi_clash = True
                dow_data.index_mfi_color = "red"
            elif (dow_index_trend < 0 and dow_index_mfi < 0) or (
                dow_index_trend > 0 and dow_index_mfi > 0
            ):
                dow_data.index_mfi_clash = False
                dow_data.index_mfi_color = "green"

        indexes_context["dow_macd"] = dow_index_macd
        indexes_context["dow_macd_color"] = dow_data.index_macd_color
        indexes_context["dow_mfi"] = dow_index_mfi
        indexes_context["dow_mfi_color"] = dow_data.index_mfi_color

        dow_data.save()

        # VIX
        ####################################
        vix_data = IndicesData.objects.get(index_api_id=11111)

        # VIX Weeks data
        (
            vix_index_trend,
            vix_index_macd,
            vix_index_mfi,
            vix_rsi,
            week1,
            week2,
            week3,
        ) = trends("^VIX", 30)
        vix_data.index_week1 = week1["relative_value"]
        vix_data.index_week1_min = week1["last_min"]
        vix_data.index_week1_max = week1["last_max"]

        vix_data.index_week2 = week2["relative_value"]
        vix_data.index_week2_min = week2["last_min"]
        vix_data.index_week2_max = week2["last_max"]

        vix_data.index_week3 = week3["relative_value"]
        vix_data.index_week3_min = week3["last_min"]
        vix_data.index_week3_max = week3["last_max"]

        vix_data.index_week_1_color = week1["week_1_color"]
        vix_data.index_week_2_color = week2["week_2_color"]
        vix_data.index_week_3_color = week3["week_3_color"]

        indexes_context["vix_week1_color"] = week1["week_1_color"]
        indexes_context["vix_week2_color"] = week2["week_2_color"]
        indexes_context["vix_week3_color"] = week3["week_3_color"]

        indexes_context["vix_week1"] = week1["relative_value"]
        indexes_context["vix_week2"] = week2["relative_value"]
        indexes_context["vix_week3"] = week3["relative_value"]

        vix_data.save()

        # Russell 2K
        ####################################
        r2k_data = IndicesData.objects.get(index_api_id=22222)

        # Russell 2K Indicators:
        (
            r2k_index_trend,
            r2k_index_macd,
            r2k_index_mfi,
            r2k_rsi,
            week1,
            week2,
            week3,
        ) = trends("^RUT", 30)

        r2k_data.index_trend = r2k_index_trend
        r2k_data.index_macd = r2k_index_macd
        r2k_data.index_mfi = r2k_index_mfi

        if np.abs(r2k_index_macd) > tan_deviation_angle:

            if (r2k_index_trend > 0 and r2k_index_macd < 0) or (
                r2k_index_trend < 0 and r2k_index_macd > 0
            ):
                r2k_data.index_macd_clash = True
                r2k_data.index_macd_color = "red"
            elif (r2k_index_trend < 0 and r2k_index_macd < 0) or (
                r2k_index_trend > 0 and r2k_index_macd > 0
            ):
                r2k_data.index_macd_clash = False
                r2k_data.index_macd_color = "green"

        else:
            r2k_data.index_macd_clash = False
            r2k_data.index_macd_color = "green"

        if np.abs(r2k_index_mfi) > tan_deviation_angle:

            if (r2k_index_trend > 0 and r2k_index_mfi < 0) or (
                r2k_index_trend < 0 and r2k_index_mfi > 0
            ):
                r2k_data.index_mfi_clash = True
                r2k_data.index_mfi_color = "red"
            elif (r2k_index_trend < 0 and r2k_index_mfi < 0) or (
                r2k_index_trend > 0 and r2k_index_mfi > 0
            ):
                r2k_data.index_mfi_clash = False
                r2k_data.index_mfi_color = "green"
        else:
            r2k_data.index_mfi_clash = False
            r2k_data.index_mfi_color = "green"

        indexes_context["r2k_macd"] = r2k_index_macd
        indexes_context["r2k_macd_color"] = r2k_data.index_macd_color
        indexes_context["r2k_mfi"] = r2k_index_mfi
        indexes_context["r2k_mfi_color"] = r2k_data.index_mfi_color

        r2k_data.save()

    except Exception as e:
        logger.error(f"Failed saving indexes data to DB.")
        print(f"Failed daving indexes data to DB. ERROR: {e}")
        messages.error(request, "Failed to update DB with Indeces data.")
        # return False, e

    return True, indexes_context
