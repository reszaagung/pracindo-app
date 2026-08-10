from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone

from core.constants import NILAI_DIGITS, NILAI_PLACES
from core.models import CounterDokumen, DiauditModel
from .akun import Akun, TipeAkun
from .jurnal import JurnalUmum, JurnalDetail, JenisKejadian

class StatusPengeluaran(models.TextChoices):
    DRAFT  = 'DRAFT',  'Draft'
    POSTED = 'POSTED', 'Terposting (Lunas)'
    BATAL  = 'BATAL',  'Dibatalkan'

class StatusPengeluaran(models.TextChoices):
    DRAFT  = 'DRAFT',  'Draft'
    POSTED = 'POSTED', 'Terposting (Lunas)'
    BATAL  = 'BATAL',  'Dibatalkan'

class PengeluaranKas(DiauditModel):
    """
    Pencatatan pembelian langsung / pengeluaran kas kecil operasional (Petty Cash).
    """
    entitas = models.ForeignKey(
        'core.Entitas', on_delete=models.PROTECT, related_name='pengeluaran'
    )
    nomor_bukti = models.CharField(max_length=32, editable=False, unique=True)
    tanggal = models.DateField(default=timezone.localdate, db_index=True)
    kategori_beban = models.ForeignKey(
        Akun, on_delete=models.PROTECT, related_name='pengeluaran_beban',
        limit_choices_to={'tipe': TipeAkun.BEBAN, 'boleh_diposting': True}
    )

    sumber_dana = models.ForeignKey(
        Akun, on_delete=models.PROTECT, related_name='pengeluaran_sumber',
        limit_choices_to={'tipe': TipeAkun.ASET, 'boleh_diposting': True}
    )
    
    pemohon = models.CharField(max_length=120, help_text="Nama staf yang meminta dana/melakukan pembelian")
    keterangan = models.CharField(max_length=255)
    nominal = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    status = models.CharField(
        max_length=10, choices=StatusPengeluaran.choices,
        default=StatusPengeluaran.DRAFT, db_index=True
    )

    dokumen = models.ForeignKey(
        'dokumen.Lampiran', null=True, blank=True,
        on_delete=models.PROTECT, related_name='+'
    )

    class Meta:
        db_table = 'akunting_pengeluaran_kas'
        ordering = ['-tanggal', '-id']
        verbose_name_plural = 'Pengeluaran kas'

    def __str__(self):
        return f"{self.nomor_bukti} - {self.pemohon} ({self.nominal})"

    def save(self, *args, **kwargs):
        if not self.nomor_bukti:
            self.nomor_bukti = CounterDokumen.berikutnya(self.entitas, 'BKK', self.tanggal)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status == StatusPengeluaran.POSTED:
            raise ValidationError('Pengeluaran yang sudah diposting tidak bisa dihapus. Batalkan saja.')
        return super().delete(*args, **kwargs)

    @transaction.atomic
    def posting(self, user):
        """
        Mencetak Jurnal Umum secara otomatis.
        Dr. Kategori Beban
        Cr. Sumber Dana (Kas)
        """
        pengeluaran = PengeluaranKas.objects.select_for_update().get(pk=self.pk)
        if pengeluaran.status != StatusPengeluaran.DRAFT:
            raise ValidationError('Hanya pengeluaran berstatus DRAFT yang bisa diposting.')

        jurnal = JurnalUmum.objects.create(
            entitas=pengeluaran.entitas,
            tanggal=pengeluaran.tanggal,
            kejadian=JenisKejadian.BEBAN_KAS,
            referensi=pengeluaran.nomor_bukti,
            keterangan=f"Pengeluaran: {pengeluaran.keterangan} (Pemohon: {pengeluaran.pemohon})",
            dibuat_oleh=user
        )

        JurnalDetail.objects.create(
            jurnal=jurnal,
            akun=pengeluaran.kategori_beban,
            debit=pengeluaran.nominal,
            kredit=Decimal('0')
        )

        JurnalDetail.objects.create(
            jurnal=jurnal,
            akun=pengeluaran.sumber_dana,
            debit=Decimal('0'),
            kredit=pengeluaran.nominal
        )

        pengeluaran.status = StatusPengeluaran.POSTED
        pengeluaran.save(update_fields=['status'])
        return pengeluaran