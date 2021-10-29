from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import IndicesData, StockData, HistoryStock


@admin.register(IndicesData)
class IndicesData(admin.ModelAdmin):
    list_display = (
        "sample_date",
        "index_symbol",
        "index_prev_close",
        "index_current_value",
        "index_api_id",
    )
    search_field = "index_symbol"
    ordering = ("index_symbol",)


# @admin.register(IndicesData)
# class IndicesData(admin.ModelAdmin):
#     list_display = ('sample_date','index_symbol','index_prev_close', 'index_current_value', 'index_api_id')
#     search_field = ('index_symbol')
#     ordering = ('index_symbol',)


@admin.register(HistoryStock)
class HistoryStocks(admin.ModelAdmin):
    list_display = (
        "pk",
        "ticker",
        "table_index",
        "time_added",
        "sold_date",
    )
    search_field = ("stock",)
    ordering = ("time_added",)


@admin.register(StockData)
class StockDataAdmin(ImportExportModelAdmin):
    pass
