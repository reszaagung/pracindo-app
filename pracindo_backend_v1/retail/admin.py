from django.contrib import admin
from .models import (
    StokRetail, SesiKasir, TransaksiPOS, ItemTransaksi,
    BukuHutangRetail, RiwayatBayarHutang,
    KategoriAkun, AkunBukuBesar, TransaksiJurnal, DetailJurnal,
    SalesRetail,BukuPiutangRetail, RiwayatBayarPiutang, BonusSales
)

@admin.register(StokRetail)
class StokRetailAdmin(admin.ModelAdmin):
    list_display = ('cabang', 'produk', 'qty', 'harga_jual')
    list_filter = ('cabang',)
    search_fields = ('produk__nama',)

@admin.register(SalesRetail)
class SalesRetailAdmin(admin.ModelAdmin):
    list_display = ('nama', 'cabang', 'persentase_bonus', 'aktif')
    list_filter = ('cabang', 'aktif')
    search_fields = ('nama',)

