from django.contrib import admin

from .models import MutasiKas, RekeningBank, RencanaBayar


@admin.register(RekeningBank)
class RekeningBankAdmin(admin.ModelAdmin):
    list_display = ('entitas', 'jenis', 'nama_bank', 'nomor_rekening',
                    'akun', 'saldo', 'aktif')
    list_filter = ('entitas', 'jenis', 'aktif')
    search_fields = ('nama_bank', 'nomor_rekening', 'nama_pemilik')
    list_select_related = ('entitas', 'akun')
    readonly_fields = ('saldo', 'urutan_terakhir')


@admin.register(MutasiKas)
class MutasiKasAdmin(admin.ModelAdmin):
    list_display = ('tanggal', 'rekening', 'debit', 'kredit',
                    'saldo_akhir', 'keterangan')
    list_filter = ('rekening', 'tanggal')
    search_fields = ('keterangan', 'referensi')
    list_select_related = ('rekening',)
    readonly_fields = [f.name for f in MutasiKas._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RencanaBayar)
class RencanaBayarAdmin(admin.ModelAdmin):
    list_display = ('tanggal_rencana', 'entitas', 'suplier', 'nominal',
                    'status', 'disetujui_oleh', 'dieksekusi_oleh')
    list_filter = ('status', 'entitas', 'tanggal_rencana')
    search_fields = ('suplier__nama',)
    list_select_related = ('entitas', 'suplier', 'rekening')
    readonly_fields = ('mutasi', 'dibuat_oleh', 'dibuat_pada')
