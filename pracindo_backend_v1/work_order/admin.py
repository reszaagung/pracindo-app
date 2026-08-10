from django.contrib import admin

from .models import (
    CounterWorkOrder, DetailPesananProduksi, WorkOrder, WorkOrderPenugasan,
    WorkOrderPesan,
)


class DetailPesananProduksiInline(admin.StackedInline):
    model = DetailPesananProduksi
    extra = 0


class WorkOrderPenugasanInline(admin.TabularInline):
    model = WorkOrderPenugasan
    extra = 1
    autocomplete_fields = ['staff']
    readonly_fields = ['ditandai_pada']


class WorkOrderPesanInline(admin.TabularInline):
    """
    Append-only: pesan bisa dilihat, tidak bisa ditambah atau diubah.
    Menambah pesan dari admin melewati pencatatan pengirim yang benar.
    """
    model = WorkOrderPesan
    extra = 0
    readonly_fields = ['pengirim', 'teks', 'dibuat_pada']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('nomor', 'judul', 'kategori', 'aturan_penyelesaian',
                    'tanggal', 'deadline', 'selesai', 'dibuat_oleh')
    list_filter = ('kategori', 'selesai', 'aturan_penyelesaian', 'tanggal')
    search_fields = ('nomor', 'judul', 'deskripsi')
    list_select_related = ('dibuat_oleh',)
    readonly_fields = ('nomor', 'dibuat_oleh', 'dibuat_pada',
                       'diselesaikan_oleh', 'waktu_selesai')
    inlines = [DetailPesananProduksiInline, WorkOrderPenugasanInline,
               WorkOrderPesanInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.dibuat_oleh = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        # Diskusi di dalamnya adalah jejak kesepakatan.
        return False


@admin.register(DetailPesananProduksi)
class DetailPesananProduksiAdmin(admin.ModelAdmin):
    list_display = ('work_order', 'nama_item', 'unit', 'stiker')
    list_filter = ('unit', 'stiker')
    search_fields = ('nama_item', 'work_order__nomor')


@admin.register(WorkOrderPesan)
class WorkOrderPesanAdmin(admin.ModelAdmin):
    list_display = ('work_order', 'pengirim', 'dibuat_pada', 'ringkas')
    search_fields = ('teks', 'work_order__nomor', 'pengirim__username')
    readonly_fields = [f.name for f in WorkOrderPesan._meta.fields]

    @admin.display(description='Isi pesan')
    def ringkas(self, obj):
        return obj.teks[:50] + '...' if len(obj.teks) > 50 else obj.teks

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CounterWorkOrder)
class CounterWorkOrderAdmin(admin.ModelAdmin):
    list_display = ('periode', 'urutan')
    readonly_fields = ('periode', 'urutan')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
