from django.contrib import admin
from .models import SalesOrder, SalesOrderItem

class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 1
    autocomplete_fields = ('produk',)

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('nomor_so', 'tanggal', 'pelanggan', 'status', 'grand_total')
    list_filter = ('status', 'tanggal', 'pelanggan')
    search_fields = ('nomor_so', 'pelanggan__nama')
    list_select_related = ('pelanggan',)
    readonly_fields = ('nomor_so', 'subtotal', 'ppn_nominal', 'grand_total')
    inlines = [SalesOrderItemInline]