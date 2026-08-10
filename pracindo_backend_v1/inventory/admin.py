from django.contrib import admin

from .models import (
    MutasiKlaim, MutasiStok, NilaiEkuivalen, PosisiKlaim,
    SaldoEntitas, Stok, Tangki,
)


@admin.register(Tangki)
class TangkiAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama', 'grup_bahan', 'produk_terisi',
                    'kapasitas_kg', 'isi_kg', 'terisi', 'aktif')
    list_filter = ('grup_bahan', 'aktif')
    search_fields = ('kode', 'nama')
    readonly_fields = ('isi_kg', 'produk_terisi')

    @admin.display(description='Terisi')
    def terisi(self, obj):
        return f"{obj.persen_terisi}%"


class SaldoEntitasInline(admin.TabularInline):
    model = SaldoEntitas
    extra = 0
    readonly_fields = ('entitas', 'qty', 'nilai')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Stok)
class StokAdmin(admin.ModelAdmin):
    list_display = ('produk', 'lapis', 'grup_bahan', 'tangki', 'qty')
    list_filter = ('lapis', 'grup_bahan', 'tangki')
    search_fields = ('produk__kode', 'produk__nama')
    list_select_related = ('produk', 'grup_bahan', 'tangki')
    readonly_fields = ('qty', 'urutan_terakhir')
    inlines = [SaldoEntitasInline]


@admin.register(MutasiStok)
class MutasiStokAdmin(admin.ModelAdmin):
    list_display = ('tanggal', 'stok', 'jenis', 'masuk', 'keluar',
                    'saldo_akhir', 'referensi')
    list_filter = ('jenis', 'tanggal')
    search_fields = ('referensi', 'stok__produk__kode')
    list_select_related = ('stok', 'stok__produk')
    readonly_fields = [f.name for f in MutasiStok._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(NilaiEkuivalen)
class NilaiEkuivalenAdmin(admin.ModelAdmin):
    list_display = ('produk', 'nilai_per_satuan', 'berlaku_sejak', 'catatan')
    list_filter = ('berlaku_sejak',)
    search_fields = ('produk__kode', 'produk__nama')
    list_select_related = ('produk',)


@admin.register(MutasiKlaim)
class MutasiKlaimAdmin(admin.ModelAdmin):
    list_display = ('tanggal', 'grup_bahan', 'entitas', 'jenis',
                    'produk', 'qty', 'tarif', 'nilai', 'referensi')
    list_filter = ('grup_bahan', 'entitas', 'jenis', 'tanggal')
    search_fields = ('referensi',)
    list_select_related = ('grup_bahan', 'entitas', 'produk')
    readonly_fields = [f.name for f in MutasiKlaim._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PosisiKlaim)
class PosisiKlaimAdmin(admin.ModelAdmin):
    list_display = ('grup_bahan', 'entitas', 'total_setor',
                    'total_ambil', 'nilai_bersih', 'berhutang')
    list_filter = ('grup_bahan',)
    list_select_related = ('grup_bahan', 'entitas')
    readonly_fields = ('total_setor', 'total_ambil', 'nilai_bersih')

    @admin.display(boolean=True, description='Berhutang')
    def berhutang(self, obj):
        return obj.nilai_bersih < 0


@admin.register(SaldoEntitas)
class SaldoEntitasAdmin(admin.ModelAdmin):
    list_display = ('stok', 'entitas', 'qty', 'nilai')
    list_filter = ('entitas',)
    list_select_related = ('stok', 'stok__produk', 'entitas')
    readonly_fields = ('qty', 'nilai')
