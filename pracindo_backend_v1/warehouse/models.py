from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import CheckConstraint, Q, UniqueConstraint
from django.utils import timezone
from django.conf import settings

from core.constants import NILAI_DIGITS, NILAI_PLACES, QTY_DIGITS, QTY_PLACES
from core.models import CounterDokumen, DiauditModel, TimeStampedModel

D0 = Decimal("0")


class JenisKemasan(models.TextChoices):
    KARUNG  = 'KARUNG',  'Karung'
    DRUM    = 'DRUM',    'Drum'
    JERIGEN = 'JERIGEN', 'Jerigen'
    DUS     = 'DUS',     'Dus'
    SAK     = 'SAK',     'Sak'
    BAG     = 'BAG',     'Bag'
    CURAH   = 'CURAH',   'Curah / tanpa kemasan'


class PenerimaanBarang(DiauditModel):
    purchase_order = models.ForeignKey(
        'akunting.PurchaseOrder', on_delete=models.PROTECT,
        related_name='penerimaan',
    )
    nomor   = models.CharField(max_length=32, editable=False)
    tanggal = models.DateField(default=timezone.localdate, db_index=True)

    no_surat_jalan = models.CharField(max_length=64)

    dokumen = models.ForeignKey(
        'dokumen.Lampiran', null=True, blank=True,
        on_delete=models.PROTECT, related_name='+',
    )
    ada_selisih = models.BooleanField(default=False, editable=False, db_index=True)
    catatan = models.TextField(blank=True)

    class Meta:
        db_table = 'warehouse_penerimaan_barang'
        ordering = ['-tanggal', '-id']
        verbose_name_plural = 'Penerimaan barang'
        constraints = [
            models.UniqueConstraint(
                fields=['purchase_order', 'no_surat_jalan'],
                name='uq_penerimaan_surat_jalan',
            ),
        ]
        indexes = [
            models.Index(fields=['tanggal'], name='ix_penerimaan_tanggal'),
            models.Index(fields=['ada_selisih'], name='ix_penerimaan_selisih'),
        ]

    def __str__(self):
        return f"{self.nomor} - SJ {self.no_surat_jalan}"

    @property
    def entitas(self):
        return self.purchase_order.entitas

    @property
    def total_koli(self):
        return sum(i.jumlah_koli or 0 for i in self.item.all())

    def save(self, *args, **kwargs):
        if not self.nomor:
            self.nomor = CounterDokumen.berikutnya(
                self.purchase_order.entitas, 'GRN', self.tanggal,
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            'Penerimaan tidak bisa dihapus. Jurnalnya sudah terposting -- '
            'terbitkan retur.'
        )


class PenerimaanItem(models.Model):
    penerimaan = models.ForeignKey(
        PenerimaanBarang, on_delete=models.PROTECT, related_name='item',
    )
    po_item = models.ForeignKey(
        'akunting.PurchaseOrderItem', on_delete=models.PROTECT,
        related_name='realisasi',
    )

    jenis_kemasan = models.CharField(
        max_length=8, choices=JenisKemasan.choices,
        default=JenisKemasan.CURAH,
    )
    jumlah_koli = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Jumlah karung/drum/dus. Kosongkan untuk curah.',
    )
    isi_per_koli = models.DecimalField(
        max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
        null=True, blank=True,
        help_text='Isi nominal tiap koli menurut label.',
    )
    qty_deklarasi = models.DecimalField(
        max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
        default=Decimal('0'), editable=False,
    )

    qty_diterima = models.DecimalField(
        max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
        validators=[MinValueValidator(Decimal('0'))],
    )
    qty_ditolak = models.DecimalField(
        max_digits=QTY_DIGITS, decimal_places=QTY_PLACES, default=Decimal('0'),
    )
    alasan_tolak = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'warehouse_penerimaan_item'
        ordering = ['id']
        constraints = [
            models.CheckConstraint(
                condition=Q(qty_diterima__gte=0) & Q(qty_ditolak__gte=0),
                name='ck_penerimaan_item_nonneg',
            ),
            models.CheckConstraint(
                condition=~(Q(qty_diterima=0) & Q(qty_ditolak=0)),
                name='ck_penerimaan_item_tidak_nol',
            ),
            models.CheckConstraint(
                condition=Q(isi_per_koli__isnull=True) | Q(isi_per_koli__gt=0),
                name='ck_penerimaan_isi_positif',
            ),
            models.UniqueConstraint(
                fields=['penerimaan', 'po_item'], name='uq_penerimaan_item',
            ),
        ]

    def __str__(self):
        return f"{self.po_item.nama_item} = {self.qty_diterima}"

    @property
    def selisih_berat(self):
        if not self.qty_deklarasi:
            return Decimal('0')
        return self.qty_diterima + self.qty_ditolak - self.qty_deklarasi

    @property
    def persen_selisih_berat(self):
        if not self.qty_deklarasi:
            return Decimal('0')
        return (self.selisih_berat / self.qty_deklarasi * 100).quantize(Decimal('0.01'))

    @property
    def selisih_po(self):
        acuan = self.qty_deklarasi or (self.qty_diterima + self.qty_ditolak)
        return acuan - self.po_item.sisa_qty

    @property
    def ada_selisih(self):
        return self.selisih_berat != 0 or self.qty_ditolak > 0

    def save(self, *args, **kwargs):
        if self.jumlah_koli and self.isi_per_koli:
            self.qty_deklarasi = (
                Decimal(self.jumlah_koli) * self.isi_per_koli
            ).quantize(Decimal('0.001'))
        else:
            self.qty_deklarasi = Decimal('0')
        super().save(*args, **kwargs)

    def clean(self):
        if self.qty_ditolak and not self.alasan_tolak:
            raise ValidationError({'alasan_tolak': 'Wajib diisi kalau ada qty ditolak.'})

        if self.jenis_kemasan != JenisKemasan.CURAH:
            if not self.jumlah_koli or not self.isi_per_koli:
                raise ValidationError(
                    'Kemasan selain curah wajib mengisi jumlah koli dan isi per koli.'
                )


class JenisSelisih(models.TextChoices):
    KURANG_KIRIM  = 'KURANG_KIRIM',  'Kurang kirim'
    LEBIH_KIRIM   = 'LEBIH_KIRIM',   'Lebih kirim'
    BERAT_KURANG  = 'BERAT_KURANG',  'Berat kurang dari label'
    RUSAK         = 'RUSAK',         'Barang rusak'
    SALAH_BARANG  = 'SALAH_BARANG',  'Barang tidak sesuai pesanan'
    MUTU_TIDAK_SESUAI = 'MUTU', 'Mutu tidak sesuai'


class StatusSelisih(models.TextChoices):
    DIBUKA       = 'DIBUKA',       'Dibuka'
    DIAJUKAN     = 'DIAJUKAN',     'Diajukan ke suplier'
    DISEPAKATI   = 'DISEPAKATI',   'Disepakati suplier'
    DISELESAIKAN = 'DISELESAIKAN', 'Selesai'
    DITUTUP      = 'DITUTUP',      'Ditutup tanpa klaim'


class Resolusi(models.TextChoices):
    TERIMA_APA_ADANYA = 'TERIMA',   'Terima apa adanya'
    POTONG_TAGIHAN    = 'POTONG',   'Potong tagihan'
    KIRIM_SUSULAN     = 'SUSULAN',  'Suplier kirim susulan'
    RETUR             = 'RETUR',    'Retur ke suplier'
    GANTI_BARANG      = 'GANTI',    'Ganti barang'


class LaporanSelisih(DiauditModel):
    nomor      = models.CharField(max_length=32, editable=False)
    penerimaan = models.ForeignKey(
        PenerimaanBarang, on_delete=models.PROTECT, related_name='laporan_selisih',
    )
    penerimaan_item = models.ForeignKey(
        PenerimaanItem, null=True, blank=True,
        on_delete=models.PROTECT, related_name='laporan_selisih',
    )

    tanggal = models.DateField(default=timezone.localdate, db_index=True)
    jenis   = models.CharField(max_length=14, choices=JenisSelisih.choices,
                               db_index=True)
    status  = models.CharField(max_length=14, choices=StatusSelisih.choices,
                               default=StatusSelisih.DIBUKA, db_index=True)

    qty_selisih = models.DecimalField(
        max_digits=QTY_DIGITS, decimal_places=QTY_PLACES, default=Decimal('0'),
    )

    nilai_selisih = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
        default=Decimal('0'), editable=False,
    )

    uraian = models.TextField()
    foto = models.ForeignKey(
        'dokumen.Lampiran', null=True, blank=True,
        on_delete=models.PROTECT, related_name='+',
    )

    resolusi = models.CharField(
        max_length=8, choices=Resolusi.choices, blank=True,
    )
    nilai_klaim = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
        default=Decimal('0'),
    )
    catatan_resolusi = models.TextField(blank=True)
    diselesaikan_pada = models.DateTimeField(null=True, blank=True, editable=False)
    diselesaikan_oleh = models.ForeignKey(
        'staff_user.Profil', null=True, blank=True,
        on_delete=models.PROTECT, related_name='selisih_diselesaikan',
        editable=False,
    )

    class Meta:
        db_table = 'warehouse_laporan_selisih'
        ordering = ['-tanggal', '-id']
        verbose_name_plural = 'Laporan selisih'
        constraints = [
            models.UniqueConstraint(fields=['nomor'], name='uq_selisih_nomor'),
            models.CheckConstraint(
                condition=Q(nilai_klaim__gte=0), name='ck_selisih_klaim_nonneg',
            ),
        ]
        indexes = [
            models.Index(fields=['status', '-tanggal'], name='ix_selisih_status'),
        ]

    def __str__(self):
        return f"{self.nomor} - {self.get_jenis_display()}"

    @property
    def suplier(self):
        return self.penerimaan.purchase_order.suplier

    @property
    def terbuka(self):
        return self.status not in (StatusSelisih.DISELESAIKAN, StatusSelisih.DITUTUP)

    @property
    def umur_hari(self):
        return (timezone.localdate() - self.tanggal).days

    def save(self, *args, **kwargs):
        if not self.nomor:
            self.nomor = CounterDokumen.berikutnya(
                self.penerimaan.purchase_order.entitas, 'BAS', self.tanggal,
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Laporan selisih tidak bisa dihapus. Tutup saja.')


class Packaging(TimeStampedModel):
    tanggal = models.DateField(default=timezone.localdate, db_index=True)
    produk  = models.ForeignKey('master.Produk', on_delete=models.PROTECT,
                                related_name='packaging')
    grup_bahan = models.ForeignKey('core.GrupBahan', on_delete=models.PROTECT)

    qty_curah   = models.DecimalField(max_digits=QTY_DIGITS,
                                      decimal_places=QTY_PLACES)
    qty_kemasan = models.PositiveIntegerField()
    isi_per_kemasan = models.DecimalField(max_digits=QTY_DIGITS,
                                          decimal_places=QTY_PLACES)

    class Meta:
        db_table = 'warehouse_packaging'
        ordering = ['-tanggal', '-id']
        verbose_name_plural = 'Packaging'
        constraints = [
            models.CheckConstraint(condition=Q(qty_curah__gt=0),
                                   name='ck_packaging_curah'),
        ]

    def __str__(self):
        return f"{self.produk.kode} - {self.qty_kemasan} kemasan"

    @property
    def susut(self):
        return self.qty_curah - (self.qty_kemasan * self.isi_per_kemasan)


class DeliveryOrder(models.Model):
    nomor_do = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=20, default='DRAFT')
    tanggal = models.DateField(auto_now_add=True)
    pengemudi = models.CharField(max_length=100, blank=True)
    plat_nomor = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'tx_delivery_order'

    def __str__(self):
        return self.nomor_do


class DeliveryOrderItem(models.Model):
    delivery_order = models.ForeignKey(DeliveryOrder, on_delete=models.CASCADE, related_name='item')
    produk = models.ForeignKey('master.Produk', on_delete=models.PROTECT, null=True)
    qty = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal('0'))

    class Meta:
        db_table = 'tx_delivery_order_item'


class StokItemsPabrik(models.Model):
    produk = models.ForeignKey('master.Produk', on_delete=models.PROTECT, related_name='stok_items_pabrik')
    isi_per_kemasan = models.DecimalField(max_digits=QTY_DIGITS, decimal_places=QTY_PLACES)

    qty_kemasan = models.IntegerField(default=0)
    total_isi   = models.DecimalField(max_digits=QTY_DIGITS, decimal_places=QTY_PLACES, default=Decimal('0'))

    class Meta:
        db_table = 'warehouse_stok_items_pabrik'
        ordering = ['produk', 'isi_per_kemasan']
        verbose_name_plural = 'Stok items pabrik'
        constraints = [
            models.UniqueConstraint(fields=['produk', 'isi_per_kemasan'], name='uq_stok_items_pabrik_posisi'),
            models.CheckConstraint(condition=Q(qty_kemasan__gte=0), name='ck_stok_items_pabrik_non_negatif'),
        ]

    def __str__(self):
        return f"{self.produk} (isi {self.isi_per_kemasan}): {self.qty_kemasan} kemasan"


class TipeMutasiStok(models.TextChoices):
    PRODUKSI    = "PRODUKSI",    "Masuk dari produksi (packing)"
    DISTRIBUSI  = "DISTRIBUSI",  "Keluar untuk distribusi"
    RETUR       = "RETUR",       "Retur masuk dari distribusi"
    PENYESUAIAN = "PENYESUAIAN", "Penyesuaian manual"


class JenisKemasanJadi(models.IntegerChoices):
    PCS_1KG   = 1, 'PCS@1KG'
    GALON_5KG = 2, 'GALON@5KG'
    DUS_12KG  = 3, 'DUS@12KG'
    PAIL_10KG = 4, 'PAIL@10KG'
    PAIL_15KG = 5, 'PAIL@15KG'
    PAIL_20KG = 6, 'PAIL@20KG'
    PAIL_25KG = 7, 'PAIL@25KG'
    PAIL_30KG = 8, 'PAIL@30KG'


class MutasiStokBarangJadi(models.Model):
    entitas    = models.ForeignKey("core.Entitas", on_delete=models.PROTECT, related_name="mutasi_stok_jadi")
    grup_bahan = models.ForeignKey("core.GrupBahan", on_delete=models.PROTECT, related_name="mutasi_stok_jadi")
    item       = models.ForeignKey("master.MasterProduk", on_delete=models.PROTECT, related_name="mutasi_stok_jadi")
    kemasan    = models.IntegerField(choices=JenisKemasanJadi.choices)

    tipe = models.CharField(max_length=14, choices=TipeMutasiStok.choices)
    arah = models.SmallIntegerField()

    qty_unit         = models.IntegerField()
    netto_per_unit_kg = models.DecimalField(max_digits=10, decimal_places=3)
    qty_kg           = models.DecimalField(max_digits=18, decimal_places=3)

    ref_type   = models.CharField(max_length=30)
    ref_id     = models.BigIntegerField()
    keterangan = models.TextField(blank=True, default="")
    waktu      = models.DateTimeField(db_index=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    dibuat_oleh = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", editable=False)

    class Meta:
        db_table = "inventory_mutasi_stok_jadi"
        ordering = ["waktu", "id"]
        verbose_name_plural = "Mutasi stok barang jadi"
        indexes = [
            models.Index(fields=["entitas", "item", "kemasan", "waktu"], name="ix_mutasi_stok_posisi"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["ref_type", "ref_id", "tipe", "entitas"], name="uq_mutasi_stok_idempoten"),
            models.CheckConstraint(condition=models.Q(arah__in=[-1, 1]), name="ck_mutasi_stok_arah_valid"),
            models.CheckConstraint(condition=models.Q(qty_unit__gt=0), name="ck_mutasi_stok_unit_positif"),
            models.CheckConstraint(condition=models.Q(qty_kg__gt=0), name="ck_mutasi_stok_kg_positif"),
        ]

    def __str__(self):
        return f"{self.entitas} {self.item} {self.get_kemasan_display()} {self.arah:+d}{self.qty_unit}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("MutasiStokBarangJadi bersifat append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("MutasiStokBarangJadi tidak boleh dihapus.")


class StokBarangJadi(TimeStampedModel):
    entitas    = models.ForeignKey("core.Entitas", on_delete=models.PROTECT, related_name="stok_barang_jadi")
    grup_bahan = models.ForeignKey("core.GrupBahan", on_delete=models.PROTECT, related_name="stok_barang_jadi")
    item       = models.ForeignKey("master.MasterProduk", on_delete=models.PROTECT, related_name="stok_barang_jadi")
    kemasan    = models.IntegerField(choices=JenisKemasanJadi.choices)

    qty_unit = models.IntegerField(default=0)
    qty_kg   = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal('0'))
    
    class Meta:
        db_table = "inventory_stok_barang_jadi"
        ordering = ["entitas", "item", "kemasan"]
        verbose_name_plural = "Stok barang jadi"
        constraints = [
            models.UniqueConstraint(fields=["entitas", "grup_bahan", "item", "kemasan"], name="uq_stok_jadi_posisi"),
            models.CheckConstraint(condition=models.Q(qty_unit__gte=0), name="ck_stok_jadi_unit_non_negatif"),
            models.CheckConstraint(condition=models.Q(qty_kg__gte=0), name="ck_stok_jadi_kg_non_negatif"),
        ]

    def __str__(self):
        return f"{self.entitas} - {self.item} ({self.get_kemasan_display()}): {self.qty_unit} unit / {self.qty_kg} kg"