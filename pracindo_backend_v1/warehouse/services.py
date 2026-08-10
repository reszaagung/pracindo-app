"""
Logika bisnis penerimaan barang — warehouse/services.py

terima_barang() adalah kejadian ekonomi pertama dalam pipeline pembelian.
Empat hal terjadi dalam SATU transaksi atomik:

    1. Baris penerimaan dan itemnya tercatat
    2. Stok RAW naik, pemilik = entitas PO
    3. Jurnal Dr Persediaan / Cr GRNI terposting
    4. Laporan selisih terbit otomatis kalau ada ketidaksesuaian

Kalau salah satu gagal, semuanya batal. Tidak pernah ada kondisi
"stok sudah naik tapi hutang belum tercatat".

TIGA ANGKA
    qty PO         yang dipesan
    qty deklarasi  jumlah koli x isi per koli
    qty timbang    hasil timbangan -- INI yang dipakai untuk stok dan nilai

GUDANG TIDAK MELIHAT HARGA. Payload dari frontend gudang tidak pernah
membawa angka rupiah. nilai_terima dihitung di server dari harga yang
tersimpan di PO, sehingga tidak ada yang bisa dimanipulasi dari klien.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from core.services import pastikan_periode_terbuka

from .models import (
    JenisKemasan, JenisSelisih, LaporanSelisih, PenerimaanBarang,
    PenerimaanItem, Resolusi, StatusSelisih,
)

Q3 = Decimal('0.001')
Q2 = Decimal('0.01')

# Selisih berat di bawah ambang ini dianggap toleransi timbangan dan
# tidak menerbitkan laporan. 0.5% adalah angka awal yang wajar untuk
# komoditas kg-based; sesuaikan dengan kesepakatan suplier.
TOLERANSI_BERAT = Decimal('0.005')


# =========================================================
# PENERIMAAN
# =========================================================

@transaction.atomic
def terima_barang(*, po_id, baris, no_surat_jalan, tanggal, user,
                  dokumen_id=None, catatan='', idem_key=None):
    """
    Mencatat penerimaan barang dari suplier.

    baris: [
      {
        'po_item_id': 12,
        'jenis_kemasan': 'KARUNG',
        'jumlah_koli': 20,
        'isi_per_koli': '25.000',
        'qty_diterima': '498.500',      # hasil timbangan
        'qty_ditolak': '0',
        'alasan_tolak': '',
      }, ...
    ]

    Grup bahan TIDAK dikirim klien -- diturunkan dari po.entitas.grup_bahan.
    Sudah tersimpan di master, jadi tidak ada peluang gudang salah pilih pool.

    Tangki juga tidak dikirim. Semua penerimaan saat ini masuk rak. Kalau
    nanti ada bahan cair yang datang lewat tangki, parameter ini harus
    dihidupkan lagi dan Produk.disimpan_di_tanki jadi penentunya.

    Unggah dokumen surat jalan HARUS dilakukan sebelum memanggil fungsi
    ini, lalu dokumen_id dikirim sebagai parameter. Kalau upload file
    dilakukan di dalam blok atomic, kegagalan transaksi meninggalkan file
    yatim di storage sementara barisnya di-rollback.

    Return: (penerimaan, [laporan_selisih, ...])
    """
    from akunting.models import PurchaseOrder, StatusPO

    if not baris:
        raise ValidationError('Tidak ada baris barang yang diterima.')

    po = (PurchaseOrder.objects.select_for_update()
          .select_related('entitas', 'entitas__grup_bahan').get(pk=po_id))
    if po.status == StatusPO.SELESAI:
        raise ValidationError('PO sudah diterima penuh.')
    if po.status in (StatusPO.DRAFT, StatusPO.BATAL):
        raise ValidationError(f'PO berstatus {po.get_status_display()}, belum bisa diterima.')

    pastikan_periode_terbuka(po.entitas_id, tanggal)

    if PenerimaanBarang.objects.filter(
        purchase_order=po, no_surat_jalan=no_surat_jalan,
    ).exists():
        raise ValidationError(
            f'Surat jalan {no_surat_jalan} sudah pernah diterima untuk PO ini.'
        )

    penerimaan = PenerimaanBarang.objects.create(
        purchase_order=po, tanggal=tanggal, no_surat_jalan=no_surat_jalan,
        dokumen_id=dokumen_id, catatan=catatan, dibuat_oleh=user,
    )

    nilai_terima = Decimal('0')
    laporan = []

    for b in baris:
        item = _simpan_item(penerimaan, b, po)
        nilai_terima += _naikkan_stok(penerimaan, item, po)
        laporan.extend(_periksa_selisih(penerimaan, item, user))

    if nilai_terima <= 0:
        raise ValidationError(
            'Seluruh barang ditolak. Terbitkan laporan selisih saja, '
            'jangan catat sebagai penerimaan.'
        )

    po.refresh_from_db()
    po.status = StatusPO.SELESAI if po.semua_item_lengkap() else StatusPO.SEBAGIAN
    po.save(update_fields=['status'])

    if laporan:
        penerimaan.ada_selisih = True
        penerimaan.save(update_fields=['ada_selisih'])

    _posting_penerimaan(penerimaan, nilai_terima, tanggal, user)
    return penerimaan, laporan


def _simpan_item(penerimaan, b, po):
    """Menyimpan satu baris item dengan validasi kemasan dan batas PO."""
    from akunting.models import PurchaseOrderItem

    po_item = PurchaseOrderItem.objects.select_for_update().get(
        pk=b['po_item_id'], purchase_order=po,
    )
    qty_terima = Decimal(str(b.get('qty_diterima', 0))).quantize(Q3)
    qty_tolak = Decimal(str(b.get('qty_ditolak', 0))).quantize(Q3)

    if qty_terima < 0 or qty_tolak < 0:
        raise ValidationError(f'{po_item.nama_item}: qty tidak boleh negatif.')
    if qty_terima == 0 and qty_tolak == 0:
        raise ValidationError(f'{po_item.nama_item}: isi qty diterima atau ditolak.')
    if qty_tolak and not b.get('alasan_tolak'):
        raise ValidationError(f'{po_item.nama_item}: alasan tolak wajib diisi.')

    # Yang dibandingkan dengan sisa PO adalah qty yang MASUK, bukan
    # termasuk yang ditolak -- barang ditolak tidak pernah jadi milik kita.
    if qty_terima > po_item.sisa_qty:
        raise ValidationError(
            f'{po_item.nama_item}: diterima {qty_terima} melebihi '
            f'sisa PO {po_item.sisa_qty}.'
        )

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
    return item


def _naikkan_stok(penerimaan, item, po):
    """
    Menaikkan stok RAW dan mengembalikan nilai rupiahnya.

    Dua hal diturunkan di server, tidak pernah dari payload gudang:
      nilai        dari harga yang tersimpan di PO
      grup_bahan   dari entitas PO -- PT masuk pool PT, CV/Agus/Marsini
                   masuk pool BERSAMA
    """
    from inventory.services import terima_raw

    nilai = (item.qty_diterima * item.po_item.harga_per_kg).quantize(Q2)

    terima_raw(
        produk_id=item.po_item.produk_id,
        grup_bahan_id=po.entitas.grup_bahan_id,
        entitas_id=po.entitas_id,
        qty=item.qty_diterima,
        nilai=nilai,
        tanggal=penerimaan.tanggal,
        referensi=penerimaan.nomor,
        idem_key=f'grn:{penerimaan.id}:item:{item.id}',
        tangki_id=None,
    )
    return nilai


def _posting_penerimaan(penerimaan, nilai_terima, tanggal, user):
    """
    Dr Persediaan / Cr GRNI.

    Liabilitas lahir DI SINI, bukan saat faktur. Faktur nanti hanya
    mereklasifikasi GRNI jadi hutang usaha dan menetapkan jatuh tempo.
    """
    from akunting.services import posting

    posting(
        kejadian='AUDIT_GUDANG',
        entitas_id=penerimaan.purchase_order.entitas_id,
        tanggal=tanggal,
        referensi=penerimaan.nomor,
        nilai={'nilai_terima': nilai_terima},
        idem_key=f'grn:{penerimaan.id}',
        user=user,
        keterangan=f'Penerimaan SJ {penerimaan.no_surat_jalan}',
    )


# =========================================================
# DETEKSI SELISIH
# =========================================================

def _periksa_selisih(penerimaan, item, user):
    """
    Menerbitkan laporan otomatis untuk setiap ketidaksesuaian.

    Tiga pemeriksaan terpisah karena maknanya berbeda:
      berat kurang  isi koli tidak sesuai label  -> klaim ke suplier
      kurang kirim  koli-nya memang kurang       -> kiriman susulan
      ditolak       mutu tidak diterima          -> retur atau ganti
    """
    hasil = []

    # 1. Selisih berat, hanya untuk kiriman berkemasan
    if item.qty_deklarasi:
        beda = item.selisih_berat
        ambang = (item.qty_deklarasi * TOLERANSI_BERAT).quantize(Q3)
        if abs(beda) > ambang:
            hasil.append(buat_laporan(
                penerimaan=penerimaan, item=item, user=user,
                jenis=JenisSelisih.BERAT_KURANG,
                qty_selisih=beda,
                uraian=(
                    f'Deklarasi {item.jumlah_koli} {item.get_jenis_kemasan_display()} '
                    f'x {item.isi_per_koli} = {item.qty_deklarasi}. '
                    f'Timbangan {item.qty_diterima + item.qty_ditolak}. '
                    f'Selisih {beda} ({item.persen_selisih_berat}%), '
                    f'melebihi toleransi {ambang}.'
                ),
            ))

    # 2. Barang ditolak karena mutu
    if item.qty_ditolak > 0:
        hasil.append(buat_laporan(
            penerimaan=penerimaan, item=item, user=user,
            jenis=JenisSelisih.RUSAK,
            qty_selisih=-item.qty_ditolak,
            uraian=f'Ditolak {item.qty_ditolak}. Alasan: {item.alasan_tolak}',
        ))

    return hasil


@transaction.atomic
def buat_laporan(*, penerimaan, item, user, jenis, qty_selisih,
                 uraian, foto_id=None):
    """
    Menerbitkan berita acara selisih.

    nilai_selisih dihitung dari harga PO -- gudang tidak mengisinya dan
    tidak melihatnya di serializer.
    """
    harga = item.po_item.harga_per_kg if item else Decimal('0')
    nilai = (abs(Decimal(qty_selisih)) * harga).quantize(Q2)

    lap = LaporanSelisih(
        penerimaan=penerimaan,
        penerimaan_item=item,
        tanggal=penerimaan.tanggal,
        jenis=jenis,
        qty_selisih=Decimal(qty_selisih).quantize(Q3),
        uraian=uraian,
        foto_id=foto_id,
        dibuat_oleh=user,
    )
    lap.save()
    LaporanSelisih.objects.filter(pk=lap.pk).update(nilai_selisih=nilai)
    lap.nilai_selisih = nilai
    return lap


@transaction.atomic
def laporan_manual(*, penerimaan_id, jenis, qty_selisih, uraian, user,
                   penerimaan_item_id=None, foto_id=None):
    """
    Laporan untuk temuan yang muncul setelah barang diterima -- misalnya
    kerusakan yang baru ketahuan saat dibongkar keesokan harinya.
    """
    penerimaan = PenerimaanBarang.objects.get(pk=penerimaan_id)
    item = (PenerimaanItem.objects.get(pk=penerimaan_item_id)
            if penerimaan_item_id else None)

    lap = buat_laporan(
        penerimaan=penerimaan, item=item, user=user, jenis=jenis,
        qty_selisih=qty_selisih, uraian=uraian, foto_id=foto_id,
    )
    if not penerimaan.ada_selisih:
        penerimaan.ada_selisih = True
        penerimaan.save(update_fields=['ada_selisih'])
    return lap


# =========================================================
# PENYELESAIAN SELISIH
# =========================================================

@transaction.atomic
def ajukan_ke_suplier(*, laporan_id, user):
    lap = LaporanSelisih.objects.select_for_update().get(pk=laporan_id)
    if lap.status != StatusSelisih.DIBUKA:
        raise ValidationError(f'Laporan sudah {lap.get_status_display()}.')
    lap.status = StatusSelisih.DIAJUKAN
    lap.save(update_fields=['status'])
    return lap


@transaction.atomic
def selesaikan_laporan(*, laporan_id, resolusi, user,
                       nilai_klaim=None, catatan=''):
    """
    Menetapkan konsekuensi selisih.

    TERIMA   nilai tidak berubah, selisih diserap sebagai beban
    POTONG   nilai_klaim mengurangi tagihan suplier; faktur nanti
             diterbitkan lebih rendah dari nilai penerimaan, dan
             sisanya masuk SELISIH_HARGA
    SUSULAN  PO tetap terbuka, tidak ada koreksi nilai
    RETUR    barang dikembalikan; stok dan GRNI dikoreksi lewat
             modul retur (belum dibangun)
    GANTI    suplier mengirim pengganti; tidak ada koreksi nilai

    Fungsi ini TIDAK memposting jurnal. Koreksi nilai terjadi saat faktur
    dicocokkan -- itulah gunanya akun SELISIH_HARGA.
    """
    lap = LaporanSelisih.objects.select_for_update().get(pk=laporan_id)
    if lap.status == StatusSelisih.DISELESAIKAN:
        raise ValidationError('Laporan sudah diselesaikan.')

    if resolusi == Resolusi.POTONG_TAGIHAN:
        if nilai_klaim is None:
            nilai_klaim = lap.nilai_selisih
        nilai_klaim = Decimal(nilai_klaim).quantize(Q2)
        if nilai_klaim <= 0:
            raise ValidationError('Potong tagihan harus punya nilai klaim.')
        if nilai_klaim > lap.nilai_selisih:
            raise ValidationError(
                f'Klaim {nilai_klaim} melebihi nilai selisih {lap.nilai_selisih}.'
            )
    else:
        nilai_klaim = Decimal('0')

    if resolusi == Resolusi.RETUR:
        raise ValidationError(
            'Retur belum didukung. Selesaikan sebagai potong tagihan '
            'atau kiriman susulan.'
        )

    lap.resolusi = resolusi
    lap.nilai_klaim = nilai_klaim
    lap.catatan_resolusi = catatan
    lap.status = StatusSelisih.DISELESAIKAN
    lap.diselesaikan_pada = timezone.now()
    lap.diselesaikan_oleh = user
    lap.save(update_fields=[
        'resolusi', 'nilai_klaim', 'catatan_resolusi',
        'status', 'diselesaikan_pada', 'diselesaikan_oleh',
    ])

    if resolusi == Resolusi.KIRIM_SUSULAN:
        _buka_kembali_po(lap)

    return lap


def _buka_kembali_po(lap):
    """Kiriman susulan berarti PO belum boleh ditutup."""
    from akunting.models import StatusPO

    po = lap.penerimaan.purchase_order
    if po.status == StatusPO.SELESAI and not po.semua_item_lengkap():
        po.status = StatusPO.SEBAGIAN
        po.save(update_fields=['status'])


@transaction.atomic
def tutup_laporan(*, laporan_id, user, alasan):
    """Menutup tanpa klaim -- selisih dianggap wajar setelah ditinjau."""
    lap = LaporanSelisih.objects.select_for_update().get(pk=laporan_id)
    if lap.status == StatusSelisih.DISELESAIKAN:
        raise ValidationError('Laporan sudah diselesaikan.')

    lap.status = StatusSelisih.DITUTUP
    lap.resolusi = Resolusi.TERIMA_APA_ADANYA
    lap.catatan_resolusi = alasan
    lap.diselesaikan_pada = timezone.now()
    lap.diselesaikan_oleh = user
    lap.save(update_fields=[
        'status', 'resolusi', 'catatan_resolusi',
        'diselesaikan_pada', 'diselesaikan_oleh',
    ])
    return lap


# =========================================================
# PEMBACAAN
# =========================================================

def klaim_belum_diselesaikan(suplier_id=None, entitas_id=None):
    """
    Selisih yang masih terbuka. Dipakai akunting sebelum menyetujui
    faktur -- jangan bayar penuh kalau masih ada klaim menggantung.
    """
    qs = (LaporanSelisih.objects
          .exclude(status__in=[StatusSelisih.DISELESAIKAN, StatusSelisih.DITUTUP])
          .select_related('penerimaan__purchase_order__suplier',
                          'penerimaan__purchase_order__entitas'))
    if suplier_id:
        qs = qs.filter(penerimaan__purchase_order__suplier_id=suplier_id)
    if entitas_id:
        qs = qs.filter(penerimaan__purchase_order__entitas_id=entitas_id)
    return qs.order_by('tanggal')


def total_potongan(penerimaan_id):
    """
    Jumlah klaim POTONG_TAGIHAN untuk satu penerimaan.

    Dipakai saat menerbitkan faktur: nilai faktur yang wajar adalah
    nilai penerimaan dikurangi angka ini.
    """
    from django.db.models import Sum

    return (LaporanSelisih.objects
            .filter(penerimaan_id=penerimaan_id,
                    resolusi=Resolusi.POTONG_TAGIHAN,
                    status=StatusSelisih.DISELESAIKAN)
            .aggregate(t=Sum('nilai_klaim'))['t'] or Decimal('0'))


def ringkasan_penerimaan(penerimaan_id):
    """Rincian lengkap satu penerimaan termasuk selisihnya."""
    p = (PenerimaanBarang.objects
         .select_related('purchase_order__suplier', 'purchase_order__entitas')
         .prefetch_related('item__po_item', 'laporan_selisih')
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
        'item': [
            {
                'nama': i.po_item.nama_item,
                'kemasan': i.get_jenis_kemasan_display(),
                'koli': i.jumlah_koli,
                'isi_per_koli': i.isi_per_koli,
                'deklarasi': i.qty_deklarasi,
                'timbang': i.qty_diterima,
                'ditolak': i.qty_ditolak,
                'selisih_berat': i.selisih_berat,
                'persen': i.persen_selisih_berat,
            }
            for i in p.item.all()
        ],
        'selisih': [
            {
                'nomor': l.nomor,
                'jenis': l.get_jenis_display(),
                'qty': l.qty_selisih,
                'status': l.get_status_display(),
                'resolusi': l.get_resolusi_display() if l.resolusi else None,
                'klaim': l.nilai_klaim,
            }
            for l in p.laporan_selisih.all()
        ],
    }
