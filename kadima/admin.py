from django.contrib import admin

from .models import IndicesData, StockData, HistoryStock

@admin.register(IndicesData)
class IndicesData(admin.ModelAdmin):
    list_display = ('sample_date','index_symbol','index_prev_close', 'index_current_value', 'index_api_id')
    search_field = ('index_symbol')
    ordering = ('index_symbol',)

# @admin.register(IndicesData)
# class IndicesData(admin.ModelAdmin):
#     list_display = ('sample_date','index_symbol','index_prev_close', 'index_current_value', 'index_api_id')
#     search_field = ('index_symbol')
#     ordering = ('index_symbol',)

@admin.register(HistoryStock)
class HistoryStocks(admin.ModelAdmin):
    list_display = ('pk', 'stock', 'table_index',)
    search_field = ('stock',)
    ordering = ('time_added',)


admin.site.register(StockData)