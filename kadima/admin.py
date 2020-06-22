from django.contrib import admin

from .models import IndicesData, StockData

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


admin.site.register(StockData)