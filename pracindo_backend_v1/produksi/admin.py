from django.contrib import admin

from .models import Batch, BatchInputRaw, SekuensBatch, Tangki, TransferWip


class BatchInputRawInline(admin.TabularInline):
    model = BatchInputRaw
    extra = 0
    readonly_fields = ("harga_per_kg", "nilai", "menghabiskan")


class TransferWipInline(admin.TabularInline):
    model = TransferWip
    fk_name = "batch_tujuan"
    extra = 0
    readonly_fields = ("harga_per_kg", "nilai", "menghabiskan")


@admin.register(Tangki)
class TangkiAdmin(admin.ModelAdmin):
    list_display = ("kode", "nama", "aktif")
    search_fields = ("kode", "nama")


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("nomor", "jenis", "nama_hasil", "tangki", "qty_hasil",
                    "harga_hasil_per_kg", "status", "waktu")
    list_filter = ("status", "jenis", "tangki", "waktu")
    search_fields = ("nomor", "nama_hasil")
    inlines = [BatchInputRawInline, TransferWipInline]

    ANGKA = ("total_qty_input", "total_nilai_input", "nilai_susut",
             "qty_hasil", "nilai_hasil", "harga_masuk_per_kg",
             "harga_hasil_per_kg", "posted_by", "posted_at")

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != "DRAFT":
            return [f.name for f in Batch._meta.fields]
        return list(self.ANGKA)

    def has_delete_permission(self, request, obj=None):
        return obj is None or obj.status == "DRAFT"


@admin.register(SekuensBatch)
class SekuensBatchAdmin(admin.ModelAdmin):
    list_display = ("awalan", "periode", "terakhir")