from django.contrib import admin
from .models import Batch, BatchInputRaw, Tangki, TransferWip

class BatchInputRawInline(admin.TabularInline):
    model = BatchInputRaw
    extra = 0
    readonly_fields = ("harga_per_kg", "nilai")

class TransferWipInline(admin.TabularInline):
    model = TransferWip
    fk_name = "batch_tujuan"
    extra = 0
    readonly_fields = ("nilai",)

@admin.register(Tangki)
class TangkiAdmin(admin.ModelAdmin):
    list_display = ("kode", "nama", "aktif")
    search_fields = ("kode", "nama")

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("nomor", "jenis", "nama_hasil", "tangki", "qty_hasil", 
                    "harga_per_kg", "waktu")
    list_filter = ("jenis", "tangki", "waktu")
    search_fields = ("nomor", "nama_hasil")
    inlines = [BatchInputRawInline, TransferWipInline]
    
    ANGKA = ("nomor", "qty_hasil", "nilai_hasil", "nilai_susut", "posted_at")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in Batch._meta.fields] + ["harga_per_kg"]
        return list(self.ANGKA)

    def has_delete_permission(self, request, obj=None):
        return False