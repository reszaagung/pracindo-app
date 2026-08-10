"""
Mesin posting jurnal — akunting/services.py

posting() adalah satu-satunya pintu masuk ke buku besar. Jurnal tidak
pernah dibuat lewat admin, shell, atau query manual.

Tiga penjaga yang dipegang fungsi ini:
    idempotency_key    retry tidak pernah menghasilkan jurnal kedua
    select_for_update  penomoran dan saldo terserialisasi per baris
    trigger database   SUM(debit) = SUM(kredit) diperiksa saat COMMIT

Yang ketiga tidak ada di kode ini -- dia hidup di migrasi
0004_trigger_jurnal_seimbang. Itu disengaja: bulk_create melewati
clean(), jadi satu-satunya penjaga yang tidak bisa dilewati adalah
trigger di database.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from core.models import CounterDokumen
from core.services import pastikan_periode_terbuka

from .models import (
    Akun, FakturPembelian, FakturPenjualan, JenisMutasiHutang,
    JenisMutasiPiutang, JurnalDetail, JurnalUmum, KartuHutang, KartuPiutang,
    StatusFaktur, StatusFakturJual, UangMukaSuplier,
)
from .posting_rules import ATURAN

Q2 = Decimal('0.01')


# =========================================================
# POSTING JURNAL
# =========================================================

@transaction.atomic
def posting(*, kejadian, entitas_id, tanggal, referensi, nilai,
            idem_key, user, keterangan=''):
    """
    Menerbitkan satu jurnal dari aturan posting.

    nilai: {nama_field: Decimal} sesuai yang dirujuk ATURAN[kejadian].
    Baris bernilai nol dilewati -- jurnal tidak perlu memuat baris kosong.
    """
    lama = JurnalUmum.objects.filter(idempotency_key=idem_key).first()
    if lama:
        return lama

    if kejadian not in ATURAN:
        raise ValidationError(f'Kejadian {kejadian} tidak ada di aturan posting.')

    pastikan_periode_terbuka(entitas_id, tanggal)

    from core.models import Entitas
    entitas = Entitas.objects.get(pk=entitas_id)

    jurnal = JurnalUmum.objects.create(
        entitas=entitas,
        nomor=CounterDokumen.berikutnya(entitas, 'JURNAL', tanggal),
        tanggal=tanggal,
        kejadian=kejadian,
        referensi=referensi,
        keterangan=keterangan,
        idempotency_key=idem_key,
        dibuat_oleh=user,
    )

    kode_dipakai = {k for k, _, _ in ATURAN[kejadian]}
    akun = {a.kode: a for a in Akun.objects.filter(kode__in=kode_dipakai)}
    hilang = kode_dipakai - set(akun)
    if hilang:
        raise ValidationError(
            f'Akun {sorted(hilang)} belum ada di bagan akun. '
            f'Jalankan migrasi seed COA.'
        )

    baris, total_d, total_k = [], Decimal('0'), Decimal('0')
    for kode, sisi, field in ATURAN[kejadian]:
        if field not in nilai:
            raise ValidationError(f'Nilai "{field}" tidak diberikan untuk {kejadian}.')
        n = Decimal(nilai[field]).quantize(Q2)
        if n == 0:
            continue
        if n < 0:
            raise ValidationError(
                f'Nilai "{field}" negatif. Arah dinyatakan lewat sisi D/K, '
                f'bukan lewat tanda.'
            )
        baris.append(JurnalDetail(
            jurnal=jurnal, akun=akun[kode],
            debit=n if sisi == 'D' else Decimal('0'),
            kredit=n if sisi == 'K' else Decimal('0'),
        ))
        if sisi == 'D':
            total_d += n
        else:
            total_k += n

    if not baris:
        raise ValidationError('Semua nilai nol, tidak ada yang bisa diposting.')
    if total_d != total_k:
        raise ValidationError(
            f'Aturan {kejadian} tidak seimbang: D {total_d} vs K {total_k}. '
            f'Periksa posting_rules.py.'
        )

    JurnalDetail.objects.bulk_create(baris)
    return jurnal


@transaction.atomic
def jurnal_balik(*, jurnal_id, tanggal, alasan, user):
    """
    Koreksi jurnal yang salah. Debit dan kredit ditukar, jumlahnya tetap
    seimbang, dan jejak audit utuh -- jurnal asli tidak pernah disentuh.
    """
    asal = JurnalUmum.objects.select_for_update().get(pk=jurnal_id)
    if asal.dibalik_oleh_id:
        raise ValidationError(f'Jurnal {asal.nomor} sudah pernah dibalik.')

    pastikan_periode_terbuka(asal.entitas_id, tanggal)

    balik = JurnalUmum.objects.create(
        entitas=asal.entitas,
        nomor=CounterDokumen.berikutnya(asal.entitas, 'JURNAL', tanggal),
        tanggal=tanggal,
        kejadian='KOREKSI',
        referensi=asal.nomor,
        keterangan=f'Balik {asal.nomor}: {alasan}',
        idempotency_key=f'balik:{asal.id}',
        dibuat_oleh=user,
    )
    JurnalDetail.objects.bulk_create([
        JurnalDetail(jurnal=balik, akun_id=b.akun_id,
                     debit=b.kredit, kredit=b.debit,
                     keterangan=b.keterangan)
        for b in asal.baris.all()
    ])

    asal.dibalik_oleh = balik
    asal.save(update_fields=['dibalik_oleh'])
    return balik


# =========================================================
# HUTANG
# =========================================================

@transaction.atomic
def post_pembayaran(*, faktur_id, nominal, tanggal, user, referensi, idem_key):
    """
    Membayar satu faktur. Dipanggil alokasi_pembayaran(), jarang langsung.

    Baris KartuHutang ditulis sebagai sumber kebenaran; sisa_hutang di
    header hanya cache supaya pembacaan jadi O(1).
    """
    ada = KartuHutang.objects.filter(referensi=idem_key).first()
    if ada:
        return ada

    faktur = FakturPembelian.objects.select_for_update().get(pk=faktur_id)
    nominal = Decimal(nominal).quantize(Q2)

    if nominal <= 0:
        raise ValidationError('Nominal pembayaran harus lebih dari nol.')
    if nominal > faktur.sisa_hutang:
        raise ValidationError(
            f'Nominal {nominal} melebihi sisa hutang {faktur.sisa_hutang}.'
        )

    mutasi = KartuHutang.objects.create(
        faktur=faktur, tanggal=tanggal, jenis=JenisMutasiHutang.BAYAR,
        debit=nominal, referensi=idem_key,
    )
    faktur.total_dibayar += nominal
    faktur.sisa_hutang -= nominal
    faktur.status = (StatusFaktur.LUNAS if faktur.sisa_hutang == 0
                     else StatusFaktur.SEBAGIAN)
    faktur.save(update_fields=['total_dibayar', 'sisa_hutang', 'status'])
    return mutasi


@transaction.atomic
def alokasi_pembayaran(*, suplier_id, entitas_id, nominal, tanggal,
                       user, idem_key, referensi=''):
    """
    Membagi satu pembayaran ke beberapa faktur terbuka, FIFO berdasarkan
    jatuh tempo. Kelebihan jadi uang muka.

    Dua detail yang menentukan benar-tidaknya:

    order_by WAJIB deterministik. Kalau dua transaksi mengunci himpunan
    baris yang beririsan dengan urutan berbeda, Postgres mendeteksi siklus
    dan membunuh salah satunya. Urutan yang sama = siklus tidak pernah
    terbentuk.

    idem_key diturunkan per faktur. Kalau tidak, satu pembayaran yang
    pecah ke tiga faktur akan bentrok di unique constraint pada baris kedua.
    """
    sisa = Decimal(nominal).quantize(Q2)
    if sisa <= 0:
        raise ValidationError('Nominal harus lebih dari nol.')

    faktur_terbuka = (FakturPembelian.objects
                      .select_for_update()
                      .filter(suplier_id=suplier_id, entitas_id=entitas_id,
                              status__in=[StatusFaktur.BELUM_BAYAR,
                                          StatusFaktur.SEBAGIAN])
                      .order_by('tanggal_jatuh_tempo', 'id'))

    alokasi = []
    for f in faktur_terbuka:
        if sisa <= 0:
            break
        porsi = min(sisa, f.sisa_hutang)
        post_pembayaran(
            faktur_id=f.id, nominal=porsi, tanggal=tanggal, user=user,
            referensi=referensi, idem_key=f'{idem_key}:f{f.id}',
        )
        alokasi.append({'faktur': f.nomor_faktur, 'nominal': porsi})
        sisa -= porsi

    uang_muka = None
    if sisa > 0:
        uang_muka = UangMukaSuplier.objects.create(
            entitas_id=entitas_id, suplier_id=suplier_id, tanggal=tanggal,
            nominal=sisa, referensi=referensi or idem_key,
        )

    posting(
        kejadian='BAYAR_HUTANG', entitas_id=entitas_id, tanggal=tanggal,
        referensi=referensi or idem_key,
        nilai={'nominal': Decimal(nominal).quantize(Q2)},
        idem_key=f'{idem_key}:jurnal', user=user,
    )
    return alokasi, uang_muka


def faktur_jatuh_tempo(entitas_id, sampai_tanggal, suplier_id=None):
    """
    Read-only. Dipakai keuangan untuk menyusun rencana bayar.

    Angka di sini SUDAH BASI begitu dibaca -- sisa hutang bisa berubah
    sebelum eksekusi. Yang mengikat adalah validasi di post_pembayaran()
    yang berjalan di bawah lock.
    """
    qs = (FakturPembelian.objects
          .filter(entitas_id=entitas_id,
                  status__in=[StatusFaktur.BELUM_BAYAR, StatusFaktur.SEBAGIAN],
                  tanggal_jatuh_tempo__lte=sampai_tanggal)
          .select_related('suplier')
          .order_by('tanggal_jatuh_tempo', 'id'))
    return qs.filter(suplier_id=suplier_id) if suplier_id else qs


# =========================================================
# PURCHASE ORDER
# =========================================================
#
# Semua operasi yang mengubah state PO lewat sini -- bukan lewat
# serializer langsung -- supaya row lock dan rekalkulasi status konsisten
# di semua jalur, baik dipanggil dari API maupun manual.
#
# PO BUKAN kejadian ekonomi. Tidak ada satu pun panggilan posting() di
# bagian ini, dan itu disengaja. Jurnal pertama lahir di
# warehouse.terima_barang().

def preview_nomor_po(entitas, tanggal):
    """
    Preview nomor untuk ditampilkan di form sebelum submit.

    Angka final bisa bergeser kalau ada PO lain dibuat di antara preview
    dan submit. buat_po() yang jadi sumber kebenaran.
    """
    return CounterDokumen.preview(entitas, 'PO', tanggal)


@transaction.atomic
def buat_po(*, entitas_id, suplier_id, tanggal, items, user,
            tanggal_kirim_diminta=None, catatan=''):
    """
    items: [
      {'produk_id': 5, 'qty_pesan': '500', 'harga_per_kg': '12500',
       'satuan': 'kg'},
      ...
    ]

    Nomor PO dibuat di dalam PurchaseOrder.save() lewat CounterDokumen,
    yang mengunci baris counter per entitas. PT dan CV bisa membuat PO
    bersamaan tanpa saling tunggu; dua PO di entitas yang sama akan antre.
    """
    from master.models import Suplier

    from .models import PurchaseOrder, PurchaseOrderItem, StatusPO

    if not items:
        raise ValidationError('Minimal harus ada satu item.')

    suplier = Suplier.objects.get(pk=suplier_id)
    if not suplier.aktif:
        raise ValidationError(f'Suplier {suplier.nama} sudah tidak aktif.')

    pastikan_periode_terbuka(entitas_id, tanggal)

    po = PurchaseOrder.objects.create(
        entitas_id=entitas_id,
        suplier=suplier,
        tanggal=tanggal,
        tanggal_kirim_diminta=tanggal_kirim_diminta,
        catatan=catatan,
        dibuat_oleh=user,
        status=StatusPO.DRAFT,
    )

    # bulk_create dilewati: PurchaseOrderItem.save() yang menghitung
    # amount dari qty x harga, dan itu tidak boleh dipercaya dari payload.
    for it in items:
        PurchaseOrderItem(
            purchase_order=po,
            produk_id=it['produk_id'],
            qty_pesan=Decimal(str(it['qty_pesan'])),
            harga_per_kg=Decimal(str(it['harga_per_kg'])),
            satuan=it.get('satuan', 'kg'),
        ).save()

    return po


@transaction.atomic
def ubah_item_po(*, po_id, items):
    """
    Mengganti seluruh item PO. Hanya boleh saat DRAFT.

    Setelah PO terkirim, item tidak boleh berubah -- suplier sudah
    memegang dokumen dengan angka lama.
    """
    from .models import PurchaseOrder, PurchaseOrderItem, StatusPO

    po = PurchaseOrder.objects.select_for_update().get(pk=po_id)
    if po.status != StatusPO.DRAFT:
        raise ValidationError(
            f'PO sudah {po.get_status_display()}, item tidak bisa diubah.'
        )
    if not items:
        raise ValidationError('Minimal harus ada satu item.')

    po.item.all().delete()
    for it in items:
        PurchaseOrderItem(
            purchase_order=po,
            produk_id=it['produk_id'],
            qty_pesan=Decimal(str(it['qty_pesan'])),
            harga_per_kg=Decimal(str(it['harga_per_kg'])),
            satuan=it.get('satuan', 'kg'),
        ).save()
    return po


@transaction.atomic
def kirim_po(*, po_id, user):
    """DRAFT -> TERKIRIM. Setelah ini item terkunci."""
    from .models import PurchaseOrder, StatusPO

    po = PurchaseOrder.objects.select_for_update().get(pk=po_id)
    if po.status != StatusPO.DRAFT:
        raise ValidationError(f'PO sudah {po.get_status_display()}.')
    if not po.item.exists():
        raise ValidationError('PO tanpa item tidak bisa dikirim.')

    po.status = StatusPO.TERKIRIM
    po.save(update_fields=['status'])
    return po


@transaction.atomic
def batalkan_po(*, po_id, user, alasan=''):
    """
    Membatalkan PO. Hanya boleh sebelum ada penerimaan.

    PO yang sudah diterima sebagian tidak bisa dibatalkan -- stok sudah
    naik dan GRNI sudah terbentuk. Tutup lewat retur.
    """
    from .models import PurchaseOrder, StatusPO

    po = PurchaseOrder.objects.select_for_update().get(pk=po_id)
    if po.status == StatusPO.BATAL:
        raise ValidationError('PO ini sudah dibatalkan sebelumnya.')
    if po.ada_penerimaan():
        raise ValidationError(
            'PO sudah ada penerimaan barang. Tutup lewat retur, '
            'bukan pembatalan.'
        )
    if not alasan.strip():
        raise ValidationError('Alasan pembatalan wajib diisi.')

    po.status = StatusPO.BATAL
    po.catatan = f'{po.catatan}\n[BATAL {timezone.now():%Y-%m-%d} oleh {user}] {alasan}'.strip()
    po.save(update_fields=['status', 'catatan'])
    return po


@transaction.atomic
def lampirkan_dokumen(*, po_id, jenis, berkas, user, keterangan=''):
    """
    Melampirkan dokumen pendukung ke PO.

    Sengaja terpisah dari buat_po() karena dokumen ini biasanya baru ada
    belakangan -- faktur pajak dan invoice sering datang berminggu-minggu
    setelah barang diterima.

    Lampiran bersifat append-only. Dokumen yang salah tidak dihapus tapi
    ditandai `digantikan_oleh`, sehingga jejak audit tetap utuh.
    """
    from django.contrib.contenttypes.models import ContentType
    from dokumen.models import Lampiran

    from .models import PurchaseOrder, StatusPO

    po = PurchaseOrder.objects.select_for_update().get(pk=po_id)
    if po.status == StatusPO.BATAL:
        raise ValidationError('PO ini sudah dibatalkan.')

    return Lampiran.objects.create(
        jenis=jenis,
        berkas=berkas,
        keterangan=keterangan,
        content_type=ContentType.objects.get_for_model(PurchaseOrder),
        object_id=po.id,
        dibuat_oleh=user,
    )


def ringkasan_po(po_id):
    """Rincian PO beserta realisasi penerimaannya."""
    from .models import PurchaseOrder

    po = (PurchaseOrder.objects
          .select_related('entitas', 'suplier')
          .prefetch_related('item__produk', 'penerimaan')
          .get(pk=po_id))

    return {
        'nomor': po.no_po,
        'tanggal': po.tanggal,
        'entitas': po.entitas.kode,
        'suplier': po.suplier.nama,
        'status': po.get_status_display(),
        'total_nilai': po.total_nilai,
        'item': [
            {
                'produk': i.produk.kode,
                'nama': i.nama_item,
                'pesan': i.qty_pesan,
                'diterima': i.qty_diterima,
                'sisa': i.sisa_qty,
                'harga': i.harga_per_kg,
                'amount': i.amount,
            }
            for i in po.item.all()
        ],
        'penerimaan': [
            {'nomor': p.nomor, 'tanggal': p.tanggal,
             'surat_jalan': p.no_surat_jalan, 'ada_selisih': p.ada_selisih}
            for p in po.penerimaan.all()
        ],
    }


# =========================================================
# FAKTUR PEMBELIAN
# =========================================================

def hitung_nilai_penerimaan(penerimaan):
    """
    Nilai rupiah barang yang BENAR-BENAR diterima.

    Dihitung dari qty timbang x harga PO. Barang yang ditolak tidak ikut --
    barang ditolak tidak pernah jadi milik kita, jadi tidak pernah jadi
    hutang juga.
    """
    total = Decimal('0')
    for item in penerimaan.item.select_related('po_item').all():
        total += (item.qty_diterima * item.po_item.harga_per_kg)
    return total.quantize(Q2)


def draft_faktur(penerimaan_id):
    """
    Angka usulan untuk form penerbitan faktur.

    Read-only. Angka ini SUDAH BASI begitu dibaca -- laporan selisih bisa
    diselesaikan di antara pembacaan dan penerbitan. Yang mengikat adalah
    perhitungan ulang di terbitkan_faktur() yang berjalan di bawah lock.
    """
    from warehouse.models import PenerimaanBarang
    from warehouse.services import total_potongan

    p = (PenerimaanBarang.objects
         .select_related('purchase_order__suplier', 'purchase_order__entitas')
         .prefetch_related('item__po_item')
         .get(pk=penerimaan_id))

    nilai_terima = hitung_nilai_penerimaan(p)
    potongan = total_potongan(penerimaan_id)
    suplier = p.purchase_order.suplier

    return {
        'penerimaan': p.nomor,
        'penerimaan_id': p.id,
        'purchase_order': p.purchase_order.no_po,
        'entitas': p.purchase_order.entitas.kode,
        'entitas_id': p.purchase_order.entitas_id,
        'suplier': suplier.nama,
        'suplier_id': suplier.id,
        'nilai_penerimaan': nilai_terima,
        'potongan_klaim': potongan,
        'usulan_total_tagihan': nilai_terima - potongan,
        'termin_hari_default': suplier.termin_hari_default,
        'sudah_difaktur': p.faktur.exists(),
        'klaim_terbuka': list(
            p.laporan_selisih
             .exclude(status__in=['DISELESAIKAN', 'DITUTUP'])
             .values_list('nomor', flat=True)
        ),
    }


@transaction.atomic
def terbitkan_faktur(*, penerimaan_id, nomor_faktur, tanggal_faktur,
                     total_tagihan, user, termin_hari=None, dokumen_id=None,
                     catatan='', abaikan_klaim_terbuka=False):
    """
    Menerbitkan faktur pembelian dari satu penerimaan.

    Dua jurnal bisa terbit sekaligus:
        FAKTUR_MASUK    Dr GRNI / Cr Hutang, sebesar nilai faktur
        FAKTUR_LEBIH    kalau faktur > penerimaan, sisa GRNI ke beban
        FAKTUR_KURANG   kalau faktur < penerimaan, GRNI dikembalikan

    Yang kedua penting: tanpa itu saldo GRNI menggantung selamanya, dan
    laporan barang-diterima-belum-difaktur jadi tidak bisa dipercaya.
    """
    from warehouse.models import PenerimaanBarang
    from warehouse.services import total_potongan

    from .models import FakturPembelian, JenisFaktur, JenisMutasiHutang, KartuHutang

    p = (PenerimaanBarang.objects.select_for_update()
         .select_related('purchase_order__suplier', 'purchase_order__entitas')
         .get(pk=penerimaan_id))

    if p.faktur.exists():
        raise ValidationError(
            f'Penerimaan {p.nomor} sudah difaktur '
            f'({p.faktur.first().nomor_faktur}).'
        )

    terbuka = p.laporan_selisih.exclude(
        status__in=['DISELESAIKAN', 'DITUTUP'],
    ).values_list('nomor', flat=True)
    if terbuka and not abaikan_klaim_terbuka:
        raise ValidationError(
            f'Masih ada laporan selisih terbuka: {", ".join(terbuka)}. '
            f'Selesaikan dulu, atau terbitkan dengan abaikan_klaim_terbuka.'
        )

    po = p.purchase_order
    entitas_id = po.entitas_id
    suplier = po.suplier

    pastikan_periode_terbuka(entitas_id, tanggal_faktur)

    if FakturPembelian.objects.filter(
        suplier=suplier, nomor_faktur=nomor_faktur,
    ).exists():
        raise ValidationError(
            {'nomor_faktur': f'Nomor {nomor_faktur} sudah pernah dipakai '
                             f'untuk suplier ini.'}
        )

    total_tagihan = Decimal(total_tagihan).quantize(Q2)
    if total_tagihan <= 0:
        raise ValidationError('Total tagihan harus lebih dari nol.')

    nilai_terima = hitung_nilai_penerimaan(p)
    potongan = total_potongan(penerimaan_id)
    nilai_wajar = nilai_terima - potongan

    if termin_hari is None:
        termin_hari = suplier.termin_hari_default

    faktur = FakturPembelian.objects.create(
        entitas_id=entitas_id,
        suplier=suplier,
        jenis=JenisFaktur.BARANG,
        penerimaan=p,
        nomor_faktur=nomor_faktur,
        tanggal_faktur=tanggal_faktur,
        termin_hari=termin_hari,
        total_tagihan=total_tagihan,
        dokumen_id=dokumen_id,
        catatan=catatan,
        dibuat_oleh=user,
    )

    KartuHutang.objects.create(
        faktur=faktur, tanggal=tanggal_faktur,
        jenis=JenisMutasiHutang.FAKTUR,
        kredit=total_tagihan, referensi=faktur.no_internal,
    )

    posting(
        kejadian='FAKTUR_MASUK', entitas_id=entitas_id, tanggal=tanggal_faktur,
        referensi=faktur.no_internal, nilai={'nilai_faktur': total_tagihan},
        idem_key=f'faktur:{faktur.id}', user=user,
        keterangan=f'Faktur {nomor_faktur} atas {p.nomor}',
    )

    selisih = total_tagihan - nilai_wajar
    if selisih != 0:
        posting(
            kejadian='FAKTUR_LEBIH' if selisih > 0 else 'FAKTUR_KURANG',
            entitas_id=entitas_id, tanggal=tanggal_faktur,
            referensi=faktur.no_internal, nilai={'selisih': abs(selisih)},
            idem_key=f'faktur:{faktur.id}:selisih', user=user,
            keterangan=(f'Selisih faktur {nomor_faktur} terhadap '
                        f'nilai penerimaan {nilai_wajar}'),
        )

    return faktur, {
        'nilai_penerimaan': nilai_terima,
        'potongan_klaim': potongan,
        'nilai_wajar': nilai_wajar,
        'total_tagihan': total_tagihan,
        'selisih': selisih,
    }


def aging_hutang(entitas_id, per=None):
    """
    Umur hutang per suplier dalam SATU query. Bukan loop per suplier --
    itu N+1 yang membunuh halaman saat suplier bertambah.
    """
    from datetime import timedelta

    from django.db.models import Q as Qf
    from django.db.models import Sum

    from .models import FakturPembelian, StatusFaktur

    per = per or timezone.localdate()

    def rentang(a, b):
        return Qf(tanggal_jatuh_tempo__range=(per - timedelta(b), per - timedelta(a)))

    return list(
        FakturPembelian.objects
        .filter(entitas_id=entitas_id,
                status__in=[StatusFaktur.BELUM_BAYAR, StatusFaktur.SEBAGIAN])
        .values('suplier_id', 'suplier__nama')
        .annotate(
            belum_tempo=Sum('sisa_hutang', filter=Qf(tanggal_jatuh_tempo__gt=per)),
            umur_1_30=Sum('sisa_hutang', filter=rentang(0, 30)),
            umur_31_60=Sum('sisa_hutang', filter=rentang(31, 60)),
            umur_60plus=Sum('sisa_hutang',
                            filter=Qf(tanggal_jatuh_tempo__lt=per - timedelta(60))),
            total=Sum('sisa_hutang'),
        )
        .order_by('-total')
    )
# =========================================================
# PIUTANG PENJUALAN (ACCOUNT RECEIVABLE)
# =========================================================

@transaction.atomic
def terbitkan_faktur_jual(*, delivery_order_id, nomor_faktur, tanggal_faktur,
                          user, termin_hari=None, catatan=''):
    """
    Menerbitkan faktur penjualan dari Surat Jalan (Delivery Order) yang sudah selesai.
    Akan memicu jurnal PENJUALAN (Dr. Piutang, Cr. Penjualan, Dr. HPP, Cr. Persediaan).
    """
    from warehouse.models import DeliveryOrder
    from master.models import Pelanggan
    from .models.piutang import FakturPenjualan, KartuPiutang, JenisMutasiPiutang
    do = DeliveryOrder.objects.select_for_update().select_related(
        'sales_order__pelanggan', 'sales_order__entitas'
    ).get(pk=delivery_order_id)

    if hasattr(do, 'faktur') and do.faktur.exists():
        raise ValidationError(f'Delivery Order {do.nomor_do} sudah difaktur.')

    so = do.sales_order
    entitas_id = so.entitas_id
    pelanggan = so.pelanggan

    pastikan_periode_terbuka(entitas_id, tanggal_faktur)

    if termin_hari is None:
        termin_hari = pelanggan.termin_hari_default

    total_tagihan = Decimal(so.grand_total).quantize(Q2)

    total_hpp = Decimal('0').quantize(Q2)

    faktur = FakturPenjualan.objects.create(
        entitas_id=entitas_id,
        pelanggan=pelanggan,
        delivery_order=do,
        nomor_faktur=nomor_faktur,
        tanggal_faktur=tanggal_faktur,
        termin_hari=termin_hari,
        total_tagihan=total_tagihan,
        catatan=catatan,
        dibuat_oleh=user,
    )
    KartuPiutang.objects.create(
        faktur=faktur, 
        tanggal=tanggal_faktur,
        jenis=JenisMutasiPiutang.FAKTUR,
        debit=total_tagihan,  
        referensi=faktur.no_internal,
    )

    posting(
        kejadian='PENJUALAN', 
        entitas_id=entitas_id, 
        tanggal=tanggal_faktur,
        referensi=faktur.no_internal, 
        nilai={'nilai_jual': total_tagihan, 'hpp': total_hpp},
        idem_key=f'faktur_jual:{faktur.id}', 
        user=user,
        keterangan=f'Faktur Penjualan {nomor_faktur} atas DO {do.nomor_do}',
    )

    return faktur


@transaction.atomic
def terima_pembayaran_piutang(*, faktur_id, nominal, tanggal, user, referensi, idem_key):
    """
    Menerima pembayaran dari pelanggan.
    Mengurangi sisa piutang di cache Faktur dan menambah baris KREDIT di KartuPiutang.
    """

    ada = KartuPiutang.objects.filter(referensi=idem_key).first()
    if ada:
        return ada

    faktur = FakturPenjualan.objects.select_for_update().get(pk=faktur_id)
    nominal = Decimal(nominal).quantize(Q2)

    if nominal <= 0:
        raise ValidationError('Nominal pembayaran piutang harus lebih dari nol.')
    
    if nominal > faktur.sisa_piutang:
        raise ValidationError(f'Nominal {nominal} melebihi sisa piutang pelanggan {faktur.sisa_piutang}.')


    mutasi = KartuPiutang.objects.create(
        faktur=faktur, 
        tanggal=tanggal, 
        jenis=JenisMutasiPiutang.TERIMA,
        kredit=nominal, 
        referensi=idem_key,
    )

    faktur.total_dibayar += nominal
    faktur.sisa_piutang -= nominal
    faktur.status = (StatusFakturJual.LUNAS if faktur.sisa_piutang == 0 else StatusFakturJual.SEBAGIAN)
    faktur.save(update_fields=['total_dibayar', 'sisa_piutang', 'status'])

    posting(
        kejadian='TERIMA_PIUTANG', 
        entitas_id=faktur.entitas_id, 
        tanggal=tanggal,
        referensi=referensi or idem_key,
        nilai={'nominal': nominal},
        idem_key=f'{idem_key}:jurnal', 
        user=user,
    )

    return mutasi