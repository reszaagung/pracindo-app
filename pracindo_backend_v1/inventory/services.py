"""
Logika bisnis persediaan — inventory/services.py

TIGA LAPIS
    RAW   Bahan diterima. Pemilik melekat di SaldoEntitas.
    POOL  Pool produksi. TIDAK ADA pemilik. Hak tercatat di MutasiKlaim.
    JADI  Barang jadi. Pemilik melekat lagi setelah diklaim.

ALUR
    terima_raw()     PO diterima          -> RAW,  SaldoEntitas bertambah
    setor_ke_pool()  bahan disetor        -> RAW turun, POOL naik, klaim +
    pakai_dari_pool()produksi mengambil   -> POOL turun (tanpa pemilik)
    hasil_ke_pool()  produk jadi masuk    -> POOL naik (tanpa pemilik)
    klaim_hasil()    entitas mengambil    -> POOL turun, JADI naik, klaim -

INVARIANT
    (1) SUM(SaldoEntitas.qty)  == Stok.qty        untuk lapis RAW dan JADI
    (2) SUM(PosisiKlaim.bersih) == nilai sisa POOL  per grup bahan
    (3) saldo_akhir baris n == saldo_akhir n-1 + masuk - keluar

Ketiganya diperiksa fungsi verifikasi_* di bagian bawah. Jalankan nightly.
Kalau (2) melenceng, perhitungan siapa berhutang ke siapa sudah salah
tanpa ada error yang muncul.

Semua fungsi penulis idempoten lewat idempotency_key: retry jaringan atau
klik ganda tidak pernah menghasilkan baris kedua.
"""
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from core.services import pastikan_periode_terbuka

from .models import (
    JenisKlaim, JenisMutasiStok, Lapis, MutasiKlaim, MutasiStok,
    NilaiEkuivalen, PosisiKlaim, SaldoEntitas, Stok, Tangki,
)

Q3 = Decimal('0.001')
Q2 = Decimal('0.01')


# =========================================================
# HELPER INTERNAL
# =========================================================

def _tgl(t):
    return t.date() if hasattr(t, 'date') else t


def _stok(produk_id, grup_bahan_id, lapis, tangki_id=None):
    """Ambil-atau-buat baris Stok, terkunci untuk sisa transaksi."""
    stok, _ = Stok.objects.select_for_update().get_or_create(
        produk_id=produk_id, grup_bahan_id=grup_bahan_id,
        lapis=lapis, tangki_id=tangki_id,
    )
    return stok


def _catat(stok, jenis, masuk, keluar, tanggal, referensi, idem_key):
    """Tulis satu baris MutasiStok dan perbarui saldo cache."""
    saldo_baru = stok.qty + masuk - keluar
    if saldo_baru < 0:
        raise ValidationError(
            f'Stok {stok.produk.kode} tidak cukup. '
            f'Tersedia {stok.qty}, diminta {keluar}.'
        )

    stok.urutan_terakhir += 1
    mutasi = MutasiStok.objects.create(
        stok=stok, urutan=stok.urutan_terakhir, tanggal=tanggal, jenis=jenis,
        masuk=masuk, keluar=keluar, saldo_akhir=saldo_baru,
        referensi=referensi, idempotency_key=idem_key,
    )
    stok.qty = saldo_baru
    stok.save(update_fields=['qty', 'urutan_terakhir'])
    return mutasi


def _geser_tangki(tangki_id, delta, produk_id=None):
    """
    Menggeser isi tangki. Menolak kalau melebihi kapasitas, dan menolak
    mencampur dua produk berbeda -- kesalahan yang tidak bisa dibatalkan.
    """
    if not tangki_id:
        return
    t = Tangki.objects.select_for_update().get(pk=tangki_id)

    if delta > 0 and produk_id:
        if t.produk_terisi_id and t.produk_terisi_id != produk_id:
            raise ValidationError(
                f'Tangki {t.kode} berisi {t.produk_terisi.kode}. '
                f'Tidak boleh dicampur produk lain.'
            )
        t.produk_terisi_id = produk_id

    baru = t.isi_kg + delta
    if baru < 0:
        raise ValidationError(f'Isi tangki {t.kode} tidak boleh negatif.')
    if baru > t.kapasitas_kg:
        raise ValidationError(
            f'Tangki {t.kode} hanya muat {t.ruang_kosong_kg} kg lagi, '
            f'diminta {delta} kg.'
        )

    t.isi_kg = baru
    if baru == 0:
        t.produk_terisi_id = None
    t.save(update_fields=['isi_kg', 'produk_terisi'])


def _geser_pemilik(stok, entitas_id, d_qty, d_nilai):
    """Menggeser SaldoEntitas. Hanya untuk lapis RAW dan JADI."""
    if stok.lapis == Lapis.POOL:
        raise ValidationError('Lapis POOL tidak boleh punya pemilik.')

    saldo, _ = SaldoEntitas.objects.select_for_update().get_or_create(
        stok=stok, entitas_id=entitas_id,
    )
    if saldo.qty + d_qty < 0:
        raise ValidationError(
            f'Milik entitas ini hanya {saldo.qty}, tidak cukup untuk {-d_qty}.'
        )
    saldo.qty += d_qty
    saldo.nilai += d_nilai
    saldo.save(update_fields=['qty', 'nilai'])
    return saldo


def _catat_klaim(entitas_id, grup_bahan_id, jenis, produk_id, qty,
                 tanggal, referensi, idem_key, arah):
    """
    Menulis satu baris buku klaim dan memperbarui cache posisi.

    arah = +1 menambah hak (SETOR), -1 mengurangi (AMBIL).
    Tarif yang berlaku DISIMPAN di baris, sehingga perubahan tarif di
    kemudian hari tidak menulis ulang sejarah.
    """
    tarif = NilaiEkuivalen.tarif(produk_id, _tgl(tanggal))
    nilai = (Decimal(qty) * tarif).quantize(Q2, rounding=ROUND_HALF_UP) * arah

    baris = MutasiKlaim.objects.create(
        entitas_id=entitas_id, grup_bahan_id=grup_bahan_id,
        tanggal=_tgl(tanggal), jenis=jenis, produk_id=produk_id,
        qty=Decimal(qty), tarif=tarif, nilai=nilai,
        referensi=referensi, idempotency_key=idem_key,
    )

    posisi, _ = PosisiKlaim.objects.select_for_update().get_or_create(
        entitas_id=entitas_id, grup_bahan_id=grup_bahan_id,
    )
    if arah > 0:
        posisi.total_setor += abs(nilai)
    else:
        posisi.total_ambil += abs(nilai)
    posisi.nilai_bersih += nilai
    posisi.save(update_fields=['total_setor', 'total_ambil', 'nilai_bersih'])

    return baris, posisi


# =========================================================
# LAPIS 1 — RAW
# =========================================================

@transaction.atomic
def terima_raw(*, produk_id, grup_bahan_id, entitas_id, qty, nilai,
               tanggal, referensi, idem_key, tangki_id=None):
    """
    Barang masuk dari suplier. Pemiliknya jelas: entitas pada PO.

    Dipanggil warehouse.terima_barang() dalam transaksi yang sama dengan
    posting jurnal, supaya stok dan GRNI tidak pernah terpisah.

    `nilai` adalah nilai perolehan rupiah (qty x harga PO), bukan nilai
    ekuivalen. Keduanya berbeda dan tidak boleh tertukar.
    """
    ada = MutasiStok.objects.filter(idempotency_key=idem_key).first()
    if ada:
        return ada

    qty = Decimal(qty).quantize(Q3)
    nilai = Decimal(nilai).quantize(Q2)
    if qty <= 0:
        raise ValidationError('Qty terima harus lebih dari nol.')

    pastikan_periode_terbuka(entitas_id, _tgl(tanggal))

    stok = _stok(produk_id, grup_bahan_id, Lapis.RAW, tangki_id)
    _geser_tangki(tangki_id, qty, produk_id)
    mutasi = _catat(stok, JenisMutasiStok.TERIMA, qty, Decimal('0'),
                    tanggal, referensi, idem_key)
    _geser_pemilik(stok, entitas_id, qty, nilai)
    return mutasi


# =========================================================
# RAW -> POOL
# =========================================================

@transaction.atomic
def setor_ke_pool(*, produk_id, grup_bahan_id, entitas_id, qty,
                  tanggal, referensi, idem_key,
                  tangki_raw_id=None, tangki_pool_id=None):
    """
    Bahan berpindah dari kepemilikan pribadi ke pool bersama.

    Di sinilah kepemilikan berubah bentuk: fisiknya lepas, haknya tercatat
    sebagai klaim. Analogi setoran bank -- lembar uangnya bukan milik Anda
    lagi, tapi saldo Anda bertambah.

    Return: (mutasi_keluar, mutasi_masuk, baris_klaim, posisi)
    """
    ada = MutasiStok.objects.filter(idempotency_key=f'{idem_key}:out').first()
    if ada:
        return ada, None, None, None

    qty = Decimal(qty).quantize(Q3)
    if qty <= 0:
        raise ValidationError('Qty setor harus lebih dari nol.')

    pastikan_periode_terbuka(entitas_id, _tgl(tanggal))

    # Keluar dari RAW, nilai perolehan ikut keluar proporsional.
    raw = _stok(produk_id, grup_bahan_id, Lapis.RAW, tangki_raw_id)
    saldo = SaldoEntitas.objects.select_for_update().get(
        stok=raw, entitas_id=entitas_id,
    )
    if qty > saldo.qty:
        raise ValidationError(
            f'Milik {saldo.entitas.kode} hanya {saldo.qty}, diminta {qty}.'
        )
    harga = (saldo.nilai / saldo.qty) if saldo.qty else Decimal('0')
    nilai_keluar = (qty * harga).quantize(Q2, rounding=ROUND_HALF_UP)
    nilai_keluar = min(nilai_keluar, saldo.nilai)

    _geser_tangki(tangki_raw_id, -qty)
    m_out = _catat(raw, JenisMutasiStok.SETOR, Decimal('0'), qty,
                   tanggal, referensi, f'{idem_key}:out')
    _geser_pemilik(raw, entitas_id, -qty, -nilai_keluar)

    # Masuk ke POOL, tanpa pemilik.
    pool = _stok(produk_id, grup_bahan_id, Lapis.POOL, tangki_pool_id)
    _geser_tangki(tangki_pool_id, qty, produk_id)
    m_in = _catat(pool, JenisMutasiStok.SETOR, qty, Decimal('0'),
                  tanggal, referensi, f'{idem_key}:in')

    # Hak atas pool bertambah.
    baris, posisi = _catat_klaim(
        entitas_id, grup_bahan_id, JenisKlaim.SETOR, produk_id, qty,
        tanggal, referensi, f'{idem_key}:klaim', arah=+1,
    )
    return m_out, m_in, baris, posisi


# =========================================================
# LAPIS 2 — POOL (tanpa pemilik)
# =========================================================

@transaction.atomic
def pakai_dari_pool(*, produk_id, grup_bahan_id, qty, tanggal,
                    referensi, idem_key, tangki_id=None):
    """
    Bahan diambil untuk diproduksi. TIDAK ADA pemilik yang berkurang --
    pool memang milik bersama, dan penyelesaiannya lewat buku klaim.
    """
    ada = MutasiStok.objects.filter(idempotency_key=idem_key).first()
    if ada:
        return ada

    qty = Decimal(qty).quantize(Q3)
    if qty <= 0:
        raise ValidationError('Qty pakai harus lebih dari nol.')

    stok = _stok(produk_id, grup_bahan_id, Lapis.POOL, tangki_id)
    _geser_tangki(tangki_id, -qty)
    return _catat(stok, JenisMutasiStok.PAKAI, Decimal('0'), qty,
                  tanggal, referensi, idem_key)


@transaction.atomic
def hasil_ke_pool(*, produk_id, grup_bahan_id, qty, tanggal,
                  referensi, idem_key, tangki_id=None):
    """
    Produk jadi masuk ke pool, masih tanpa pemilik. Pemilik baru
    ditetapkan saat klaim_hasil().
    """
    ada = MutasiStok.objects.filter(idempotency_key=idem_key).first()
    if ada:
        return ada

    qty = Decimal(qty).quantize(Q3)
    if qty <= 0:
        raise ValidationError('Qty hasil harus lebih dari nol.')

    stok = _stok(produk_id, grup_bahan_id, Lapis.POOL, tangki_id)
    _geser_tangki(tangki_id, qty, produk_id)
    return _catat(stok, JenisMutasiStok.HASIL, qty, Decimal('0'),
                  tanggal, referensi, idem_key)


# =========================================================
# POOL -> JADI
# =========================================================

@transaction.atomic
def klaim_hasil(*, produk_id, grup_bahan_id, entitas_id, qty,
                tanggal, referensi, idem_key,
                tangki_pool_id=None, nilai_perolehan=None):
    """
    Entitas mengambil barang jadi dari pool.

    Hak atas pool berkurang. Kalau pengambilan melebihi setoran, posisi
    bersih jadi negatif -- entitas itu berhutang ke entitas lain dalam
    grup yang sama.

    `nilai_perolehan` adalah harga pokok rupiah untuk SaldoEntitas di
    lapis JADI. Kalau tidak diisi, dipakai nilai ekuivalen -- itu hanya
    layak sebagai perkiraan, bukan angka akuntansi.
    """
    ada = MutasiStok.objects.filter(idempotency_key=f'{idem_key}:out').first()
    if ada:
        return ada, None, None, None

    qty = Decimal(qty).quantize(Q3)
    if qty <= 0:
        raise ValidationError('Qty klaim harus lebih dari nol.')

    pastikan_periode_terbuka(entitas_id, _tgl(tanggal))

    pool = _stok(produk_id, grup_bahan_id, Lapis.POOL, tangki_pool_id)
    if qty > pool.qty:
        raise ValidationError(
            f'Pool hanya berisi {pool.qty} {pool.produk.kode}, diminta {qty}.'
        )

    _geser_tangki(tangki_pool_id, -qty)
    m_out = _catat(pool, JenisMutasiStok.KLAIM, Decimal('0'), qty,
                   tanggal, referensi, f'{idem_key}:out')

    jadi = _stok(produk_id, grup_bahan_id, Lapis.JADI, None)
    m_in = _catat(jadi, JenisMutasiStok.KLAIM, qty, Decimal('0'),
                  tanggal, referensi, f'{idem_key}:in')

    if nilai_perolehan is None:
        tarif = NilaiEkuivalen.tarif(produk_id, _tgl(tanggal))
        nilai_perolehan = (qty * tarif).quantize(Q2, rounding=ROUND_HALF_UP)
    _geser_pemilik(jadi, entitas_id, qty, Decimal(nilai_perolehan).quantize(Q2))

    baris, posisi = _catat_klaim(
        entitas_id, grup_bahan_id, JenisKlaim.AMBIL, produk_id, qty,
        tanggal, referensi, f'{idem_key}:klaim', arah=-1,
    )
    return m_out, m_in, baris, posisi


# =========================================================
# PENYELESAIAN ANTAR ENTITAS
# =========================================================

@transaction.atomic
def lunasi_posisi(*, grup_bahan_id, entitas_id, nilai, tanggal,
                  referensi, idem_key):
    """
    Menyelesaikan posisi negatif dengan pembayaran tunai atau setoran lain
    di luar pool.

    Contoh: PT berposisi -239, membayar tunai ke CV. Baris LUNAS +239
    mengembalikan posisi PT ke nol, dan sisi kas dicatat terpisah lewat
    akunting.posting().
    """
    ada = MutasiKlaim.objects.filter(idempotency_key=idem_key).first()
    if ada:
        return ada, None

    nilai = Decimal(nilai).quantize(Q2)
    if nilai == 0:
        raise ValidationError('Nilai pelunasan tidak boleh nol.')

    baris = MutasiKlaim.objects.create(
        entitas_id=entitas_id, grup_bahan_id=grup_bahan_id,
        tanggal=_tgl(tanggal), jenis=JenisKlaim.LUNAS,
        produk=None, qty=Decimal('0'), tarif=Decimal('0'), nilai=nilai,
        referensi=referensi, idempotency_key=idem_key,
    )
    posisi, _ = PosisiKlaim.objects.select_for_update().get_or_create(
        entitas_id=entitas_id, grup_bahan_id=grup_bahan_id,
    )
    posisi.nilai_bersih += nilai
    posisi.save(update_fields=['nilai_bersih'])
    return baris, posisi


# =========================================================
# OPNAME
# =========================================================

@transaction.atomic
def sesuaikan_stok(*, produk_id, grup_bahan_id, lapis, qty_fisik, tanggal,
                   referensi, idem_key, tangki_id=None, entitas_id=None,
                   nilai_penyesuaian=None):
    """
    Menyesuaikan catatan ke hasil hitung fisik (opname).

    Hanya boleh dipanggil role Supervisor (dicek di view) -- penyalahgunaan
    di sini sulit dideteksi karena tidak ada dokumen pembanding independen
    seperti PO atau resep produksi.

    `entitas_id` hanya relevan untuk lapis RAW/JADI (berpemilik); selisih
    dibebankan ke entitas itu dengan `nilai_penyesuaian` (default 0 --
    opname murni koreksi kuantitas, bukan revaluasi).
    """
    ada = MutasiStok.objects.filter(idempotency_key=idem_key).first()
    if ada:
        return ada

    qty_fisik = Decimal(qty_fisik).quantize(Q3)
    if qty_fisik < 0:
        raise ValidationError('Qty fisik tidak boleh negatif.')

    stok = _stok(produk_id, grup_bahan_id, lapis, tangki_id)
    delta = qty_fisik - stok.qty
    if delta == 0:
        raise ValidationError('Tidak ada selisih untuk disesuaikan.')

    if entitas_id:
        pastikan_periode_terbuka(entitas_id, _tgl(tanggal))

    _geser_tangki(tangki_id, delta, produk_id if delta > 0 else None)
    if delta > 0:
        mutasi = _catat(stok, JenisMutasiStok.OPNAME, delta, Decimal('0'),
                        tanggal, referensi, idem_key)
    else:
        mutasi = _catat(stok, JenisMutasiStok.OPNAME, Decimal('0'), -delta,
                        tanggal, referensi, idem_key)

    if stok.berpemilik and entitas_id:
        nilai = Decimal(nilai_penyesuaian or 0).quantize(Q2)
        _geser_pemilik(stok, entitas_id, delta, nilai)

    return mutasi


# =========================================================
# PEMBACAAN
# =========================================================

def posisi_grup(grup_bahan_id):
    """
    Posisi seluruh entitas dalam satu grup. Negatif = berhutang.

    Return: [{'entitas', 'setor', 'ambil', 'bersih', 'berhutang'}, ...]
    """
    return [
        {
            'entitas': p.entitas.kode,
            'setor': p.total_setor,
            'ambil': p.total_ambil,
            'bersih': p.nilai_bersih,
            'berhutang': p.nilai_bersih < 0,
        }
        for p in (PosisiKlaim.objects
                  .filter(grup_bahan_id=grup_bahan_id)
                  .select_related('entitas').order_by('entitas__kode'))
    ]


def isi_pool(grup_bahan_id, tanggal=None):
    """
    Isi pool beserta nilai ekuivalennya. Dipakai untuk memeriksa
    invariant (2) dan sebagai dasar hitung kapasitas produksi.
    """
    tanggal = tanggal or timezone.localdate()
    hasil, total = [], Decimal('0')

    for s in (Stok.objects.filter(grup_bahan_id=grup_bahan_id,
                                  lapis=Lapis.POOL, qty__gt=0)
              .select_related('produk')):
        try:
            tarif = NilaiEkuivalen.tarif(s.produk_id, tanggal)
        except ValidationError:
            tarif = Decimal('0')
        nilai = (s.qty * tarif).quantize(Q2, rounding=ROUND_HALF_UP)
        total += nilai
        hasil.append({
            'produk': s.produk.kode, 'qty': s.qty,
            'tarif': tarif, 'nilai': nilai,
        })
    return hasil, total


# =========================================================
# REKONSILIASI
# =========================================================

def verifikasi_kepemilikan(grup_bahan_id=None):
    """
    Invariant (1): SUM(SaldoEntitas.qty) == Stok.qty untuk RAW dan JADI.

    Kalau melenceng, ada mutasi yang menyentuh Stok.qty tanpa lewat modul
    ini -- dan kepemilikan sudah salah sejak saat itu.
    """
    qs = Stok.objects.filter(lapis__in=[Lapis.RAW, Lapis.JADI])
    if grup_bahan_id:
        qs = qs.filter(grup_bahan_id=grup_bahan_id)

    melenceng = []
    for stok in qs.select_related('produk', 'grup_bahan'):
        total = (SaldoEntitas.objects.filter(stok=stok)
                 .aggregate(t=Sum('qty'))['t'] or Decimal('0'))
        if total != stok.qty:
            melenceng.append({
                'stok': str(stok), 'fisik': stok.qty,
                'kepemilikan': total, 'selisih': stok.qty - total,
            })
    return melenceng


def verifikasi_pool_bersih(grup_bahan_id):
    """
    Invariant (2): SUM(PosisiKlaim.nilai_bersih) == nilai sisa POOL.

    Ini pemeriksaan terpenting. Kalau melenceng, angka siapa berhutang
    ke siapa sudah tidak bisa dipercaya.
    """
    _, nilai_pool = isi_pool(grup_bahan_id)
    total_posisi = (PosisiKlaim.objects.filter(grup_bahan_id=grup_bahan_id)
                    .aggregate(t=Sum('nilai_bersih'))['t'] or Decimal('0'))
    return {
        'nilai_pool': nilai_pool,
        'total_posisi': total_posisi,
        'selisih': nilai_pool - total_posisi,
        'cocok': nilai_pool == total_posisi,
    }


def verifikasi_posisi_cache(grup_bahan_id=None):
    """PosisiKlaim adalah cache. Bandingkan dengan MutasiKlaim asli."""
    qs = PosisiKlaim.objects.all()
    if grup_bahan_id:
        qs = qs.filter(grup_bahan_id=grup_bahan_id)

    melenceng = []
    for p in qs.select_related('entitas', 'grup_bahan'):
        asli = (MutasiKlaim.objects
                .filter(entitas=p.entitas, grup_bahan=p.grup_bahan)
                .aggregate(t=Sum('nilai'))['t'] or Decimal('0'))
        if asli != p.nilai_bersih:
            melenceng.append({
                'entitas': p.entitas.kode, 'cache': p.nilai_bersih,
                'ledger': asli, 'selisih': p.nilai_bersih - asli,
            })
    return melenceng


def verifikasi_rantai_saldo(stok_id, sejak_urutan=0):
    """
    Invariant (3): rantai saldo berjalan MutasiStok, diperiksa dengan
    window function dalam satu pass.
    """
    from django.db import connection

    with connection.cursor() as c:
        c.execute("""
            SELECT urutan, saldo_akhir, seharusnya FROM (
                SELECT urutan, saldo_akhir,
                       LAG(saldo_akhir) OVER (ORDER BY urutan) + masuk - keluar
                           AS seharusnya
                  FROM inventory_mutasi_stok
                 WHERE stok_id = %s AND urutan > %s
            ) t
            WHERE seharusnya IS NOT NULL AND saldo_akhir <> seharusnya
        """, [stok_id, sejak_urutan])
        return c.fetchall()
