"""
Purchase order — komitmen pembelian.

PO BUKAN kejadian ekonomi. Tidak ada satu pun panggilan posting jurnal 
di file ini, dan itu disengaja. Jurnal pertama lahir di warehouse saat 
barang benar-benar diterima.

Kolom `entitas` menjawab "siapa yang berhutang ke suplier", bukan 
"siapa yang memiliki bahannya". Kepemilikan bahan dilacak terpisah di inventory.
SaldoEntitas sesuai spesifikasi SZA.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F, Q, Sum, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.utils import timezone

from core.constants import (
    HARGA_DIGITS, HARGA_PLACES,
    NILAI_DIGITS, NILAI_PLACES,
    QTY_DIGITS, QTY_PLACES,
)
from core.models import CounterDokumen, DiauditModel


class StatusPO(models.TextChoices):
    DRAFT     = 'DRAFT',     'Draft'
    PENDING   = 'PENDING',   'Menunggu Persetujuan'
    APPROVED  = 'APPROVED',  'Disetujui Internal'
    TERKIRIM  = 'TERKIRIM',  'Terkirim ke suplier'
    DISETUJUI = 'DISETUJUI', 'Disetujui suplier'
    DITOLAK   = 'DITOLAK',   'Ditolak'
    SEBAGIAN  = 'SEBAGIAN',  'Diterima sebagian'
    SELESAI   = 'SELESAI',   'Diterima penuh'
    BATAL     = 'BATAL',     'Dibatalkan'


class PurchaseOrderQuerySet(models.QuerySet):
    def untuk_entitas(self, entitas_id):
        return self.filter(entitas_id=entitas_id)

    def terbuka(self):
        """Dasar laporan komitmen — PO yang masih menunggu barang untuk Akunting."""
        return self.filter(status__in=[
            StatusPO.APPROVED, StatusPO.TERKIRIM, 
            StatusPO.DISETUJUI, StatusPO.SEBAGIAN
        ])

    def dengan_total(self):
        """
        Menghitung subtotal, nilai PPN, dan Grand Total di level database.
        Ini mencegah N+1 query saat serializer me-render daftar PO.
        """
        return self.annotate(
            subtotal_agg=Coalesce(Sum('item__amount'), Decimal('0'))
        ).annotate(
            ppn_nominal_agg=ExpressionWrapper(
                F('subtotal_agg') * (F('ppn_persen') / Decimal('100.0')),
                output_field=models.DecimalField(max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES)
            )
        ).annotate(
            grand_total_agg=ExpressionWrapper(
                F('subtotal_agg') + F('ppn_nominal_agg'),
                output_field=models.DecimalField(max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES)
            )
        )

    def untuk_gudang(self):
        """
        Prefetch untuk Received.vue.
        GEMBOK GUDANG: Gudang otomatis bisa melihat dan memproses PO 
        hanya jika statusnya sudah APPROVED, TERKIRIM, DISETUJUI, atau SEBAGIAN.
        """
        return self.filter(status__in=[
            StatusPO.APPROVED, StatusPO.TERKIRIM, 
            StatusPO.DISETUJUI, StatusPO.SEBAGIAN
        ]) \
        .select_related('suplier', 'entitas') \
        .prefetch_related('item')


class PurchaseOrder(DiauditModel):
    entitas = models.ForeignKey(
        'core.Entitas', on_delete=models.PROTECT, related_name='purchase_order',
    )
    suplier = models.ForeignKey(
        'master.Suplier', on_delete=models.PROTECT, related_name='purchase_order',
    )
    
    no_po   = models.CharField(max_length=32, editable=False)
    tanggal = models.DateField(default=timezone.localdate)
    status  = models.CharField(
        max_length=10, choices=StatusPO.choices,
        default=StatusPO.DRAFT, db_index=True,
    )
    tanggal_kirim_diminta = models.DateField(null=True, blank=True)
    catatan = models.TextField(blank=True)
    ppn_persen = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=Decimal('0.00'),
        help_text="Persentase PPN (contoh: 11.00 untuk 11%). Isi 0 jika non-PKP."
    )

    objects = PurchaseOrderQuerySet.as_manager()

    class Meta:
        db_table = 'akunting_purchase_order'
        ordering = ['-tanggal', '-id']
        verbose_name_plural = 'Purchase order'
        constraints = [
            models.UniqueConstraint(
                fields=['entitas', 'no_po'], name='uq_po_nomor_per_entitas',
            ),
        ]
        indexes = [
            models.Index(fields=['entitas', 'status', '-tanggal'], name='ix_po_ent_status'),
            models.Index(fields=['suplier', 'status'], name='ix_po_sup_status'),
        ]

    def __str__(self):
        return f"{self.no_po} — {self.suplier.nama}"

    @property
    def subtotal(self):
        """Halaman detail saja. Di list view pakai .dengan_total()."""
        return self.item.aggregate(t=Coalesce(Sum('amount'), Decimal('0')))['t']

    @property
    def ppn_nominal(self):
        """Nilai rupiah dari PPN untuk halaman detail."""
        return (self.subtotal * (self.ppn_persen / Decimal('100'))).quantize(Decimal('0.01'))

    @property
    def grand_total(self):
        """Total tagihan akhir yang harus dibayar termasuk PPN."""
        return self.subtotal + self.ppn_nominal

    @property
    def boleh_diubah(self):
        return self.status == StatusPO.DRAFT

    def semua_item_lengkap(self):
        """Dipakai warehouse.terima_barang() untuk memilih SELESAI vs SEBAGIAN."""
        return not self.item.filter(qty_diterima__lt=F('qty_pesan')).exists()

    def ada_penerimaan(self):
        return self.item.filter(qty_diterima__gt=0).exists()

    def save(self, *args, **kwargs):
        if not self.no_po:
            self.no_po = CounterDokumen.berikutnya(self.entitas, 'PO', self.tanggal)
        super().save(*args, **kwargs)

    def clean(self):
        if self.suplier_id and not self.suplier.aktif:
            raise ValidationError({'suplier': 'Suplier sudah tidak aktif.'})

    def delete(self, *args, **kwargs):
        if self.status != StatusPO.DRAFT:
            raise ValidationError('PO yang sudah diproses tidak bisa dihapus. Batalkan saja.')
        return super().delete(*args, **kwargs)


    # =========================================================
    # STATE TRANSITIONS
    # =========================================================
    
    @transaction.atomic
    def ajukan(self):
        """Merubah DRAFT menjadi PENDING (Menunggu Persetujuan Manajer)"""
        po = PurchaseOrder.objects.select_for_update().get(pk=self.pk)
        if po.status != StatusPO.DRAFT:
            raise ValidationError('Hanya PO DRAFT yang bisa diajukan.')
        if not po.item.exists():
            raise ValidationError('PO tanpa item tidak bisa diajukan.')
        
        po.status = StatusPO.PENDING
        po.save(update_fields=['status'])
        return po

    @transaction.atomic
    def setujui(self):
        """
        Approve Internal.
        Saat ini dipanggil, PO otomatis terbaca oleh Warehouse via untuk_gudang().
        """
        po = PurchaseOrder.objects.select_for_update().get(pk=self.pk)
        if po.status != StatusPO.PENDING:
            raise ValidationError('Hanya PO PENDING yang bisa disetujui.')
        
        po.status = StatusPO.APPROVED
        po.save(update_fields=['status'])
        return po

    @transaction.atomic
    def tolak(self, alasan=''):
        """Tolak Internal (Bisa dikembalikan dari PENDING/APPROVED ke DITOLAK)"""
        po = PurchaseOrder.objects.select_for_update().get(pk=self.pk)
        if po.status not in [StatusPO.PENDING, StatusPO.APPROVED, StatusPO.TERKIRIM]:
            raise ValidationError('Status saat ini tidak bisa ditolak.')
        
        po.status = StatusPO.DITOLAK
        if alasan:
            po.catatan = f"{po.catatan}\n[DITOLAK] {alasan}".strip()
        po.save(update_fields=['status', 'catatan'])
        return po

    @transaction.atomic
    def kirim(self):
        """Setelah Approve, PO resmi dikirim ke Suplier"""
        po = PurchaseOrder.objects.select_for_update().get(pk=self.pk)
        if po.status != StatusPO.APPROVED:
            raise ValidationError('PO harus di-Approve terlebih dahulu sebelum dikirim ke Suplier.')
        
        po.status = StatusPO.TERKIRIM
        po.save(update_fields=['status'])
        return po

    @transaction.atomic
    def batalkan(self, alasan=''):
        po = PurchaseOrder.objects.select_for_update().get(pk=self.pk)
        if po.ada_penerimaan():
            raise ValidationError('PO sudah diterima sebagian. Tutup lewat retur, bukan pembatalan.')
        
        po.status  = StatusPO.BATAL
        po.catatan = f"{po.catatan}\n[BATAL] {alasan}".strip()
        po.save(update_fields=['status', 'catatan'])
        return po


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name='item',
    )
    produk = models.ForeignKey('master.Produk', on_delete=models.PROTECT)
    
    nama_item = models.CharField(max_length=200)
    satuan    = models.CharField(max_length=8, default='kg')
    
    qty_pesan = models.DecimalField(
        max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
        validators=[MinValueValidator(Decimal('0.001'))],
    )
    qty_diterima = models.DecimalField(
        max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
        default=Decimal('0'), editable=False,
    )
    harga_per_kg = models.DecimalField(
        max_digits=HARGA_DIGITS, decimal_places=HARGA_PLACES,
        validators=[MinValueValidator(Decimal('0'))],
    )
    amount = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
        default=Decimal('0'), editable=False,
    )

    class Meta:
        db_table = 'akunting_purchase_order_item'
        ordering = ['id']
        constraints = [
            models.CheckConstraint(condition=Q(qty_pesan__gt=0), name='ck_poitem_qty_positif'),
            models.CheckConstraint(condition=Q(harga_per_kg__gte=0), name='ck_poitem_harga_nonneg'),
            models.CheckConstraint(
                condition=Q(qty_diterima__gte=0) & Q(qty_diterima__lte=F('qty_pesan')),
                name='ck_poitem_terima_dalam_batas',
            ),
            models.UniqueConstraint(
                fields=['purchase_order', 'produk'], name='uq_poitem_produk',
            ),
        ]
        indexes = [
            models.Index(fields=['purchase_order'], name='ix_poitem_po'),
        ]

    def __str__(self):
        return f"{self.nama_item} — {self.qty_pesan} {self.satuan}"

    @property
    def sisa_qty(self):
        return self.qty_pesan - self.qty_diterima

    @property
    def sudah_lengkap(self):
        return self.qty_diterima >= self.qty_pesan

    def save(self, *args, **kwargs):
        if self.produk_id and not self.nama_item:
            self.nama_item = self.produk.nama
            
        self.amount = (self.qty_pesan * self.harga_per_kg).quantize(Decimal('0.01'))
        
        if self.pk is None and not self.purchase_order.boleh_diubah:
            raise ValidationError('Item hanya bisa ditambah saat PO masih draft.')
            
        if kwargs.get('update_fields') is not None:
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'amount'}
            
        super().save(*args, **kwargs)


class PembelianKemasan(DiauditModel):
    nomor         = models.CharField(max_length=48, unique=True, editable=False)
    no_po         = models.CharField(max_length=64, blank=True, default="", db_index=True)
    entitas       = models.ForeignKey("core.Entitas", on_delete=models.PROTECT)
    kemasan       = models.ForeignKey('inventory.Kemasan', on_delete=models.PROTECT)
    qty_pcs       = models.IntegerField() # Satuannya Unit/Pcs
    harga_per_pcs = models.DecimalField(max_digits=20, decimal_places=2)
    nilai         = models.DecimalField(max_digits=20, decimal_places=2)
    tanggal       = models.DateField(db_index=True)
    status        = models.CharField(max_length=10, choices=StatusPO.choices, default=StatusPO.DRAFT)
    
    class Meta:
        db_table = "inventory_pembelian_kemasan"


class PurchaseOrderKemasanItem(models.Model):
    purchase_order = models.ForeignKey('PembelianKemasan', on_delete=models.CASCADE, related_name='items')
    kemasan        = models.ForeignKey('inventory.Kemasan', on_delete=models.PROTECT)
    qty_pesan      = models.IntegerField() # Satuannya Pcs/Unit (Integer)
    qty_diterima   = models.IntegerField(default=0)
    harga_per_pcs  = models.DecimalField(max_digits=20, decimal_places=2)
    amount         = models.DecimalField(max_digits=20, decimal_places=2, default=0, editable=False)

    class Meta:
        db_table = "inventory_pembelian_kemasan_item"

    def save(self, *args, **kwargs):
        if self.qty_pesan and self.harga_per_pcs:
            self.amount = self.qty_pesan * self.harga_per_pcs
        super().save(*args, **kwargs)

    @property
    def sisa_qty(self):
        return self.qty_pesan - self.qty_diterima

    def __str__(self):
        return f"Item PO Kemasan: {self.qty_pesan} pcs"