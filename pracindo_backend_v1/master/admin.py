from django.contrib import admin

from .models import Kategori, Pelanggan, Produk, Satuan, Suplier


@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama', 'aktif')
    list_filter = ('aktif',)
    search_fields = ('kode', 'nama')

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Satuan)
class SatuanAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama', 'aktif')
    list_filter = ('aktif',)
    search_fields = ('kode', 'nama')

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Produk)
class ProdukAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama', 'jenis', 'kategori', 'satuan',
                    'disimpan_di_tanki', 'aktif')
    list_filter = ('jenis', 'kategori', 'disimpan_di_tanki', 'aktif')
    search_fields = ('kode', 'nama')
    list_select_related = ('kategori', 'satuan')

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Suplier)
class SuplierAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama', 'kontak_nama', 'kontak_hp',
                    'termin_hari_default', 'npwp', 'aktif')
    list_filter = ('aktif',)
    search_fields = ('kode', 'nama', 'npwp', 'kontak_nama')

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Pelanggan)
class PelangganAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama', 'kontak_nama', 'kontak_hp',
                    'termin_hari_default', 'plafon_kredit', 'aktif')
    list_filter = ('aktif',)
    search_fields = ('kode', 'nama', 'npwp')

    def has_delete_permission(self, request, obj=None):
        return False