from django.contrib import admin
from .models import (
    CabangToko, StokRetail, SesiKasir, TransaksiPOS, ItemTransaksi,
    BukuHutangRetail, RiwayatBayarHutang,
    KategoriAkun, AkunBukuBesar, TransaksiJurnal, DetailJurnal
)

@admin.register(CabangToko)
class CabangTokoAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama', 'aktif')
    search_fields = ('kode', 'nama')

@admin.register(StokRetail)
class StokRetailAdmin(admin.ModelAdmin):
    list_display = ('cabang', 'produk', 'qty', 'harga_jual')
    list_filter = ('cabang',)
    search_fields = ('produk__nama',)

@admin.register(SesiKasir)
class SesiKasirAdmin(admin.ModelAdmin):
    list_display = ('cabang', 'kasir', 'waktu_buka', 'status', 'total_penjualan')
    list_filter = ('status', 'cabang')

class ItemTransaksiInline(admin.TabularInline):
    model = ItemTransaksi
    extra = 0
    readonly_fields = ('produk', 'qty', 'harga_satuan', 'subtotal')

@admin.register(TransaksiPOS)
class TransaksiPOSAdmin(admin.ModelAdmin):
    list_display = ('nomor_struk', 'sesi', 'waktu_transaksi', 'grand_total', 'metode_bayar', 'status')
    list_filter = ('status', 'metode_bayar')
    search_fields = ('nomor_struk',)
    inlines = [ItemTransaksiInline]

class RiwayatBayarHutangInline(admin.TabularInline):
    model = RiwayatBayarHutang
    extra = 0

@admin.register(BukuHutangRetail)
class BukuHutangRetailAdmin(admin.ModelAdmin):
    list_display = ('referensi', 'cabang', 'total_hutang', 'total_dibayar', 'status')
    list_filter = ('status', 'cabang')
    search_fields = ('referensi',)
    inlines = [RiwayatBayarHutangInline]

@admin.register(KategoriAkun)
class KategoriAkunAdmin(admin.ModelAdmin):
    list_display = ('nama', 'tipe_saldo')
    search_fields = ('nama',)

@admin.register(AkunBukuBesar)
class AkunBukuBesarAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama', 'kategori', 'cabang', 'aktif')
    list_filter = ('aktif', 'kategori', 'cabang')
    search_fields = ('kode', 'nama')

class DetailJurnalInline(admin.TabularInline):
    model = DetailJurnal
    extra = 0

@admin.register(TransaksiJurnal)
class TransaksiJurnalAdmin(admin.ModelAdmin):
    list_display = ('nomor_jurnal', 'tanggal', 'referensi', 'cabang')
    list_filter = ('cabang',)
    search_fields = ('nomor_jurnal', 'referensi')
    inlines = [DetailJurnalInline]