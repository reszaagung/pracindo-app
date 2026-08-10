from django.contrib import admin

from .models import CounterDokumen, Entitas, GrupBahan, PeriodeAkuntansi


@admin.register(GrupBahan)
class GrupBahanAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama')
    search_fields = ('kode', 'nama')


@admin.register(Entitas)
class EntitasAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama', 'jenis', 'grup_bahan', 'npwp', 'aktif')
    list_filter = ('jenis', 'grup_bahan', 'aktif')
    search_fields = ('kode', 'nama', 'npwp')

    def get_readonly_fields(self, request, obj=None):
        return ('kode',) if obj else ()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CounterDokumen)
class CounterDokumenAdmin(admin.ModelAdmin):
    list_display = ('entitas', 'jenis', 'periode', 'urutan')
    list_filter = ('entitas', 'jenis')
    readonly_fields = ('entitas', 'jenis', 'periode', 'urutan')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PeriodeAkuntansi)
class PeriodeAkuntansiAdmin(admin.ModelAdmin):
    list_display = ('entitas', 'tahun', 'bulan', 'ditutup', 'ditutup_pada', 'ditutup_oleh')
    list_filter = ('entitas', 'ditutup', 'tahun')
    readonly_fields = ('ditutup_pada', 'ditutup_oleh')
