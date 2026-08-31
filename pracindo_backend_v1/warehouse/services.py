
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from core.services import pastikan_periode_terbuka

from .models import (
    JenisKemasan, JenisSelisih, LaporanSelisih, PenerimaanBarang,
    PenerimaanItem, Resolusi, StatusSelisih,
)

Q3 = Decimal('0.001')
Q2 = Decimal('0.01')
TOLERANSI_BERAT = Decimal('0.005')


def ambang_toleransi():
    """Dipakai serializer/endpoint config supaya frontend tidak menebak."""
    return {"toleransi_berat_persen": str(TOLERANSI_BERAT * 100)}


@transaction.atomic
def terima_barang(*, po_id, baris, no_surat_jalan, tanggal, user,
                  dokumen_id=None, catatan=''):
    """
    Menerima kiriman suplier.

    Mengembalikan (penerimaan, laporan_selisih, setoran).

    Titik otorisasinya di sini: barang belum jadi milik siapa pun sampai
    staf gudang menimbang dan menyimpan. Purchasing menerbitkan PO,
    suplier mengirim, tapi hak baru lahir saat ada orang yang
    menandatangani.
    """
    from akunting.models import PurchaseOrder, StatusPO
    from inventory.services import terbitkan_pembelian_dari_penerimaan

    if not baris:
        raise ValidationError('Tidak ada baris barang yang diterima.')

    po = (PurchaseOrder.objects.select_for_update()
          .select_related('entitas').get(pk=po_id))

    if po.status == StatusPO.SELESAI:
        raise ValidationError('PO sudah diterima penuh.')
    if po.status in (StatusPO.DRAFT, StatusPO.BATAL):
        raise ValidationError(
            f'PO berstatus {po.get_status_display()}, belum bisa diterima.')
    if not po.entitas.aktif:
        raise ValidationError(
            f'Entitas {po.entitas.kode} nonaktif. Barangnya tidak bisa '
            f'dicatat sebagai hak siapa pun.')

    pastikan_periode_terbuka(po.entitas_id, tanggal)

    if PenerimaanBarang.objects.filter(
            purchase_order=po, no_surat_jalan=no_surat_jalan).exists():
        raise ValidationError(
            f'Surat jalan {no_surat_jalan} sudah pernah diterima untuk PO ini.')

    penerimaan = PenerimaanBarang.objects.create(
        purchase_order=po, tanggal=tanggal, no_surat_jalan=no_surat_jalan,
        dokumen_id=dokumen_id, catatan=catatan, dibuat_oleh=user,
    )

    laporan = []
    ada_terima = False
    for b in baris:
        item = _simpan_item(penerimaan, b, po)
        if item.qty_diterima > 0:
            ada_terima = True
        laporan.extend(_periksa_selisih(penerimaan, item, user))

    if not ada_terima and not laporan:
        raise ValidationError(
            'Seluruh barang ditolak. Terbitkan laporan selisih saja, jangan '
            'catat sebagai penerimaan.')

    po.refresh_from_db()
    po.status = StatusPO.SELESAI if po.semua_item_lengkap() else StatusPO.SEBAGIAN
    po.save(update_fields=['status'])

    if laporan:
        penerimaan.ada_selisih = True
        penerimaan.save(update_fields=['ada_selisih'])
    setoran = terbitkan_pembelian_dari_penerimaan(penerimaan, user=user)

    return penerimaan, laporan, setoran


def _simpan_item(penerimaan, b, po):
    from akunting.models import PurchaseOrderItem

    po_item = PurchaseOrderItem.objects.select_for_update().get(
        pk=b['po_item_id'], purchase_order=po)

    if po_item.harga_per_kg is None:
        raise ValidationError(
            f'{po_item.nama_item}: harga PO kosong. Lengkapi PO sebelum '
            f'barangnya diterima.')

    qty_terima = Decimal(str(b.get('qty_diterima', 0))).quantize(Q3)
    qty_tolak = Decimal(str(b.get('qty_ditolak', 0))).quantize(Q3)

    if qty_terima < 0 or qty_tolak < 0:
        raise ValidationError(f'{po_item.nama_item}: qty tidak boleh negatif.')
    if qty_terima == 0 and qty_tolak == 0:
        raise ValidationError(
            f'{po_item.nama_item}: isi qty diterima atau ditolak.')
    if qty_tolak and not b.get('alasan_tolak'):
        raise ValidationError(
            f'{po_item.nama_item}: alasan tolak wajib diisi.')
    if qty_terima > po_item.sisa_qty:
        raise ValidationError(
            f'{po_item.nama_item}: diterima {qty_terima} melebihi sisa PO '
            f'{po_item.sisa_qty}.')

    item = PenerimaanItem(
        penerimaan=penerimaan,
        po_item=po_item,
        jenis_kemasan=b.get('jenis_kemasan', JenisKemasan.CURAH),
        jumlah_koli=b.get('jumlah_koli') or None,
        isi_per_koli=(Decimal(str(b['isi_per_koli'])).quantize(Q3)
                      if b.get('isi_per_koli') else None),
        qty_diterima=qty_terima,
        qty_ditolak=qty_tolak,
        alasan_tolak=b.get('alasan_tolak', ''),
    )
    item.full_clean(exclude=['qty_deklarasi'])
    item.save()
    po_item.qty_diterima = F('qty_diterima') + qty_terima
    po_item.save(update_fields=['qty_diterima'])
    po_item.refresh_from_db(fields=['qty_diterima'])
    return item


def _periksa_selisih(penerimaan, item, user):
    """
    Dua jenis selisih dengan makna berbeda:

        BERAT_KURANG  timbang != deklarasi   koli lengkap, isinya beda
        RUSAK         ada qty ditolak        barang tidak bisa dipakai

    Keduanya klaim ke SUPLIER. Tidak satu pun menyentuh pool atau hak
    entitas -- barang yang tidak pernah masuk tidak perlu dikeluarkan.
    """
    hasil = []

    if item.qty_deklarasi:
        beda = item.selisih_berat
        ambang = (item.qty_deklarasi * TOLERANSI_BERAT).quantize(Q3)
        if abs(beda) > ambang:
            arah = 'kurang' if beda < 0 else 'lebih'
            hasil.append(buat_laporan(
                penerimaan=penerimaan, item=item, user=user,
                jenis=(JenisSelisih.BERAT_KURANG if beda < 0
                       else JenisSelisih.LEBIH_KIRIM),
                qty_selisih=beda,
                uraian=f'Deklarasi {item.jumlah_koli} koli '
                       f'= {item.qty_deklarasi} Kg, timbang '
                       f'{item.qty_diterima + item.qty_ditolak} Kg. '
                       f'Selisih {beda} ({arah}), melebihi toleransi '
                       f'{ambang} Kg.',
            ))

    if item.qty_ditolak > 0:
        hasil.append(buat_laporan(
            penerimaan=penerimaan, item=item, user=user,
            jenis=JenisSelisih.RUSAK,
            qty_selisih=-item.qty_ditolak,
            uraian=f'Ditolak {item.qty_ditolak} Kg. '
                   f'Alasan: {item.alasan_tolak}',
        ))

    return hasil

@transaction.atomic
def buat_laporan(*, penerimaan, item, user, jenis, qty_selisih, uraian,
                 foto_id=None):
    """
    Berita acara ketidaksesuaian.

    nilai_selisih dihitung dari harga PO, bukan diisi manusia. Gudang
    tidak melihat rupiah -- dia menimbang dan memotret.
    """
    if item is None:
        harga = Decimal('0')          # laporan manual tanpa item
    else:
        harga = item.po_item.harga_per_kg
        if harga is None:
            raise ValidationError(
                f'{item.po_item.nama_item}: harga PO kosong. Laporan selisih '
                f'tanpa nilai tidak bisa diklaim ke suplier.')

    nilai = (abs(Decimal(qty_selisih)) * harga).quantize(Q2)

    lap = LaporanSelisih.objects.create(
        penerimaan=penerimaan, penerimaan_item=item,
        tanggal=penerimaan.tanggal, jenis=jenis,
        qty_selisih=Decimal(qty_selisih).quantize(Q3),
        uraian=uraian, foto_id=foto_id, dibuat_oleh=user,
    )
    LaporanSelisih.objects.filter(pk=lap.pk).update(nilai_selisih=nilai)
    lap.nilai_selisih = nilai
    return lap


@transaction.atomic
def laporan_manual(*, penerimaan_id, jenis, qty_selisih, uraian, user,
                   penerimaan_item_id=None, foto_id=None):
    """Temuan yang muncul belakangan, setelah barang sudah diterima."""
    penerimaan = PenerimaanBarang.objects.get(pk=penerimaan_id)
    item = (PenerimaanItem.objects.select_related('po_item')
            .get(pk=penerimaan_item_id) if penerimaan_item_id else None)

    if item is not None and item.penerimaan_id != penerimaan.id:
        raise ValidationError(
            'Item yang dipilih bukan bagian dari penerimaan ini.')

    lap = buat_laporan(penerimaan=penerimaan, item=item, user=user,
                       jenis=jenis, qty_selisih=qty_selisih, uraian=uraian,
                       foto_id=foto_id)
    if not penerimaan.ada_selisih:
        penerimaan.ada_selisih = True
        penerimaan.save(update_fields=['ada_selisih'])
    return lap


@transaction.atomic
def ajukan_ke_suplier(*, laporan_id, user):
    lap = LaporanSelisih.objects.select_for_update().get(pk=laporan_id)
    if lap.status != StatusSelisih.DIBUKA:
        raise ValidationError(f'Laporan sudah {lap.get_status_display()}.')
    if lap.nilai_selisih <= 0:
        raise ValidationError(
            f'{lap.nomor} bernilai nol. Klaim tanpa nilai tidak bisa '
            f'diajukan -- periksa harga di PO.')
    lap.status = StatusSelisih.DIAJUKAN
    lap.save(update_fields=['status'])
    return lap


@transaction.atomic
def selesaikan_laporan(*, laporan_id, resolusi, user, nilai_klaim=None,
                       catatan=''):
    """
    RESOLUSI menentukan konsekuensi finansialnya:

        TERIMA   nilai tetap, selisih diserap sebagai beban
        POTONG   nilai_klaim mengurangi tagihan suplier
        SUSULAN  PO dibuka kembali, menunggu kiriman berikutnya
        RETUR    barang dikembalikan
    """
    from akunting.models import StatusPO

    lap = (LaporanSelisih.objects.select_for_update()
           .select_related('penerimaan__purchase_order').get(pk=laporan_id))

    if lap.status in (StatusSelisih.DISELESAIKAN, StatusSelisih.DITUTUP):
        raise ValidationError(
            f'Laporan sudah {lap.get_status_display()}.')

    if resolusi == Resolusi.POTONG_TAGIHAN:
        nilai_klaim = Decimal(
            nilai_klaim if nilai_klaim is not None else lap.nilai_selisih
        ).quantize(Q2)
        if nilai_klaim <= 0:
            raise ValidationError('Nilai klaim harus lebih dari 0.')
        if nilai_klaim > lap.nilai_selisih:
            raise ValidationError(
                f'Klaim Rp{nilai_klaim:,.2f} melebihi nilai selisih '
                f'Rp{lap.nilai_selisih:,.2f}. Memotong lebih banyak daripada '
                f'yang hilang berarti menagih barang yang diterima.')
    else:
        nilai_klaim = Decimal('0')

    lap.resolusi = resolusi
    lap.nilai_klaim = nilai_klaim
    lap.catatan_resolusi = catatan
    lap.status = StatusSelisih.DISELESAIKAN
    lap.diselesaikan_pada = timezone.now()
    lap.diselesaikan_oleh = user
    lap.save(update_fields=['resolusi', 'nilai_klaim', 'catatan_resolusi',
                            'status', 'diselesaikan_pada', 'diselesaikan_oleh'])

    if resolusi == Resolusi.KIRIM_SUSULAN:
        po = lap.penerimaan.purchase_order
        if po.status == StatusPO.SELESAI and not po.semua_item_lengkap():
            po.status = StatusPO.SEBAGIAN
            po.save(update_fields=['status'])

    return lap


@transaction.atomic
def tutup_laporan(*, laporan_id, user, alasan):
    """Ditutup tanpa klaim. Selisihnya diserap sebagai beban."""
    lap = LaporanSelisih.objects.select_for_update().get(pk=laporan_id)
    if lap.status in (StatusSelisih.DISELESAIKAN, StatusSelisih.DITUTUP):
        raise ValidationError(f'Laporan sudah {lap.get_status_display()}.')
    if not alasan or not alasan.strip():
        raise ValidationError('Alasan penutupan wajib diisi.')

    lap.status = StatusSelisih.DITUTUP
    lap.resolusi = Resolusi.TERIMA_APA_ADANYA
    lap.nilai_klaim = Decimal('0')
    lap.catatan_resolusi = alasan
    lap.diselesaikan_pada = timezone.now()
    lap.diselesaikan_oleh = user
    lap.save(update_fields=['status', 'resolusi', 'nilai_klaim',
                            'catatan_resolusi', 'diselesaikan_pada',
                            'diselesaikan_oleh'])
    return lap


def klaim_belum_diselesaikan(suplier_id=None, entitas_id=None):
    qs = (LaporanSelisih.objects
          .exclude(status__in=[StatusSelisih.DISELESAIKAN,
                               StatusSelisih.DITUTUP])
          .select_related('penerimaan__purchase_order__suplier',
                          'penerimaan__purchase_order__entitas'))
    if suplier_id:
        qs = qs.filter(penerimaan__purchase_order__suplier_id=suplier_id)
    if entitas_id:
        qs = qs.filter(penerimaan__purchase_order__entitas_id=entitas_id)
    return qs.order_by('tanggal')


def total_potongan(penerimaan_id):
    return LaporanSelisih.objects.filter(
        penerimaan_id=penerimaan_id,
        resolusi=Resolusi.POTONG_TAGIHAN,
        status=StatusSelisih.DISELESAIKAN,
    ).aggregate(t=Sum('nilai_klaim'))['t'] or Decimal('0')


def ringkasan_penerimaan(penerimaan_id):
    p = (PenerimaanBarang.objects
         .select_related('purchase_order__suplier', 'purchase_order__entitas')
         .prefetch_related('item__po_item', 'item__pembelian',
                           'laporan_selisih')
         .get(pk=penerimaan_id))

    return {
        'nomor': p.nomor,
        'tanggal': p.tanggal,
        'surat_jalan': p.no_surat_jalan,
        'po': p.purchase_order.no_po,
        'suplier': p.purchase_order.suplier.nama,
        'entitas': p.purchase_order.entitas.kode,
        'total_koli': p.total_koli,
        'ada_selisih': p.ada_selisih,
        'toleransi_persen': str(TOLERANSI_BERAT * 100),
        'item': [{
            'nama': i.po_item.nama_item,
            'kemasan': i.get_jenis_kemasan_display(),
            'koli': i.jumlah_koli,
            'isi_per_koli': i.isi_per_koli,
            'deklarasi': i.qty_deklarasi,
            'timbang': i.qty_diterima,
            'ditolak': i.qty_ditolak,
            'selisih_berat': i.selisih_berat,
            'persen': i.persen_selisih_berat,

            'setoran': getattr(i, 'pembelian', None)
                       and i.pembelian.nomor,
        } for i in p.item.all()],
        'selisih': [{
            'nomor': l.nomor,
            'jenis': l.get_jenis_display(),
            'qty': l.qty_selisih,
            'nilai': l.nilai_selisih,
            'status': l.get_status_display(),
            'resolusi': l.get_resolusi_display() if l.resolusi else None,
            'klaim': l.nilai_klaim,
        } for l in p.laporan_selisih.all()],
    }

from .models import DeliveryOrder

def distribusi_siap_kirim(entitas_id=None):
    """Mengembalikan daftar DO asli dari database yang berstatus DRAFT."""
    
    dos = DeliveryOrder.objects.filter(status='DRAFT').order_by('tanggal')
    
    hasil = []
    for do in dos:
        hasil.append({
            'id': do.id,
            'nomor': do.nomor_do,
            'pelanggan_nama': 'Pelanggan DO (Belum ada relasi)', 
            'alamat': 'Belum ada alamat',
            'lat': None,
            'lng': None,
            'berat_kg': Decimal('0.0')
        })
    return hasil

def rincian_distribusi(distribusi_id):
    """Mengembalikan detail DO beserta baris produknya dari database."""
    try:
        do = DeliveryOrder.objects.prefetch_related('item__produk').get(id=distribusi_id)
    except DeliveryOrder.DoesNotExist:
        return {}
    
    hasil = {
        'id': do.id,
        'nomor': do.nomor_do,
        'pelanggan_nama': 'Pelanggan DO (Belum ada relasi)',
        'alamat': 'Belum ada alamat',
        'lat': None,
        'lng': None,
        'berat_kg': Decimal('0.0'),
        'baris': []
    }
    
    for itm in do.item.all():
        hasil['baris'].append({
            'produk_kode': getattr(itm.produk, 'kode', '-'),
            'produk_nama': getattr(itm.produk, 'nama', '-'),
            'stiker': '-', # Fitur stiker belum ada di model DeliveryOrderItem
            'qty': itm.qty,
            'unit': 'KG'
        })
    return hasil

def tandai_terkirim(distribusi_id, waktu, oleh):
    """Mengubah status Delivery Order nyata di database."""
    DeliveryOrder.objects.filter(id=distribusi_id).update(status='SELESAI')

def kembalikan_stok(distribusi_id, alasan, oleh):
    """
    Mengubah status retur. 
    (Logika penambahan stok fisik nanti diletakkan di sini).
    """
    DeliveryOrder.objects.filter(id=distribusi_id).update(status='RETUR')