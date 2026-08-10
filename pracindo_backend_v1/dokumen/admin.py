from django.contrib import admin

from .models import Lampiran


@admin.register(Lampiran)
class LampiranAdmin(admin.ModelAdmin):
    list_display = ('jenis', 'nama_asli', 'ukuran_byte', 'masih_berlaku',
                    'dibuat_oleh', 'dibuat_pada')
    list_filter = ('jenis', 'dibuat_pada')
    search_fields = ('nama_asli', 'keterangan')
    readonly_fields = ('nama_asli', 'ukuran_byte', 'dibuat_oleh', 'dibuat_pada')

    @admin.display(boolean=True, description='Berlaku')
    def masih_berlaku(self, obj):
        return obj.digantikan_oleh_id is None

    def has_delete_permission(self, request, obj=None):
        return False
