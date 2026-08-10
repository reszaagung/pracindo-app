from django.contrib import admin

from .models import (
    Akun, FakturPembelian, JurnalDetail, JurnalUmum, KartuHutang,
    PurchaseOrder, PurchaseOrderItem, SaldoAkunBulanan, UangMukaSuplier,
    FakturPenjualan, KartuPiutang 
)

# ---------------- Bagan akun ----------------

@admin.register(Akun)
class AkunAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama', 'tipe', 'saldo_normal', 'parent',
                    'boleh_diposting', 'aktif')
    list_filter = ('tipe', 'boleh_diposting', 'aktif')
    search_fields = ('kode', 'nama')
    list_select_related = ('parent',)

    @admin.display(description='Saldo normal')
    def saldo_normal(self, obj):
        return obj.saldo_normal


@admin.register(SaldoAkunBulanan)
class SaldoAkunBulananAdmin(admin.ModelAdmin):
    list_display = ('akun', 'entitas', 'tahun', 'bulan',
                    'saldo_awal', 'total_debit', 'total_kredit', 'saldo_akhir')
    list_filter = ('entitas', 'tahun', 'bulan')
    search_fields = ('akun__kode', 'akun__nama')
    list_select_related = ('akun', 'entitas')


# ---------------- Buku besar ----------------

class JurnalDetailInline(admin.TabularInline):
    model = JurnalDetail
    extra = 0
    readonly_fields = ('akun', 'debit', 'kredit', 'keterangan')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(JurnalUmum)
class JurnalUmumAdmin(admin.ModelAdmin):
    list_display = ('nomor', 'tanggal', 'entitas', 'kejadian', 'referensi',
                    'total_debit', 'seimbang', 'sudah_dibalik')
    list_filter = ('entitas', 'kejadian', 'tanggal')
    search_fields = ('nomor', 'referensi', 'keterangan')
    list_select_related = ('entitas',)
    readonly_fields = [f.name for f in JurnalUmum._meta.fields]
    inlines = [JurnalDetailInline]

    @admin.display(boolean=True, description='Seimbang')
    def seimbang(self, obj):
        return obj.seimbang

    @admin.display(boolean=True, description='Dibalik')
    def sudah_dibalik(self, obj):
        return obj.sudah_dibalik

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ---------------- Pembelian ----------------

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0 # BUG FIX 3: Diubah dari 1 ke 0 untuk cegah crash form kosong
    readonly_fields = ('qty_diterima', 'amount', 'sisa_qty')
    autocomplete_fields = ('produk',)

    @admin.display(description='Sisa')
    def sisa_qty(self, obj):
        return obj.sisa_qty if obj.pk else '-'

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('no_po', 'tanggal', 'entitas', 'suplier', 'status',
                    'subtotal', 'dibuat_oleh') 
    list_filter = ('entitas', 'status', 'tanggal')
    search_fields = ('no_po', 'suplier__nama')
    list_select_related = ('entitas', 'suplier', 'dibuat_oleh')
    readonly_fields = ('no_po', 'dibuat_oleh', 'dibuat_pada')
    inlines = [PurchaseOrderItemInline]
    def get_queryset(self, request):
        return super().get_queryset(request).dengan_total()

    @admin.display(description='Subtotal')
    def subtotal(self, obj):
        return obj.subtotal
    def save_model(self, request, obj, form, change):
        if getattr(obj, 'dibuat_oleh', None) is None:
            obj.dibuat_oleh = request.user
        super().save_model(request, obj, form, change)
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'nama_item', 'qty_pesan',
                    'qty_diterima', 'harga_per_kg', 'amount')
    search_fields = ('nama_item', 'purchase_order__no_po')
    list_select_related = ('purchase_order',)
    readonly_fields = ('qty_diterima', 'amount')


# ---------------- Hutang ----------------
class KartuHutangInline(admin.TabularInline):
    model = KartuHutang
    extra = 0
    readonly_fields = ('tanggal', 'jenis', 'debit', 'kredit', 'referensi')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(FakturPembelian)
class FakturPembelianAdmin(admin.ModelAdmin):
    list_display = ('nomor_faktur', 'tanggal_faktur', 'entitas', 'suplier',
                    'jenis', 'tanggal_jatuh_tempo', 'total_tagihan',
                    'sisa_hutang', 'status', 'terlambat')
    list_filter = ('entitas', 'status', 'jenis', 'tanggal_jatuh_tempo')
    search_fields = ('nomor_faktur', 'no_internal', 'suplier__nama')
    list_select_related = ('entitas', 'suplier', 'dibuat_oleh')

    readonly_fields = ('no_internal', 'tanggal_jatuh_tempo', 'total_dibayar',
                       'sisa_hutang', 'dibuat_oleh', 'dibuat_pada')
    inlines = [KartuHutangInline]

    @admin.display(boolean=True, description='Telat')
    def terlambat(self, obj):
        return obj.terlambat

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'dibuat_oleh', None) is None:
            obj.dibuat_oleh = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(UangMukaSuplier)
class UangMukaSuplierAdmin(admin.ModelAdmin):
    list_display = ('tanggal', 'entitas', 'suplier', 'nominal', 'sisa')
    list_filter = ('entitas',)
    search_fields = ('suplier__nama', 'referensi')
    list_select_related = ('entitas', 'suplier')
    readonly_fields = ('sisa',)

# ---------------- Piutang (AR) ----------------

# PASTIKAN BARIS INI ADA:
class KartuPiutangInline(admin.TabularInline):
    model = KartuPiutang
    extra = 0
    readonly_fields = ('tanggal', 'jenis', 'debit', 'kredit', 'referensi')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(FakturPenjualan)
class FakturPenjualanAdmin(admin.ModelAdmin):
    list_display = ('nomor_faktur', 'tanggal_faktur', 'entitas', 'pelanggan',
                    'tanggal_jatuh_tempo', 'total_tagihan', 'sisa_piutang', 'status')
    list_filter = ('entitas', 'status', 'tanggal_jatuh_tempo')
    search_fields = ('nomor_faktur', 'no_internal', 'pelanggan__nama')
    list_select_related = ('entitas', 'pelanggan', 'dibuat_oleh')
    readonly_fields = ('no_internal', 'tanggal_jatuh_tempo', 'total_dibayar',
                       'sisa_piutang', 'dibuat_oleh', 'dibuat_pada')
    inlines = [KartuPiutangInline]

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'dibuat_oleh', None) is None:
            obj.dibuat_oleh = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False