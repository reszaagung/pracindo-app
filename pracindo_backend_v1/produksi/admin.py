from django.contrib import admin

from .models import Resep, ResepItem, SesiInput, SesiProduksi


class ResepItemInline(admin.TabularInline):
    model = ResepItem
    extra = 1
    autocomplete_fields = ('bahan',)


@admin.register(Resep)
class ResepAdmin(admin.ModelAdmin):
    list_display = ('produk_jadi', 'versi', 'hasil_per_batch',
                    'susut_wajar', 'berlaku_sejak', 'aktif')
    list_filter = ('aktif', 'berlaku_sejak')
    search_fields = ('produk_jadi__kode', 'produk_jadi__nama', 'nama')
    list_select_related = ('produk_jadi',)
    inlines = [ResepItemInline]


class SesiInputInline(admin.TabularInline):
    model = SesiInput
    extra = 0
    autocomplete_fields = ('bahan',)
    readonly_fields = ('selisih',)


@admin.register(SesiProduksi)
class SesiProduksiAdmin(admin.ModelAdmin):
    list_display = ('nomor', 'tanggal', 'grup_bahan', 'resep',
                    'qty_target', 'qty_hasil', 'susut', 'status')
    list_filter = ('grup_bahan', 'status', 'tanggal')
    search_fields = ('nomor', 'resep__produk_jadi__kode')
    list_select_related = ('grup_bahan', 'resep', 'resep__produk_jadi')
    readonly_fields = ('nomor', 'qty_hasil', 'dibuat_oleh', 'dibuat_pada')
    inlines = [SesiInputInline]

    def has_delete_permission(self, request, obj=None):
        return False
