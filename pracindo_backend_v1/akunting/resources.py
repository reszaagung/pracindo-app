from import_export import resources
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from .models import (
    Akun, FakturPembelian, JurnalUmum,
    PurchaseOrder, PurchaseOrderItem, SaldoAkunBulanan, UangMukaSuplier,
    FakturPenjualan, PembelianKemasan, PurchaseOrderKemasanItem,
)


# ---------------- Bagan akun ----------------

class AkunResource(resources.ModelResource):
    parent = Field(
        attribute='parent',
        column_name='parent_kode',
        widget=ForeignKeyWidget(Akun, 'kode'),
    )

    class Meta:
        model = Akun
        import_id_fields = ('kode',)
        # 'kode' = kunci pencocokan baris: kalau sudah ada -> update, kalau belum -> buat baru


class SaldoAkunBulananResource(resources.ModelResource):
    akun = Field(
        attribute='akun',
        column_name='akun_kode',
        widget=ForeignKeyWidget(Akun, 'kode'),
    )

    class Meta:
        model = SaldoAkunBulanan
        import_id_fields = ('akun', 'entitas', 'tahun', 'bulan')
        # PERHATIAN: kalau tabel ini dihitung otomatis dari posting jurnal, jangan
        # buka fitur import-nya di admin (lihat catatan di bawah) — export saja aman.


# ---------------- Buku besar (export-only) ----------------

class JurnalUmumResource(resources.ModelResource):
    class Meta:
        model = JurnalUmum
        # tidak ada import_id_fields khusus karena resource ini hanya dipakai untuk export


# ---------------- Pembelian ----------------

class PurchaseOrderResource(resources.ModelResource):
    no_po = Field(attribute='no_po', column_name='no_po', readonly=True)
    dibuat_oleh = Field(attribute='dibuat_oleh', column_name='dibuat_oleh', readonly=True)
    dibuat_pada = Field(attribute='dibuat_pada', column_name='dibuat_pada', readonly=True)

    def __init__(self, **kwargs):
        super().__init__()
        self.user = kwargs.get('user')

    def before_save_instance(self, instance, row, **kwargs):
        if getattr(instance, 'dibuat_oleh_id', None) is None and self.user is not None:
            instance.dibuat_oleh = self.user

    class Meta:
        model = PurchaseOrder
        import_id_fields = ('id',)
        # no_po/dibuat_oleh/dibuat_pada tetap tampil saat export, tapi diabaikan saat
        # import (readonly=True) — sama seperti perilaku save_model() di admin.


class PurchaseOrderItemResource(resources.ModelResource):
    purchase_order = Field(
        attribute='purchase_order',
        column_name='no_po',
        widget=ForeignKeyWidget(PurchaseOrder, 'no_po'),
    )
    qty_diterima = Field(attribute='qty_diterima', column_name='qty_diterima', readonly=True)
    amount = Field(attribute='amount', column_name='amount', readonly=True)

    class Meta:
        model = PurchaseOrderItem
        import_id_fields = ('id',)


# ---------------- Hutang ----------------

class FakturPembelianResource(resources.ModelResource):
    no_internal = Field(attribute='no_internal', column_name='no_internal', readonly=True)
    dibuat_oleh = Field(attribute='dibuat_oleh', column_name='dibuat_oleh', readonly=True)
    dibuat_pada = Field(attribute='dibuat_pada', column_name='dibuat_pada', readonly=True)

    def __init__(self, **kwargs):
        super().__init__()
        self.user = kwargs.get('user')

    def before_save_instance(self, instance, row, **kwargs):
        if getattr(instance, 'dibuat_oleh_id', None) is None and self.user is not None:
            instance.dibuat_oleh = self.user

    class Meta:
        model = FakturPembelian
        import_id_fields = ('nomor_faktur',)


class UangMukaSuplierResource(resources.ModelResource):
    sisa = Field(attribute='sisa', column_name='sisa', readonly=True)

    class Meta:
        model = UangMukaSuplier
        import_id_fields = ('id',)


# ---------------- Piutang (AR) ----------------

class FakturPenjualanResource(resources.ModelResource):
    no_internal = Field(attribute='no_internal', column_name='no_internal', readonly=True)
    dibuat_oleh = Field(attribute='dibuat_oleh', column_name='dibuat_oleh', readonly=True)
    dibuat_pada = Field(attribute='dibuat_pada', column_name='dibuat_pada', readonly=True)

    def __init__(self, **kwargs):
        super().__init__()
        self.user = kwargs.get('user')

    def before_save_instance(self, instance, row, **kwargs):
        if getattr(instance, 'dibuat_oleh_id', None) is None and self.user is not None:
            instance.dibuat_oleh = self.user

    class Meta:
        model = FakturPenjualan
        import_id_fields = ('nomor_faktur',)


class PembelianKemasanResource(resources.ModelResource):
    no_po = Field(attribute='no_po', column_name='no_po', readonly=True)
    dibuat_oleh = Field(attribute='dibuat_oleh', column_name='dibuat_oleh', readonly=True)
    dibuat_pada = Field(attribute='dibuat_pada', column_name='dibuat_pada', readonly=True)

    def __init__(self, **kwargs):
        super().__init__()
        self.user = kwargs.get('user')

    def before_save_instance(self, instance, row, **kwargs):
        if getattr(instance, 'dibuat_oleh_id', None) is None and self.user is not None:
            instance.dibuat_oleh = self.user

    class Meta:
        model = PembelianKemasan
        import_id_fields = ('id',)


class PurchaseOrderKemasanItemResource(resources.ModelResource):
    purchase_order = Field(
        attribute='purchase_order',
        column_name='no_po',
        widget=ForeignKeyWidget(PembelianKemasan, 'no_po'),
    )
    qty_diterima = Field(attribute='qty_diterima', column_name='qty_diterima', readonly=True)
    amount = Field(attribute='amount', column_name='amount', readonly=True)

    class Meta:
        model = PurchaseOrderKemasanItem
        import_id_fields = ('id',)