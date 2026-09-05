from import_export import resources
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from core.models import Entitas
from master.models import Suplier, Produk

from .models import (
    Akun,
    FakturPembelian,
    JurnalUmum,
    PurchaseOrder,
    PurchaseOrderItem,
    SaldoAkunBulanan,
    UangMukaSuplier,
    FakturPenjualan,
    PembelianKemasan,
    PurchaseOrderKemasanItem,
)


# =========================================================
# AKUN
# =========================================================

class AkunResource(resources.ModelResource):
    parent = Field(
        attribute="parent",
        column_name="parent_kode",
        widget=ForeignKeyWidget(Akun, "kode"),
    )

    class Meta:
        model = Akun
        import_id_fields = ("kode",)


# =========================================================
# SALDO AKUN BULANAN
# =========================================================

class SaldoAkunBulananResource(resources.ModelResource):
    akun = Field(
        attribute="akun",
        column_name="akun_kode",
        widget=ForeignKeyWidget(Akun, "kode"),
    )

    entitas = Field(
        attribute="entitas",
        column_name="entitas",
        widget=ForeignKeyWidget(Entitas, "nama"),
    )

    class Meta:
        model = SaldoAkunBulanan
        import_id_fields = (
            "akun",
            "entitas",
            "tahun",
            "bulan",
        )


# =========================================================
# JURNAL UMUM
# =========================================================

class JurnalUmumResource(resources.ModelResource):
    class Meta:
        model = JurnalUmum


# =========================================================
# PURCHASE ORDER
# =========================================================

class PurchaseOrderResource(resources.ModelResource):

    no_po = Field(
        attribute="no_po",
        column_name="No. PO",
    )

    entitas = Field(
        attribute="entitas",
        column_name="Entitas",
        widget=ForeignKeyWidget(Entitas, "nama"),
    )

    suplier = Field(
        attribute="suplier",
        column_name="Supplier",
        widget=ForeignKeyWidget(Suplier, "nama"),
    )

    tanggal = Field(
        attribute="tanggal",
        column_name="Tanggal",
    )

    status = Field(
        attribute="status",
        column_name="Status",
    )

    tanggal_kirim_diminta = Field(
        attribute="tanggal_kirim_diminta",
        column_name="Tanggal Kirim Diminta",
    )

    catatan = Field(
        attribute="catatan",
        column_name="Catatan",
    )

    ppn_persen = Field(
        attribute="ppn_persen",
        column_name="PPN",
    )

    dibuat_oleh = Field(
        attribute="dibuat_oleh",
        column_name="dibuat_oleh",
        readonly=True,
    )

    dibuat_pada = Field(
        attribute="dibuat_pada",
        column_name="dibuat_pada",
        readonly=True,
    )

    def __init__(self, **kwargs):
        super().__init__()
        self.user = kwargs.get("user")

    def before_save_instance(self, instance, row, **kwargs):
        if (
            getattr(instance, "dibuat_oleh_id", None) is None
            and self.user is not None
        ):
            instance.dibuat_oleh = self.user

    class Meta:
        model = PurchaseOrder
        import_id_fields = ("no_po",)


# =========================================================
# PURCHASE ORDER ITEM
# =========================================================

class PurchaseOrderItemResource(resources.ModelResource):

    purchase_order = Field(
        attribute="purchase_order",
        column_name="No. PO",
        widget=ForeignKeyWidget(
            PurchaseOrder,
            "no_po",
        ),
    )

    produk = Field(
        attribute="produk",
        column_name="Nama Barang",
        widget=ForeignKeyWidget(
            Produk,
            "nama",
        ),
    )

    nama_item = Field(
        attribute="nama_item",
        column_name="Nama Barang",
    )

    qty_pesan = Field(
        attribute="qty_pesan",
        column_name="Qty",
    )

    satuan = Field(
        attribute="satuan",
        column_name="Satuan",
    )

    harga_per_kg = Field(
        attribute="harga_per_kg",
        column_name="Harga",
    )

    qty_diterima = Field(
        attribute="qty_diterima",
        column_name="qty_diterima",
        readonly=True,
    )

    amount = Field(
        attribute="amount",
        column_name="amount",
        readonly=True,
    )

    class Meta:
        model = PurchaseOrderItem
        import_id_fields = (
            "purchase_order",
            "produk",
        )


# =========================================================
# FAKTUR PEMBELIAN
# =========================================================

class FakturPembelianResource(resources.ModelResource):
    no_internal = Field(
        attribute="no_internal",
        column_name="no_internal",
        readonly=True,
    )

    dibuat_oleh = Field(
        attribute="dibuat_oleh",
        column_name="dibuat_oleh",
        readonly=True,
    )

    dibuat_pada = Field(
        attribute="dibuat_pada",
        column_name="dibuat_pada",
        readonly=True,
    )

    def __init__(self, **kwargs):
        super().__init__()
        self.user = kwargs.get("user")

    def before_save_instance(self, instance, row, **kwargs):
        if (
            getattr(instance, "dibuat_oleh_id", None) is None
            and self.user is not None
        ):
            instance.dibuat_oleh = self.user

    class Meta:
        model = FakturPembelian
        import_id_fields = ("nomor_faktur",)


# =========================================================
# UANG MUKA SUPLIER
# =========================================================

class UangMukaSuplierResource(resources.ModelResource):
    sisa = Field(
        attribute="sisa",
        column_name="sisa",
        readonly=True,
    )

    class Meta:
        model = UangMukaSuplier
        import_id_fields = ("id",)


# =========================================================
# FAKTUR PENJUALAN
# =========================================================

class FakturPenjualanResource(resources.ModelResource):
    no_internal = Field(
        attribute="no_internal",
        column_name="no_internal",
        readonly=True,
    )

    dibuat_oleh = Field(
        attribute="dibuat_oleh",
        column_name="dibuat_oleh",
        readonly=True,
    )

    dibuat_pada = Field(
        attribute="dibuat_pada",
        column_name="dibuat_pada",
        readonly=True,
    )

    def __init__(self, **kwargs):
        super().__init__()
        self.user = kwargs.get("user")

    def before_save_instance(self, instance, row, **kwargs):
        if (
            getattr(instance, "dibuat_oleh_id", None) is None
            and self.user is not None
        ):
            instance.dibuat_oleh = self.user

    class Meta:
        model = FakturPenjualan
        import_id_fields = ("nomor_faktur",)


# =========================================================
# PEMBELIAN KEMASAN
# =========================================================

class PembelianKemasanResource(resources.ModelResource):
    no_po = Field(
        attribute="no_po",
        column_name="no_po",
        readonly=True,
    )

    dibuat_oleh = Field(
        attribute="dibuat_oleh",
        column_name="dibuat_oleh",
        readonly=True,
    )

    dibuat_pada = Field(
        attribute="dibuat_pada",
        column_name="dibuat_pada",
        readonly=True,
    )

    def __init__(self, **kwargs):
        super().__init__()
        self.user = kwargs.get("user")

    def before_save_instance(self, instance, row, **kwargs):
        if (
            getattr(instance, "dibuat_oleh_id", None) is None
            and self.user is not None
        ):
            instance.dibuat_oleh = self.user

    class Meta:
        model = PembelianKemasan
        import_id_fields = ("id",)


# =========================================================
# PURCHASE ORDER KEMASAN ITEM
# =========================================================

class PurchaseOrderKemasanItemResource(resources.ModelResource):
    purchase_order = Field(
        attribute="purchase_order",
        column_name="no_po",
        widget=ForeignKeyWidget(
            PembelianKemasan,
            "no_po",
        ),
    )

    qty_diterima = Field(
        attribute="qty_diterima",
        column_name="qty_diterima",
        readonly=True,
    )

    amount = Field(
        attribute="amount",
        column_name="amount",
        readonly=True,
    )

    class Meta:
        model = PurchaseOrderKemasanItem
        import_id_fields = ("id",)