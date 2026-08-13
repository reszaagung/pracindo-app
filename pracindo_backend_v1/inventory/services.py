"""
Logika bisnis persediaan — inventory/services.py

ATURAN TUNGGAL YANG MENJAGA SEMUANYA

    Nilai tidak diciptakan dan tidak dimusnahkan diam-diam.
    Setiap rupiah yang keluar dari satu baris Stok harus masuk ke baris
    Stok lain, ATAU dibebankan lewat MutasiKlaim RUGI.

Kalau aturan itu dipegang, invariant (2) benar karena konstruksi:

    terima_raw       nilai masuk ke RAW      klaim tidak berubah
    setor_ke_pool    RAW -> POOL             klaim +sebesar nilai pindah
    pakai_dari_pool  POOL -> (dipegang)      klaim tidak berubah
    hasil_ke_pool    (dipegang) -> POOL      klaim tidak berubah
    klaim_hasil      POOL -> JADI            klaim -sebesar nilai pindah
    klaim_kemasan    POOL(kg) -> JADI(pcs)   klaim -sebesar porsi tangki
    bebankan_rugi    POOL -> hilang          klaim -sebesar nilai hilang

Produksi = pakai_dari_pool berkali-kali, lalu hasil_ke_pool sebesar
rendemen, lalu bebankan_rugi sebesar sisanya. Jumlah keduanya HARUS sama
persis dengan yang keluar:

    keluar 50.000 = hasil 47.142,86 + susut 2.857,14

PEMBULATAN
    Nilai yang ikut keluar dihitung proporsional, BUKAN qty x harga.
    Dan kalau stok terkuras habis, seluruh sisa nilai ikut keluar tanpa
    dihitung ulang. Tanpa aturan kedua itu, receh pembulatan menumpuk di
    baris kosong dan invariant (2) melenceng pelan-pelan.
"""
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from core.models import GrupBahan
from core.services import pastikan_periode_terbuka

from .models import (
    JenisKlaim, JenisMutasiStok, Kemasan, Lapis, MutasiKlaim, MutasiStok,
    NilaiEkuivalen, PosisiKlaim, SaldoEntitas, Stok, Tangki,
)

Q3 = Decimal('0.001')
Q2 = Decimal('0.01')
NOL = Decimal('0')


# =========================================================
# HELPER INTERNAL
# =========================================================

def _tgl(t):
    if isinstance(t, str):
        return timezone.datetime.fromisoformat(t).date()
    return t.date() if hasattr(t, 'date') else t


def _d(v, q=Q2):
    return Decimal(str(v)).quantize(q, rounding=ROUND_HALF_UP)


def _stok(produk_id, grup_bahan_id, lapis, tangki_id=None):
    """Ambil-atau-buat baris Stok, terkunci untuk sisa transaksi."""
    stok, _ = Stok.objects.select_for_update().get_or_create(
        produk_id=produk_id, grup_bahan_id=grup_bahan_id,
        lapis=lapis, tangki_id=tangki_id,
    )
    return stok


def _porsi_nilai(stok, qty):
    """
    Nilai yang ikut keluar bersama `qty`.

    Kalau qty menguras habis stok, SELURUH sisa nilai ikut -- tidak
    dihitung proporsional. Ini yang mencegah receh tertinggal di baris
    kosong, dan alasan constraint ck_stok_kosong_tanpa_nilai ada.
    """
    if stok.qty <= 0:
        return NOL
    if qty >= stok.qty:
        return stok.nilai
    return (stok.nilai * qty / stok.qty).quantize(Q2, rounding=ROUND_HALF_UP)


def _catat(stok, jenis, masuk, keluar, tanggal, referensi, idem_key,
           nilai_masuk=NOL, nilai_keluar=NOL):
    """Tulis satu baris MutasiStok dan perbarui cache qty + nilai."""
    saldo_baru = stok.qty + masuk - keluar
    if saldo_baru < 0:
        raise ValidationError(
            f'Stok {stok.produk.kode} tidak cukup. '
            f'Tersedia {stok.qty}, diminta {keluar}.'
        )

    nilai_baru = stok.nilai + nilai_masuk - nilai_keluar
    if nilai_baru < 0:
        # Hanya mungkin kalau ada bug pembulatan. Lebih baik berhenti di
        # sini daripada menyimpan nilai negatif yang tidak berarti apa pun.
        raise ValidationError(
            f'Nilai stok {stok.produk.kode} jadi negatif '
            f'({stok.nilai} - {nilai_keluar}). Transaksi dibatalkan.'
        )
    if saldo_baru == 0 and nilai_baru != 0:
        # PRD §23: seluruh sisa nilai harus ikut KELUAR pada transaksi yang
        # menghabiskan stok. Itu tugas pemanggil lewat _porsi_nilai(),
        # bukan tugas _catat() untuk membakarnya diam-diam. Dulu baris ini
        # berbunyi `nilai_baru = NOL`, dan verifikasi_rantai_saldo() justru
        # mengecualikan baris ber-qty nol -- jadi satu-satunya tempat nilai
        # bisa lenyap adalah tempat yang tidak diperiksa.
        raise ValidationError(
            f'Stok {stok.produk.kode} habis tapi masih menyisakan '
            f'{nilai_baru}. Nilai sisa harus ikut keluar di transaksi ini. '
            f'Periksa perhitungan nilai_keluar di pemanggil.'
        )

    stok.urutan_terakhir += 1
    mutasi = MutasiStok.objects.create(
        stok=stok, urutan=stok.urutan_terakhir, tanggal=tanggal, jenis=jenis,
        masuk=masuk, keluar=keluar, saldo_akhir=saldo_baru,
        nilai_masuk=nilai_masuk, nilai_keluar=nilai_keluar,
        saldo_nilai=nilai_baru,
        referensi=referensi, idempotency_key=idem_key,
    )
    stok.qty = saldo_baru
    stok.nilai = nilai_baru
    stok.save(update_fields=['qty', 'nilai', 'urutan_terakhir'])
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
    if saldo.qty == 0:
        # Habis wajib bernilai nol. Ini yang dijaga constraint
        # ck_saldo_kosong_tanpa_nilai, bukan penutup kesalahan.
        saldo.nilai = NOL
    elif saldo.nilai < 0:
        # Nilai negatif dengan qty positif TIDAK PERNAH punya arti. Kalau
        # muncul, ada bug pembulatan di pemanggil. Membungkamnya jadi nol
        # membuat Stok.nilai dan SaldoEntitas.nilai berpisah diam-diam,
        # dan invariant (1b) melenceng tanpa jejak asalnya.
        raise ValidationError(
            f'Nilai kepemilikan entitas {saldo.entitas_id} atas '
            f'{stok.produk.kode} jadi negatif ({saldo.nilai}) padahal '
            f'qty {saldo.qty}. Transaksi dibatalkan.'
        )
    saldo.save(update_fields=['qty', 'nilai'])
    return saldo


def _periode_grup(grup_bahan_id, tanggal):
    """
    pakai_dari_pool dan hasil_ke_pool tidak punya entitas, tapi tetap
    tidak boleh menembus periode yang sudah ditutup. Diperiksa untuk
    seluruh entitas dalam grup.
    """
    grup = GrupBahan.objects.get(pk=grup_bahan_id)
    for e in grup.entitas.all():
        pastikan_periode_terbuka(e.id, _tgl(tanggal))


def _catat_klaim(entitas_id, grup_bahan_id, jenis, produk_id, qty, tarif,
                 nilai, tanggal, referensi, idem_key):
    """
    Menulis satu baris buku klaim dan memperbarui cache posisi.

    `nilai` sudah bertanda: positif menambah hak, negatif mengurangi.
    Tarif dan nilai DITENTUKAN PEMANGGIL, karena hanya pemanggil yang
    tahu berapa rupiah yang benar-benar berpindah di sisi stok. Menghitung
    ulang di sini akan membuat kedua sisi selisih satu-dua receh.
    """
    baris = MutasiKlaim.objects.create(
        entitas_id=entitas_id, grup_bahan_id=grup_bahan_id,
        tanggal=_tgl(tanggal), jenis=jenis, produk_id=produk_id,
        qty=Decimal(qty), tarif=tarif, nilai=nilai,
        referensi=referensi, idempotency_key=idem_key,
    )

    posisi, _ = PosisiKlaim.objects.select_for_update().get_or_create(
        entitas_id=entitas_id, grup_bahan_id=grup_bahan_id,
    )
    if jenis == JenisKlaim.SETOR:
        posisi.total_setor += abs(nilai)
    elif jenis == JenisKlaim.AMBIL:
        posisi.total_ambil += abs(nilai)
    elif jenis == JenisKlaim.RUGI:
        posisi.total_rugi += abs(nilai)
    posisi.nilai_bersih += nilai
    posisi.save(update_fields=['total_setor', 'total_ambil', 'total_rugi',
                               'nilai_bersih'])
    return baris, posisi


def alokasi_prorata(bobot, total):
    """
    Membagi `total` sebanding `bobot` ({id: Decimal}), dengan sisa
    pembulatan diberikan ke bobot terbesar supaya jumlahnya PERSIS total.

    Kalau tidak dibulatkan begini, kerugian Rp10.000 dibagi tiga entitas
    menghasilkan Rp9.999,99 dan invariant (2) langsung melenceng.

    PUBLIK. produksi.pratinjau_kerugian() wajib memakai fungsi yang sama
    persis, termasuk cara residual dialokasikan -- kalau tidak, angka
    pratinjau meleset satu-dua sen dari yang benar-benar terbit, dan
    operator kehilangan kepercayaan pada layarnya sendiri.
    """
    jumlah_bobot = sum(bobot.values())
    if jumlah_bobot <= 0 or total == 0:
        return {}

    hasil, terpakai = {}, NOL
    # Urutan kedua (kv[0]) membuat hasil deterministik saat ada bobot kembar.
    urut = sorted(bobot.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    for k, b in urut[1:]:
        bagian = (total * b / jumlah_bobot).quantize(Q2, rounding=ROUND_HALF_UP)
        hasil[k] = bagian
        terpakai += bagian
    hasil[urut[0][0]] = total - terpakai
    return hasil


# Nama lama dipertahankan supaya pemanggil internal tidak perlu diubah.
_alokasi_prorata = alokasi_prorata


# =========================================================
# PEMBEBANAN NILAI YANG MUSNAH
# =========================================================

@transaction.atomic
def bebankan_rugi(*, grup_bahan_id, nilai, tanggal, referensi, idem_key):
    """
    Nilai hilang dari pool tanpa produk pengganti. Dibagi pro-rata ke
    pemegang hak POSITIF dalam grup, sebanding besar haknya.

    Dipanggil saat sesi produksi GAGAL, sesi R&D yang hasilnya tidak masuk
    pool, dan opname kurang di lapis POOL. Tanpa ini, pool berkurang
    sementara total klaim tetap, dan angka siapa berhutang ke siapa
    langsung salah.

    Entitas berposisi negatif TIDAK ikut menanggung: dia sudah mengambil
    lebih dari haknya, menambah beban justru menghukum yang sudah
    menyetor.
    """
    # Penjaga memakai PREFIKS, bukan ':0'. Indeks 0 bisa tidak pernah
    # ditulis kalau bagian pertama membulat ke nol, dan penjaga lama
    # meloloskan pemanggilan kedua -- pembebanan ganda tanpa suara.
    if MutasiKlaim.objects.filter(
            idempotency_key__startswith=f'{idem_key}:').exists():
        return []

    nilai = _d(nilai)
    if nilai <= 0:
        return []

    posisi = list(PosisiKlaim.objects.select_for_update()
                  .filter(grup_bahan_id=grup_bahan_id, nilai_bersih__gt=0)
                  .select_related('entitas'))
    if not posisi:
        # Kondisi ini secara matematis TIDAK MUNGKIN kalau invariant (2)
        # utuh: pakai_dari_pool() tidak menyentuh klaim, jadi nilai bahan
        # yang sedang dipegang produksi masih tercatat sebagai hak
        # seseorang. Kalau sampai ke sini, pembukuan sudah rusak sebelum
        # transaksi ini dimulai -- menerima pembebanan berarti menulis di
        # atas kerusakan.
        raise ValidationError(
            f'Tidak ada pemegang hak positif di grup ini, kerugian {nilai} '
            f'tidak bisa dibebankan. Kondisi ini hanya mungkin kalau '
            f'invariant (2) sudah melenceng. Jalankan '
            f'/inventory/verifikasi/?grup={grup_bahan_id} sebelum '
            f'melanjutkan.'
        )

    bobot = {p.entitas_id: p.nilai_bersih for p in posisi}
    bagian = alokasi_prorata(bobot, nilai)

    baris = []
    # Kunci memakai entitas_id, bukan indeks enumerate(). Urutan dict yang
    # dikembalikan alokasi_prorata() menaruh bobot terbesar di AKHIR, jadi
    # indeks 0 dulu menunjuk pemegang hak terbesar kedua -- dan berpindah
    # entitas begitu komposisi grup berubah.
    for entitas_id, jml in sorted(bagian.items()):
        if jml == 0:
            continue
        b, _ = _catat_klaim(
            entitas_id, grup_bahan_id, JenisKlaim.RUGI, None,
            NOL, NOL, -jml, tanggal, referensi, f'{idem_key}:e{entitas_id}',
        )
        baris.append(b)
    return baris


# =========================================================
# LAPIS 1 — RAW
# =========================================================

@transaction.atomic
def terima_raw(*, produk_id, grup_bahan_id, entitas_id, qty, nilai,
               tanggal, referensi, idem_key, tangki_id=None):
    """
    Barang masuk dari suplier. Pemiliknya jelas: entitas pada PO.

    `nilai` adalah nilai perolehan rupiah (qty x harga PO). Inilah biaya
    yang akan mengalir terus sampai barang jadi -- tidak ada tarif sintetis
    di jalur ini.
    """
    ada = MutasiStok.objects.filter(idempotency_key=idem_key).first()
    if ada:
        return ada

    qty = Decimal(qty).quantize(Q3)
    nilai = _d(nilai)
    if qty <= 0:
        raise ValidationError('Qty terima harus lebih dari nol.')
    if nilai < 0:
        raise ValidationError('Nilai perolehan tidak boleh negatif.')

    pastikan_periode_terbuka(entitas_id, _tgl(tanggal))

    stok = _stok(produk_id, grup_bahan_id, Lapis.RAW, tangki_id)
    _geser_tangki(tangki_id, qty, produk_id)
    mutasi = _catat(stok, JenisMutasiStok.TERIMA, qty, NOL,
                    tanggal, referensi, idem_key, nilai_masuk=nilai)
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

    Nilai yang ikut pindah = porsi nilai perolehan milik entitas itu.
    Klaim yang terbit persis sebesar nilai yang pindah, sehingga invariant
    (2) tidak pernah bergeser.

    Return: (mutasi_keluar, mutasi_masuk, baris_klaim, posisi)
    """
    ada = MutasiStok.objects.filter(idempotency_key=f'{idem_key}:out').first()
    if ada:
        return ada, None, None, None

    qty = Decimal(qty).quantize(Q3)
    if qty <= 0:
        raise ValidationError('Qty setor harus lebih dari nol.')

    pastikan_periode_terbuka(entitas_id, _tgl(tanggal))

    raw = _stok(produk_id, grup_bahan_id, Lapis.RAW, tangki_raw_id)
    try:
        saldo = SaldoEntitas.objects.select_for_update().get(
            stok=raw, entitas_id=entitas_id,
        )
    except SaldoEntitas.DoesNotExist:
        raise ValidationError(
            f'Entitas ini belum punya stok RAW {raw.produk.kode} '
            f'di grup {raw.grup_bahan.kode}.'
        )
    if qty > saldo.qty:
        raise ValidationError(
            f'Milik {saldo.entitas.kode} hanya {saldo.qty}, diminta {qty}.'
        )

    # --- SISI RAW: biaya perolehan keluar, proporsional ---
    # Ini rupiah yang benar-benar dibayar ke suplier. Angkanya diteruskan
    # ke akunting sebagai biaya bahan, dan TIDAK dipakai menghitung hak.
    if qty >= saldo.qty:
        biaya_keluar = saldo.nilai
    else:
        biaya_keluar = (saldo.nilai * qty / saldo.qty).quantize(
            Q2, rounding=ROUND_HALF_UP)

    # =====================================================================
    # SISI POOL — OPSI A: NILAI RIIL. Lihat PATCH §P8 sebelum mengubah.
    # =====================================================================
    # Nilai yang masuk POOL = nilai yang keluar dari RAW. Persis, tanpa
    # perantara. Inilah "nilai riil inventory" PRD §25.
    #
    # Dulu sisi ini diisi `qty x NilaiEkuivalen.tarif` sementara sisi RAW
    # dikurangi `biaya_keluar`. Kedua angka itu berbeda dan selisihnya
    # tidak punya baris jurnal apa pun -- rupiah muncul atau lenyap di
    # batas lapis. Invariant (2) tetap lulus karena kedua sisi klaim
    # memakai angka sintetis yang sama, dan itu justru yang berbahaya:
    # verifikator melaporkan "cocok" sementara nilai bocor di tempat yang
    # tidak diperiksa.
    #
    # KONSEKUENSI: dua entitas yang menyetor 10 kg gula identik dengan
    # harga beli berbeda kini mendapat hak yang BERBEDA. Kalau grup Anda
    # bekerja atas dasar "siapa menyetor berapa kilo" dan bukan "berapa
    # rupiah", ini salah -- pakai Opsi C di dokumen PATCH, jangan
    # mengembalikan kode lama.
    nilai_pindah = biaya_keluar
    if nilai_pindah <= 0:
        # Tidak ada dasar biaya sama sekali (mis. RAW diterima bernilai
        # nol). Di sinilah NilaiEkuivalen berperan sebagai BENIH, persis
        # seperti yang dijanjikan docstring modelnya. wajib=False supaya
        # barang tetap bisa masuk pool walau tarifnya belum ditetapkan:
        # qty bertambah tanpa nilai tetap menjaga invariant (2).
        nilai_pindah = (
            qty * NilaiEkuivalen.tarif(produk_id, _tgl(tanggal), wajib=False)
        ).quantize(Q2, rounding=ROUND_HALF_UP)

    tarif = (nilai_pindah / qty).quantize(Q2) if qty else NOL

    _geser_tangki(tangki_raw_id, -qty)
    m_out = _catat(raw, JenisMutasiStok.SETOR, NOL, qty,
                   tanggal, referensi, f'{idem_key}:out',
                   nilai_keluar=biaya_keluar)
    _geser_pemilik(raw, entitas_id, -qty, -biaya_keluar)

    pool = _stok(produk_id, grup_bahan_id, Lapis.POOL, tangki_pool_id)
    _geser_tangki(tangki_pool_id, qty, produk_id)
    m_in = _catat(pool, JenisMutasiStok.SETOR, qty, NOL,
                  tanggal, referensi, f'{idem_key}:in',
                  nilai_masuk=nilai_pindah)

    baris, posisi = _catat_klaim(
        entitas_id, grup_bahan_id, JenisKlaim.SETOR, produk_id, qty,
        tarif, nilai_pindah, tanggal, referensi, f'{idem_key}:klaim',
    )
    return m_out, m_in, baris, posisi


# =========================================================
# LAPIS 2 — POOL (tanpa pemilik)
# =========================================================

@transaction.atomic
def pakai_dari_pool(*, produk_id, grup_bahan_id, qty, tanggal,
                    referensi, idem_key, tangki_id=None):
    """
    Bahan diambil untuk diproduksi. Klaim TIDAK berubah -- nilai belum
    hilang, hanya berpindah ke tangan proses produksi.

    Return: (mutasi, nilai_yang_ikut_keluar)

    Pemanggil WAJIB mengembalikan nilai itu ke pool lewat hasil_ke_pool()
    atau membebankannya lewat bebankan_rugi(). Kalau tidak, invariant (2)
    melenceng dan tidak ada yang memberi tahu.
    """
    ada = MutasiStok.objects.filter(idempotency_key=idem_key).first()
    if ada:
        return ada, ada.nilai_keluar

    qty = Decimal(qty).quantize(Q3)
    if qty <= 0:
        raise ValidationError('Qty pakai harus lebih dari nol.')

    _periode_grup(grup_bahan_id, tanggal)

    stok = _stok(produk_id, grup_bahan_id, Lapis.POOL, tangki_id)
    if qty > stok.qty:
        lokasi = f' di tangki {stok.tangki.kode}' if stok.tangki_id else ''
        raise ValidationError(
            f'Pool hanya berisi {stok.qty} {stok.produk.kode}{lokasi}, '
            f'diminta {qty}.'
        )

    nilai_keluar = _porsi_nilai(stok, qty)
    _geser_tangki(tangki_id, -qty)
    mutasi = _catat(stok, JenisMutasiStok.PAKAI, NOL, qty,
                    tanggal, referensi, idem_key, nilai_keluar=nilai_keluar)
    return mutasi, nilai_keluar


@transaction.atomic
def hasil_ke_pool(*, produk_id, grup_bahan_id, qty, nilai_masuk, tanggal,
                  referensi, idem_key, tangki_id=None):
    """
    Produk jadi masuk pool membawa nilai yang dihitung PEMANGGIL.

    Untuk produksi, itu nilai sebanding rendemen -- bukan seluruh nilai
    bahan. Sisanya dibebankan terpisah lewat bebankan_rugi(), sehingga
    harga per satuan tidak terkerek naik oleh susut.

    `nilai_masuk` wajib diisi. Tidak ada nilai default, karena menebak di
    sini berarti menciptakan rupiah dari udara.
    """
    ada = MutasiStok.objects.filter(idempotency_key=idem_key).first()
    if ada:
        return ada

    qty = Decimal(qty).quantize(Q3)
    nilai_masuk = _d(nilai_masuk)
    if qty <= 0:
        raise ValidationError('Qty hasil harus lebih dari nol.')
    if nilai_masuk < 0:
        raise ValidationError('Nilai hasil tidak boleh negatif.')

    _periode_grup(grup_bahan_id, tanggal)

    stok = _stok(produk_id, grup_bahan_id, Lapis.POOL, tangki_id)
    _geser_tangki(tangki_id, qty, produk_id)
    return _catat(stok, JenisMutasiStok.HASIL, qty, NOL,
                  tanggal, referensi, idem_key, nilai_masuk=nilai_masuk)


# =========================================================
# POOL -> JADI  (packaging / pengambilan hak)
# =========================================================

@transaction.atomic
def klaim_hasil(*, produk_id, grup_bahan_id, entitas_id, qty,
                tanggal, referensi, idem_key, tangki_pool_id=None):
    """
    Entitas mengambil barang jadi dari pool.

    TARIF KLAIM = HARGA RATA ISI TANGKI SAAT ITU. Bukan tarif tetap,
    bukan harga PO bahan aslinya. Tangki berisi 33 kg senilai Rp47.142,86
    (35 kg / Rp50.000 masuk, 2 kg susut sudah dibebankan): mengambil 10 kg
    mengurangi hak sebesar 47.142,86 x 10/33 = Rp14.285,72.

    Angka Rp15.151,52 yang dulu tertulis di sini adalah harga ABSORPSI --
    seluruh nilai bahan dipaksa menempel di 33 kg yang selamat. Itu persis
    yang ditolak seluruh modul ini.

    Kalau pengambilan melebihi setoran, posisi bersih jadi negatif --
    entitas itu berhutang ke entitas lain dalam grup yang sama.
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

    nilai_ambil = _porsi_nilai(pool, qty)
    tarif = (nilai_ambil / qty).quantize(Q2) if qty else NOL

    _geser_tangki(tangki_pool_id, -qty)
    m_out = _catat(pool, JenisMutasiStok.KLAIM, NOL, qty,
                   tanggal, referensi, f'{idem_key}:out',
                   nilai_keluar=nilai_ambil)

    jadi = _stok(produk_id, grup_bahan_id, Lapis.JADI, None)
    m_in = _catat(jadi, JenisMutasiStok.KLAIM, qty, NOL,
                  tanggal, referensi, f'{idem_key}:in',
                  nilai_masuk=nilai_ambil)
    _geser_pemilik(jadi, entitas_id, qty, nilai_ambil)

    baris, posisi = _catat_klaim(
        entitas_id, grup_bahan_id, JenisKlaim.AMBIL, produk_id, qty,
        tarif, -nilai_ambil, tanggal, referensi, f'{idem_key}:klaim',
    )
    return m_out, m_in, baris, posisi


@transaction.atomic
def klaim_kemasan(*, kemasan_id, grup_bahan_id, entitas_id, jumlah,
                  tanggal, referensi, idem_key, tangki_pool_id=None,
                  qty_curah_aktual=None):
    """
    Pengepakan: curah keluar dari tangki dalam kg, barang jadi masuk
    dalam pcs.

        Tangki Monitor Blue   50 kg  senilai 50.000
        PT minta 10 pcs @ 1 kg  ->  10 kg keluar
        Hak PT berkurang 50.000 x 10/35... (proporsi isi tangki saat itu)

    KENAPA PROPORSI, BUKAN qty x TARIF
        Tarif hanya angka tampilan. Isi tangki 35 kg senilai 50.000
        berarti Rp1.428,57/kg -- angka yang tidak pernah bulat. Mengalikan
        10 kg dengan tarif yang sudah dibulatkan ke Rp1,5/gram menghasilkan
        15.000, padahal porsi sebenarnya 14.285,71. Selisih Rp714 itu
        muncul dari udara dan menambah hak PT tanpa ada barang di
        belakangnya.

    `qty_curah_aktual` dipakai kalau timbangan menunjukkan curah yang
    keluar berbeda dari jumlah x isi -- susut pengepakan, tetesan di
    selang, sisa di corong. Nilainya ikut curah yang benar-benar keluar,
    jadi susut itu ditanggung yang mengepak. Itu benar: dia yang memilih
    kapan dan bagaimana mengepak.
    """
    ada = MutasiStok.objects.filter(idempotency_key=f'{idem_key}:out').first()
    if ada:
        return ada, None, None, None

    kemasan = (Kemasan.objects
               .select_related('produk_curah', 'produk_kemasan')
               .get(pk=kemasan_id))
    if not kemasan.aktif:
        raise ValidationError(f'Kemasan {kemasan} sudah tidak aktif.')

    jumlah = Decimal(jumlah).quantize(Q3)
    if jumlah <= 0:
        raise ValidationError('Jumlah kemasan harus lebih dari nol.')

    qty_curah = (Decimal(qty_curah_aktual).quantize(Q3)
                 if qty_curah_aktual is not None
                 else kemasan.curah_untuk(jumlah))
    if qty_curah <= 0:
        raise ValidationError('Curah yang keluar harus lebih dari nol.')

    pastikan_periode_terbuka(entitas_id, _tgl(tanggal))

    pool = _stok(kemasan.produk_curah_id, grup_bahan_id, Lapis.POOL,
                 tangki_pool_id)
    if qty_curah > pool.qty:
        raise ValidationError(
            f'Tangki hanya berisi {pool.qty} {pool.produk.kode}, '
            f'{jumlah} kemasan butuh {qty_curah}.'
        )

    nilai = _porsi_nilai(pool, qty_curah)

    # Curah keluar (kg)
    _geser_tangki(tangki_pool_id, -qty_curah)
    m_out = _catat(pool, JenisMutasiStok.KLAIM, NOL, qty_curah,
                   tanggal, referensi, f'{idem_key}:out', nilai_keluar=nilai)

    # Kemasan masuk (pcs) -- satuan berubah, nilai tidak
    jadi = _stok(kemasan.produk_kemasan_id, grup_bahan_id, Lapis.JADI, None)
    m_in = _catat(jadi, JenisMutasiStok.KLAIM, jumlah, NOL,
                  tanggal, referensi, f'{idem_key}:in', nilai_masuk=nilai)
    _geser_pemilik(jadi, entitas_id, jumlah, nilai)

    tarif_per_kemasan = (nilai / jumlah).quantize(Q2) if jumlah else NOL
    baris, posisi = _catat_klaim(
        entitas_id, grup_bahan_id, JenisKlaim.AMBIL,
        kemasan.produk_kemasan_id, jumlah, tarif_per_kemasan, -nilai,
        tanggal, referensi, f'{idem_key}:klaim',
    )
    return m_out, m_in, baris, posisi


def rencana_kemasan(kemasan_id, grup_bahan_id, jumlah, tangki_pool_id=None):
    """
    Pratinjau sebelum tombol ditekan: berapa curah yang keluar, berapa
    hak yang berkurang, dan cukup atau tidak.

    Dipakai layar pengepakan supaya operator melihat angkanya dulu.
    Tidak menulis apa pun.
    """
    kemasan = (Kemasan.objects
               .select_related('produk_curah', 'produk_kemasan')
               .get(pk=kemasan_id))
    qty_curah = kemasan.curah_untuk(jumlah)

    pool = (Stok.objects
            .filter(produk_id=kemasan.produk_curah_id,
                    grup_bahan_id=grup_bahan_id, lapis=Lapis.POOL,
                    tangki_id=tangki_pool_id)
            .select_related('tangki').first())
    if not pool or pool.qty <= 0:
        return {
            'cukup': False, 'qty_curah': qty_curah, 'tersedia': NOL,
            'nilai': NOL, 'pesan': 'Tangki kosong.',
        }

    nilai = _porsi_nilai(pool, min(qty_curah, pool.qty))
    return {
        'kemasan': str(kemasan),
        'produk_curah': pool.produk.kode,
        'produk_kemasan': kemasan.produk_kemasan.kode,
        'tangki': pool.tangki.kode if pool.tangki_id else None,
        'jumlah': Decimal(jumlah),
        'isi_per_kemasan': kemasan.isi,
        'qty_curah': qty_curah,
        'tersedia': pool.qty,
        'cukup': qty_curah <= pool.qty,
        'nilai': nilai,
        'tarif_tampilan': pool.harga_rata,
        'maksimum_kemasan': (pool.qty / kemasan.isi).quantize(
            Q3, rounding=ROUND_DOWN),
    }


# =========================================================
# SELISIH PEMBULATAN
# =========================================================

@transaction.atomic
def luruskan_pembulatan(*, grup_bahan_id, tanggal, referensi, idem_key,
                        batas=Decimal('1.00')):
    """
    Menutup selisih kecil antara isi pool dan total klaim dengan baris
    KOREKSI bertanggal.

    Selisih sekecil apa pun tetap DICATAT, tidak dibulatkan diam-diam.
    Bedanya besar: selisih yang punya baris jurnal bisa dilacak dan
    dijumlahkan; selisih yang hanya "dimaafkan" akan menumpuk sampai
    tidak ada yang tahu asalnya.

    `batas` adalah pagar pengaman. Selisih di atas batas BUKAN pembulatan
    -- itu bug, dan menutupnya dengan koreksi otomatis justru menghapus
    jejak yang dibutuhkan untuk menemukannya.
    """
    hasil = verifikasi_pool_bersih(grup_bahan_id)
    selisih = hasil['selisih']
    if selisih == 0:
        return None

    if abs(selisih) > batas:
        raise ValidationError(
            f'Selisih {selisih} melampaui batas pembulatan {batas}. '
            f'Ini bukan pembulatan. Periksa mutasi terakhir sebelum '
            f'menutupnya.'
        )

    if MutasiKlaim.objects.filter(idempotency_key=f'{idem_key}:0').exists():
        return None

    # Dibebankan ke pemegang hak terbesar: dia yang paling terpengaruh
    # kalau selisih dibiarkan, dan porsinya paling tidak terasa.
    posisi = (PosisiKlaim.objects.select_for_update()
              .filter(grup_bahan_id=grup_bahan_id)
              .order_by('-nilai_bersih').first())
    if not posisi:
        raise ValidationError('Belum ada posisi klaim di grup ini.')

    baris, _ = _catat_klaim(
        posisi.entitas_id, grup_bahan_id, JenisKlaim.KOREKSI, None,
        NOL, NOL, selisih, tanggal,
        referensi or 'Selisih pembulatan', f'{idem_key}:0',
    )
    return baris


# =========================================================
# PENYELESAIAN ANTAR ENTITAS
# =========================================================

def lunasi_posisi(*, grup_bahan_id, entitas_id, nilai, tanggal,
                  referensi, idem_key):
    """
    Menyelesaikan posisi negatif dengan pembayaran tunai di luar pool.

    PERHATIAN: baris LUNAS memindahkan hak ANTAR entitas, jadi harus
    berpasangan supaya jumlahnya nol. Membayar Rp239 berarti +239 untuk
    yang membayar dan -239 untuk yang menerima. Kalau hanya satu sisi
    yang dicatat, total klaim bergeser sementara pool diam, dan invariant
    (2) melenceng.
    """
    raise ValidationError(
        'Pakai lunasi_antar_entitas(). Pelunasan satu sisi merusak '
        'invariant (2).'
    )


@transaction.atomic
def lunasi_antar_entitas(*, grup_bahan_id, entitas_bayar_id,
                         entitas_terima_id, nilai, tanggal, referensi,
                         idem_key):
    """
    Pemindahan hak dari yang membayar ke yang menerima uang.

    Yang membayar tunai posisinya naik (hutangnya berkurang), yang
    menerima uang posisinya turun (piutangnya dicairkan). Jumlah kedua
    baris nol, jadi total klaim grup tidak berubah -- sesuai kenyataan:
    isi pool memang tidak tersentuh oleh pembayaran tunai.
    """
    if MutasiKlaim.objects.filter(idempotency_key=f'{idem_key}:bayar').exists():
        return None, None

    nilai = _d(nilai)
    if nilai <= 0:
        raise ValidationError('Nilai pelunasan harus lebih dari nol.')
    if entitas_bayar_id == entitas_terima_id:
        raise ValidationError('Entitas pembayar dan penerima harus berbeda.')

    pastikan_periode_terbuka(entitas_bayar_id, _tgl(tanggal))
    pastikan_periode_terbuka(entitas_terima_id, _tgl(tanggal))

    b1, _ = _catat_klaim(entitas_bayar_id, grup_bahan_id, JenisKlaim.LUNAS,
                         None, NOL, NOL, nilai, tanggal, referensi,
                         f'{idem_key}:bayar')
    b2, _ = _catat_klaim(entitas_terima_id, grup_bahan_id, JenisKlaim.LUNAS,
                         None, NOL, NOL, -nilai, tanggal, referensi,
                         f'{idem_key}:terima')
    return b1, b2


# =========================================================
# OPNAME
# =========================================================

@transaction.atomic
def sesuaikan_stok(*, produk_id, grup_bahan_id, lapis, qty_fisik, tanggal,
                   referensi, idem_key, tangki_id=None, entitas_id=None,
                   nilai_penyesuaian=None):
    """
    Menyesuaikan catatan ke hasil hitung fisik. Supervisor saja.

    LAPIS POOL
        Kurang -> nilai proporsional ikut hilang, dan langsung dibebankan
                  lewat bebankan_rugi(). Ini penting: opname kurang di
                  pool adalah kerugian nyata milik bersama.
        Lebih  -> qty bertambah dengan nilai 0 (atau nilai_penyesuaian
                  kalau memang ada dasarnya). Menambah qty tanpa nilai
                  menurunkan harga per kg dan tetap menjaga invariant (2).

    LAPIS RAW/JADI
        Selisih dibebankan ke `entitas_id` dengan `nilai_penyesuaian`.
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
    else:
        _periode_grup(grup_bahan_id, tanggal)

    if stok.berpemilik and not entitas_id:
        raise ValidationError(
            f'Opname lapis {lapis} wajib menyebut entitas pemilik selisih.'
        )

    if delta > 0:
        nilai_masuk = _d(nilai_penyesuaian or 0)
        _geser_tangki(tangki_id, delta, produk_id)
        mutasi = _catat(stok, JenisMutasiStok.OPNAME, delta, NOL,
                        tanggal, referensi, idem_key, nilai_masuk=nilai_masuk)
        if stok.berpemilik:
            _geser_pemilik(stok, entitas_id, delta, nilai_masuk)
    else:
        nilai_keluar = _porsi_nilai(stok, -delta)
        _geser_tangki(tangki_id, delta)
        mutasi = _catat(stok, JenisMutasiStok.OPNAME, NOL, -delta,
                        tanggal, referensi, idem_key, nilai_keluar=nilai_keluar)
        if stok.berpemilik:
            _geser_pemilik(stok, entitas_id, delta, -nilai_keluar)
        elif nilai_keluar > 0:
            bebankan_rugi(
                grup_bahan_id=grup_bahan_id, nilai=nilai_keluar,
                tanggal=tanggal, referensi=referensi,
                idem_key=f'{idem_key}:rugi',
            )

    return mutasi


# =========================================================
# PEMBACAAN
# =========================================================

def posisi_grup(grup_bahan_id):
    """Posisi seluruh entitas dalam satu grup. Negatif = berhutang."""
    return [
        {
            'entitas': p.entitas.kode,
            'entitas_id': p.entitas_id,
            'setor': p.total_setor,
            'ambil': p.total_ambil,
            'rugi': p.total_rugi,
            'bersih': p.nilai_bersih,
            'berhutang': p.nilai_bersih < 0,
        }
        for p in (PosisiKlaim.objects
                  .filter(grup_bahan_id=grup_bahan_id)
                  .select_related('entitas').order_by('entitas__kode'))
    ]


def isi_pool(grup_bahan_id, tanggal=None):
    """
    Isi pool beserta nilai riil yang melekat. Tidak ada tarif sintetis di
    sini -- angkanya dibaca langsung dari Stok.nilai.
    """
    hasil, total = [], NOL
    for s in (Stok.objects.filter(grup_bahan_id=grup_bahan_id,
                                  lapis=Lapis.POOL, qty__gt=0)
              .select_related('produk', 'tangki').order_by('produk__kode')):
        total += s.nilai
        hasil.append({
            'produk': s.produk.kode,
            'produk_id': s.produk_id,
            'tangki': s.tangki.kode if s.tangki_id else None,
            'qty': s.qty,
            'nilai': s.nilai,
            'harga_rata': s.harga_rata,
        })
    return hasil, total


def isi_tangki(tangki_id):
    """Nominal yang tersimpan di satu tangki. Dasar tarif klaim."""
    s = (Stok.objects.filter(tangki_id=tangki_id, lapis=Lapis.POOL, qty__gt=0)
         .select_related('produk').first())
    if not s:
        return {'produk': None, 'qty': NOL, 'nilai': NOL, 'harga_rata': NOL}
    return {
        'produk': s.produk.kode, 'produk_id': s.produk_id,
        'qty': s.qty, 'nilai': s.nilai, 'harga_rata': s.harga_rata,
    }


# =========================================================
# REKONSILIASI
# =========================================================

def verifikasi_kepemilikan(grup_bahan_id=None):
    """Invariant (1a) dan (1b): qty DAN nilai kepemilikan == baris Stok."""
    qs = Stok.objects.filter(lapis__in=[Lapis.RAW, Lapis.JADI])
    if grup_bahan_id:
        qs = qs.filter(grup_bahan_id=grup_bahan_id)

    melenceng = []
    for stok in qs.select_related('produk', 'grup_bahan'):
        agg = (SaldoEntitas.objects.filter(stok=stok)
               .aggregate(q=Sum('qty'), n=Sum('nilai')))
        tot_q = agg['q'] or NOL
        tot_n = agg['n'] or NOL
        if tot_q != stok.qty or tot_n != stok.nilai:
            melenceng.append({
                'stok': str(stok),
                'qty_fisik': stok.qty, 'qty_kepemilikan': tot_q,
                'selisih_qty': stok.qty - tot_q,
                'nilai_fisik': stok.nilai, 'nilai_kepemilikan': tot_n,
                'selisih_nilai': stok.nilai - tot_n,
            })
    return melenceng


def verifikasi_pool_bersih(grup_bahan_id, toleransi=Decimal('0')):
    """
    Invariant (2): SUM(PosisiKlaim.nilai_bersih) == SUM(Stok.nilai) POOL.

    Sekarang ini harus COCOK PERSIS, bukan kira-kira. Setiap rupiah yang
    keluar dari pool sudah punya pasangan: masuk ke stok lain, atau
    terbit sebagai baris RUGI. Selisih sekecil apa pun berarti ada jalur
    yang menyentuh Stok.nilai tanpa lewat services ini.
    """
    total_pool = (Stok.objects
                  .filter(grup_bahan_id=grup_bahan_id, lapis=Lapis.POOL)
                  .aggregate(t=Sum('nilai'))['t'] or NOL)
    total_posisi = (PosisiKlaim.objects.filter(grup_bahan_id=grup_bahan_id)
                    .aggregate(t=Sum('nilai_bersih'))['t'] or NOL)
    selisih = total_pool - total_posisi
    return {
        'nilai_pool': total_pool,
        'total_posisi': total_posisi,
        'selisih': selisih,
        'cocok': selisih == 0,
        # Selisih dalam toleransi boleh ditutup luruskan_pembulatan().
        # Di luar toleransi berarti ada jalur yang menyentuh Stok.nilai
        # tanpa lewat modul ini -- jangan ditutup, dilacak.
        'dalam_toleransi': abs(selisih) <= toleransi,
        'toleransi': toleransi,
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
                .aggregate(t=Sum('nilai'))['t'] or NOL)
        if asli != p.nilai_bersih:
            melenceng.append({
                'entitas': p.entitas.kode, 'cache': p.nilai_bersih,
                'ledger': asli, 'selisih': p.nilai_bersih - asli,
            })
    return melenceng


def verifikasi_rantai_saldo(stok_id, sejak_urutan=0):
    """Invariant (3): rantai saldo berjalan qty dan nilai, satu pass."""
    from django.db import connection

    with connection.cursor() as c:
        c.execute("""
            SELECT urutan, saldo_akhir, qty_seharusnya,
                   saldo_nilai, nilai_seharusnya FROM (
                SELECT urutan, saldo_akhir, saldo_nilai,
                       LAG(saldo_akhir) OVER (ORDER BY urutan)
                           + masuk - keluar        AS qty_seharusnya,
                       LAG(saldo_nilai) OVER (ORDER BY urutan)
                           + nilai_masuk - nilai_keluar AS nilai_seharusnya
                  FROM inventory_mutasi_stok
                 WHERE stok_id = %s AND urutan > %s
            ) t
            WHERE (qty_seharusnya IS NOT NULL AND saldo_akhir <> qty_seharusnya)
               OR (nilai_seharusnya IS NOT NULL
                   AND saldo_nilai <> nilai_seharusnya)
        """, [stok_id, sejak_urutan])
        return c.fetchall()


def verifikasi_semua(grup_bahan_id):
    """Satu panggilan untuk cron nightly."""
    return {
        'kepemilikan': verifikasi_kepemilikan(grup_bahan_id),
        'posisi_cache': verifikasi_posisi_cache(grup_bahan_id),
        'pool_bersih': verifikasi_pool_bersih(grup_bahan_id),
    }