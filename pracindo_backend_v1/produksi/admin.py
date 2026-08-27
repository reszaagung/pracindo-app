from django.contrib import admin
from .models import Batch, BatchInputRaw, Tangki, TransferWip

class BatchInputRawInline(admin.TabularInline):
    model = BatchInputRaw
    extra = 0
    # Field harga dan nilai otomatis dihitung snapshot sistem, jangan di-edit
    readonly_fields = ("harga_per_kg", "nilai")

class TransferWipInline(admin.TabularInline):
    model = TransferWip
    fk_name = "batch_tujuan"
    extra = 0
    # Nilai ditarik dari WIP batch sumber, jangan di-edit
    readonly_fields = ("nilai",)

@admin.register(Tangki)
class TangkiAdmin(admin.ModelAdmin):
    list_display = ("kode", "nama", "aktif")
    search_fields = ("kode", "nama")

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("nomor", "jenis", "nama_hasil", "tangki", "qty_hasil", 
                    "harga_per_kg", "status", "waktu")
    list_filter = ("status", "jenis", "tangki", "waktu")
    search_fields = ("nomor", "nama_hasil")
    inlines = [BatchInputRawInline, TransferWipInline]
    
    # Field-field ini adalah hasil kalkulasi otomatis sistem setelah posting,
    # jadi biarkan read-only meskipun statusnya DRAFT. (Kecuali susut_kg yang diinput manual)
    ANGKA = ("nomor", "qty_hasil", "nilai_hasil", "nilai_susut", "posted_at")

    def get_readonly_fields(self, request, obj=None):
        # Jika batch sudah di-POSTED, semua field dikunci mati (Immutable)
        if obj and obj.status != "DRAFT":
            # Tambahkan harga_per_kg (@property) agar ikut tampil sebagai read-only
            return [f.name for f in Batch._meta.fields] + ["harga_per_kg"]
        
        # Jika DRAFT, kunci field kalkulasi saja
        return list(self.ANGKA)

    def has_delete_permission(self, request, obj=None):
        # Hanya DRAFT yang boleh dihapus dari Admin
        return obj is None or obj.status == "DRAFT"