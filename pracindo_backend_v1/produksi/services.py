"""
Logika bisnis produksi — produksi/services.py

DUA HAL YANG TIDAK BOLEH DICAMPUR

  KELAYAKAN FISIK    berapa unit yang BISA diproduksi.
                     min() atas semua bahan dalam resep. Rupiah tidak
                     berlaku di sini -- klaim senilai Rp50.000 tidak bisa
                     jadi teh kemasan kalau teh celupnya habis.

  ALIRAN NILAI       berapa rupiah yang menempel di hasil.
                     Sebanding rendemen. Harga per satuan TETAP; yang
                     susut kehilangan nilainya, dan kehilangan itu
                     dibebankan ke pemegang hak.

    Bahan A  10 kg  Rp10.000
    Bahan B  20 kg  Rp30.000
    Bahan C   5 kg  Rp10.000
    ----------------------------
    Masuk    35 kg  Rp50.000     Rp1.428,57/kg
    Hasil    33 kg  Rp47.142,86  Rp1.428,57/kg   <- harga tidak berubah
    Susut     2 kg  Rp 2.857,14  -> MutasiKlaim RUGI, pro-rata

  KENAPA BUKAN ABSORPSI
    Kalau nilai penuh dipaksa menempel di 33 kg, harganya jadi
    Rp1.515,15/kg. Siapa pun yang kebetulan mengklaim dari batch
    bersusut tinggi jadi membayar lebih mahal, padahal susut itu milik
    bersama. Dengan pengakuan kerugian, harga konsisten antar batch dan
    susutnya dibagi rata sesuai besar hak.

  DASAR RENDEMEN
    Rasio nilai dihitung dari HASIL versus HASIL YANG SEHARUSNYA, bukan
    dari qty hasil versus qty bahan. Versi lama membagi unit produk jadi
    dengan kilogram bahan -- hanya kebetulan benar saat 1 unit = 1 kg,
    dan skenario 35 kg -> 35 unit menyembunyikannya sempurna. Lihat
    selesaikan_sesi().

Semua operasi bekerja di lapis POOL. Entitas tidak pernah muncul di sini,
kecuali saat kerugian harus dibebankan -- dan itu didelegasikan ke
inventory.bebankan_rugi().
"""
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from inventory.models import Lapis, Stok
from inventory.services import (
    alokasi_prorata, bebankan_rugi, hasil_ke_pool, pakai_dari_pool,
)

from .models import (
    HasilKomponen, JenisSesi, Resep, SesiInput, SesiProduksi, StatusSesi,
)

Q3 = Decimal('0.001')
Q2 = Decimal('0.01')
NOL = Decimal('0')


# =========================================================
# KAPASITAS
# =========================================================

def _tersedia_per_bahan(grup_bahan_id, bahan_ids):
    """
    Total qty per bahan di POOL, DIJUMLAHKAN lintas tangki.

    Dulu ini dict comprehension atas baris Stok, sehingga bahan yang
    tersimpan di dua tangki hanya terhitung satu tangki -- yang terakhir
    menimpa yang sebelumnya. Kapasitas jadi lebih kecil dari kenyataan.
    """
    baris = (Stok.objects
             .filter(grup_bahan_id=grup_bahan_id, lapis=Lapis.POOL,
                     produk_id__in=bahan_ids)
             .values('produk_id')
             .annotate(total=Sum('qty'), nilai=Sum('nilai')))
    return {b['produk_id']: (b['total'], b['nilai']) for b in baris}


def hitung_kapasitas(grup_bahan_id, produk_jadi_id, tanggal=None):
    """Berapa unit yang bisa diproduksi dari isi pool saat ini."""
    resep = Resep.berlaku(produk_jadi_id, tanggal)
    item = list(resep.item.select_related('bahan'))
    if not item:
        raise ValidationError(f'Resep {resep} belum punya bahan.')

    tersedia = _tersedia_per_bahan(grup_bahan_id, [i.bahan_id for i in item])

    rincian, kapasitas = [], []
    for i in item:
        ada, nilai = tersedia.get(i.bahan_id, (NOL, NOL))
        per_unit = i.qty / resep.hasil_per_batch
        cukup = ((ada / per_unit).quantize(Q3, rounding=ROUND_DOWN)
                 if per_unit else NOL)
        kapasitas.append(cukup)
        rincian.append({
            'bahan': i.bahan.kode, 'bahan_id': i.bahan_id,
            'tersedia': ada, 'nilai_tersedia': nilai,
            'harga_rata': (nilai / ada).quantize(Decimal('0.0001')) if ada else NOL,
            'per_unit': per_unit, 'cukup_untuk': cukup,
        })

    maksimum = min(kapasitas) if kapasitas else NOL
    pembatas = [r['bahan'] for r in rincian if r['cukup_untuk'] == maksimum]

    sisa = {
        r['bahan']: (r['tersedia'] - (maksimum * r['per_unit'])).quantize(Q3)
        for r in rincian
    }
    return {
        'resep': str(resep),
        'resep_id': resep.id,
        'maksimum': maksimum,
        'pembatas': pembatas,
        'rincian': rincian,
        'sisa_bila_maksimum': sisa,
    }


# =========================================================
# ALOKASI TANGKI
# =========================================================

def alokasi_tangki(grup_bahan_id, bahan_id, qty):
    """
    Memecah kebutuhan satu bahan ke beberapa tangki asal.

    Ditarik dari tangki dengan isi terbanyak dulu supaya jumlah tangki
    yang tersentuh sesedikit mungkin -- tiap tangki yang dibuka adalah
    satu kesempatan salah tuang.

    Return: [(tangki_id, qty), ...]. tangki_id None = stok rak.
    """
    qty = Decimal(qty).quantize(Q3)
    baris = list(Stok.objects
                 .filter(grup_bahan_id=grup_bahan_id, lapis=Lapis.POOL,
                         produk_id=bahan_id, qty__gt=0)
                 .select_related('produk', 'tangki')
                 .order_by('-qty'))

    total = sum(b.qty for b in baris)
    if total < qty:
        nama = baris[0].produk.kode if baris else bahan_id
        raise ValidationError(
            f'Pool hanya berisi {total} {nama}, dibutuhkan {qty}.'
        )

    hasil, sisa = [], qty
    for b in baris:
        if sisa <= 0:
            break
        ambil = min(b.qty, sisa)
        hasil.append((b.tangki_id, ambil))
        sisa -= ambil
    return hasil


# =========================================================
# PEMBUATAN SESI
# =========================================================

@transaction.atomic
def buat_sesi_produksi(*, grup_bahan_id, resep_id, qty_target, tanggal,
                       user, tangki_hasil_id=None, catatan='', idem_key=''):
    """
    Membuat sesi DRAFT Produksi Rutin beserta rencana per tangki.

    `idem_key` mencegah klik ganda melahirkan dua sesi. DRAFT memang belum
    menarik bahan dari pool, jadi tidak berbahaya -- tapi mengotori daftar
    dan membuat operator ragu sesi mana yang harus dimulai. PRD-v2 §31:
    semua mutasi wajib punya kunci idempotensi.
    """
    if idem_key:
        ada = SesiProduksi.objects.filter(idem_key=idem_key).first()
        if ada:
            return ada

    resep = Resep.objects.select_related('produk_jadi').get(pk=resep_id)
    qty_target = Decimal(qty_target).quantize(Q3)

    kap = hitung_kapasitas(grup_bahan_id, resep.produk_jadi_id, tanggal)
    if qty_target > kap['maksimum']:
        raise ValidationError(
            f"Bahan hanya cukup untuk {kap['maksimum']} unit "
            f"(dibatasi {', '.join(kap['pembatas'])}), diminta {qty_target}."
        )

    sesi = SesiProduksi(
        grup_bahan_id=grup_bahan_id, tanggal=tanggal, resep=resep,
        produk_jadi_id=resep.produk_jadi_id, qty_target=qty_target,
        tangki_hasil_id=tangki_hasil_id, jenis_sesi=JenisSesi.PRODUKSI,
        catatan=catatan, dibuat_oleh=user,
        # None, bukan '': kolomnya unique, dan string kosong berkali-kali
        # akan bentrok. NULL boleh berulang di semua basis data yang dipakai.
        idem_key=idem_key or None,
    )
    sesi.save()

    for bahan_id, qty in resep.kebutuhan(qty_target).items():
        for tangki_id, bagian in alokasi_tangki(grup_bahan_id, bahan_id, qty):
            SesiInput.objects.create(
                sesi=sesi, bahan_id=bahan_id, tangki_id=tangki_id,
                qty_rencana=bagian, qty_aktual=bagian,
            )
    return sesi


@transaction.atomic
def buat_sesi_rnd(*, grup_bahan_id, produk_jadi_id, qty_target, tanggal,
                  user, baris, hasil_masuk_pool=True, tangki_hasil_id=None,
                  catatan='', idem_key=''):
    """
    Sesi DRAFT eksperimen, tanpa resep dan tanpa batas kapasitas.

    hasil_masuk_pool=False berarti hasilnya dibuang atau disimpan di luar
    sistem. Nilai bahannya tetap musnah dari pool, jadi selesaikan_sesi()
    akan membebankannya sebagai kerugian -- persis seperti sesi gagal.
    """
    if idem_key:
        ada = SesiProduksi.objects.filter(idem_key=idem_key).first()
        if ada:
            return ada

    qty_target = Decimal(qty_target).quantize(Q3)
    if not baris:
        raise ValidationError('Sesi R&D butuh minimal satu bahan.')

    sesi = SesiProduksi(
        grup_bahan_id=grup_bahan_id, tanggal=tanggal,
        produk_jadi_id=produk_jadi_id, qty_target=qty_target,
        jenis_sesi=JenisSesi.RND, hasil_masuk_pool=hasil_masuk_pool,
        tangki_hasil_id=tangki_hasil_id, catatan=catatan, dibuat_oleh=user,
        idem_key=idem_key or None,
    )
    sesi.save()

    for b in baris:
        qty = Decimal(b['qty_rencana']).quantize(Q3)
        if qty <= 0:
            continue
        tangki_id = b.get('tangki_id')
        potongan = ([(tangki_id, qty)] if tangki_id
                    else alokasi_tangki(grup_bahan_id, b['bahan_id'], qty))
        for tid, bagian in potongan:
            SesiInput.objects.create(
                sesi=sesi, bahan_id=b['bahan_id'], tangki_id=tid,
                qty_rencana=bagian, qty_aktual=bagian,
            )
    return sesi


# =========================================================
# MULAI — bahan keluar dari pool
# =========================================================

@transaction.atomic
def mulai_sesi(*, sesi_id, qty_aktual=None):
    """
    Menarik bahan dari pool dan mencatat rupiah yang ikut keluar.

    `qty_aktual` boleh berisi nol untuk membatalkan satu bahan. Dulu nol
    membuat pakai_dari_pool() menolak dan seluruh sesi ikut rollback --
    operator tidak punya cara bilang "bahan C tidak jadi dipakai".
    Sekarang baris nol dilewati dan qty_rencana-nya tetap tercatat.

    Kunci: {(bahan_id, tangki_id): qty} atau {bahan_id: qty} untuk
    membagi rata ke seluruh tangki bahan itu secara proporsional.
    """
    sesi = SesiProduksi.objects.select_for_update().get(pk=sesi_id)
    if sesi.status != StatusSesi.DRAFT:
        raise ValidationError(f'Sesi sudah {sesi.get_status_display()}.')

    override = _normalkan_override(sesi, qty_aktual or {})
    nilai_total = NOL
    ada_yang_dipakai = False

    for inp in (sesi.input.select_for_update()
                .select_related('bahan', 'tangki').order_by('id')):
        kunci = (inp.bahan_id, inp.tangki_id)
        if kunci in override:
            inp.qty_aktual = override[kunci]

        if inp.qty_aktual <= 0:
            inp.qty_aktual = NOL
            inp.nilai_aktual = NOL
            inp.save(update_fields=['qty_aktual', 'nilai_aktual'])
            continue

        _, nilai = pakai_dari_pool(
            produk_id=inp.bahan_id,
            grup_bahan_id=sesi.grup_bahan_id,
            qty=inp.qty_aktual,
            tanggal=sesi.tanggal,
            referensi=sesi.nomor,
            idem_key=f'sesi:{sesi.id}:pakai:{inp.bahan_id}:{inp.tangki_id or 0}',
            tangki_id=inp.tangki_id,
        )
        inp.nilai_aktual = nilai
        inp.save(update_fields=['qty_aktual', 'nilai_aktual'])
        nilai_total += nilai
        ada_yang_dipakai = True

    if not ada_yang_dipakai:
        raise ValidationError(
            'Semua bahan berkuantitas nol. Batalkan sesi kalau memang '
            'tidak jadi berjalan.'
        )

    sesi.nilai_input = nilai_total
    sesi.status = StatusSesi.BERJALAN
    sesi.save(update_fields=['nilai_input', 'status'])
    return sesi


def _normalkan_override(sesi, qty_aktual):
    """
    Menerima {bahan_id: qty} maupun {(bahan_id, tangki_id): qty}.

    Bentuk pertama dibagi proporsional ke tangki-tangki bahan itu,
    dengan sisa pembulatan ke bagian terbesar supaya totalnya persis.
    """
    hasil, per_bahan = {}, {}
    for k, v in qty_aktual.items():
        if isinstance(k, tuple):
            hasil[(k[0], k[1])] = Decimal(v).quantize(Q3)
        else:
            per_bahan[int(k)] = Decimal(v).quantize(Q3)

    if not per_bahan:
        return hasil

    baris = list(sesi.input.filter(bahan_id__in=per_bahan.keys()))
    for bahan_id, total in per_bahan.items():
        milik = [b for b in baris if b.bahan_id == bahan_id]
        if not milik:
            raise ValidationError(f'Bahan {bahan_id} bukan bagian sesi ini.')
        if len(milik) == 1:
            hasil[(bahan_id, milik[0].tangki_id)] = total
            continue
        dasar = sum(b.qty_rencana for b in milik) or Decimal('1')
        milik.sort(key=lambda b: b.qty_rencana, reverse=True)
        terpakai = NOL
        for b in milik[1:]:
            bagian = (total * b.qty_rencana / dasar).quantize(
                Q3, rounding=ROUND_HALF_UP)
            hasil[(bahan_id, b.tangki_id)] = bagian
            terpakai += bagian
        hasil[(bahan_id, milik[0].tangki_id)] = total - terpakai
    return hasil


def _simpan_komposisi_hasil(sesi, qty_hasil, nilai_hasil):
    """Persistenkan lineage X -> bahan input dengan pembulatan deterministik."""
    inputs = [i for i in sesi.input.all() if i.qty_aktual > 0]
    if not inputs:
        raise ValidationError('Hasil tidak memiliki komponen bahan aktual.')

    total_qty = sum((i.qty_aktual for i in inputs), NOL)
    total_nilai = sum((i.nilai_aktual for i in inputs), NOL)
    if total_qty <= 0:
        raise ValidationError('Total bahan aktual harus lebih dari nol.')
    if total_nilai != sesi.nilai_input:
        raise ValidationError(
            'Nilai komponen input tidak sama dengan nilai_input sesi.'
        )

    HasilKomponen.objects.filter(sesi=sesi).delete()

    # Bagian terbesar menerima residual pembulatan terakhir agar total qty
    # dan nilai tepat sama dengan output sesi.
    inputs.sort(key=lambda i: (i.qty_aktual, i.id), reverse=True)
    rows = []
    qty_terpakai = NOL
    nilai_terpakai = NOL
    for i in inputs[1:]:
        q = (qty_hasil * i.qty_aktual / total_qty).quantize(
            Q3, rounding=ROUND_HALF_UP)
        v = (nilai_hasil * i.nilai_aktual / total_nilai).quantize(
            Q2, rounding=ROUND_HALF_UP) if total_nilai else NOL
        rows.append((i, q, v))
        qty_terpakai += q
        nilai_terpakai += v

    utama = inputs[0]
    rows.append((
        utama, qty_hasil - qty_terpakai, nilai_hasil - nilai_terpakai
    ))

    for i, q, v in rows:
        if q < 0 or v < 0:
            raise ValidationError('Pembulatan komponen menghasilkan nilai negatif.')
        HasilKomponen.objects.create(
            sesi=sesi, sesi_input=i, bahan_id=i.bahan_id, qty=q, nilai=v,
        )

    cek = HasilKomponen.objects.filter(sesi=sesi).aggregate(
        qty=Sum('qty'), nilai=Sum('nilai')
    )
    if cek['qty'] != qty_hasil or cek['nilai'] != nilai_hasil:
        raise ValidationError(
            'Komposisi hasil tidak seimbang dengan qty/nilai hasil.'
        )


# =========================================================
# SELESAI — nilai kembali ke pool
# =========================================================

@transaction.atomic
def selesaikan_sesi(*, sesi_id, qty_hasil, abaikan_susut=False):
    """
    Hasil masuk pool membawa nilai SEBANDING RENDEMEN. Selisihnya --
    nilai yang melekat pada bagian yang susut -- dibebankan ke pemegang
    hak lewat MutasiKlaim RUGI.

    Batas yang berarti adalah batas BAWAH: hasil di bawah
    target x (1 - susut_wajar) berarti ada yang tidak beres. Batas atas
    juga dijaga karena hasil melebihi target biasanya salah timbang.

    `abaikan_susut=True` menembus batas bawah dengan sengaja -- dipakai
    kalau supervisor sudah memeriksa dan memang segitu hasilnya.
    """
    sesi = SesiProduksi.objects.select_for_update().select_related(
        'resep', 'grup_bahan').get(pk=sesi_id)
    if sesi.status != StatusSesi.BERJALAN:
        raise ValidationError(
            f'Sesi harus berstatus Berjalan, sekarang '
            f'{sesi.get_status_display()}.'
        )

    qty_hasil = Decimal(qty_hasil).quantize(Q3)
    if qty_hasil <= 0:
        raise ValidationError(
            'Qty hasil harus lebih dari nol. Kalau tidak ada hasil sama '
            'sekali, gagalkan sesinya.'
        )

    if sesi.jenis_sesi == JenisSesi.PRODUKSI:
        if qty_hasil > sesi.qty_target:
            raise ValidationError(
                f'Hasil {qty_hasil} melebihi target {sesi.qty_target}. '
                f'Periksa timbangan atau resepnya.'
            )
        if sesi.resep and not abaikan_susut:
            batas = (sesi.qty_target * sesi.resep.hasil_minimum_wajar
                     ).quantize(Q3)
            if qty_hasil < batas:
                hilang = (100 * (1 - qty_hasil / sesi.qty_target)).quantize(Q2)
                raise ValidationError(
                    f'Susut {hilang}% melampaui batas wajar resep '
                    f'({sesi.resep.susut_wajar * 100}%). Hasil minimum '
                    f'{batas}. Minta supervisor menyetujui lewat '
                    f'abaikan_susut kalau angkanya memang benar.'
                )

    # =====================================================
    # PEMBAGIAN NILAI: yang selamat vs yang susut
    # =====================================================
    # DASAR RENDEMEN, BUKAN QTY BAHAN.
    #
    # Yang dibandingkan harus dua besaran bersatuan sama: hasil yang
    # KELUAR versus hasil yang SEHARUSNYA keluar dari bahan yang
    # benar-benar ditarik. Versi lama membagi qty_hasil (unit produk
    # jadi) dengan qty bahan (kg) -- hanya kebetulan benar saat 1 unit
    # = 1 kg, dan skenario uji 35 kg -> 35 unit menyembunyikannya
    # sempurna.
    #
    #   target 30 unit, rencana bahan 35 kg, aktual 35 kg, hasil 29 unit
    #     benar : 29/30 -> susut  3,3%
    #     lama  : 29/35 -> susut 17,1%   <- selisihnya dibebankan sebagai
    #                                       RUGI ke orang yang tidak
    #                                       melakukan kesalahan apa pun
    #
    # Nilai susut selalu merupakan SELISIH, bukan angka yang dibulatkan
    # sendiri, supaya hasil + susut == nilai_input persis.
    baris_input = list(sesi.input.all())
    qty_input_aktual = sum((i.qty_aktual for i in baris_input), NOL)
    qty_rencana_total = sum((i.qty_rencana for i in baris_input), NOL)

    if qty_input_aktual <= 0:
        raise ValidationError(
            'Sesi tidak memiliki bahan aktual. Selesaikan tidak dapat '
            'menciptakan nilai tanpa input nyata.'
        )

    if sesi.jenis_sesi == JenisSesi.PRODUKSI and qty_rencana_total > 0:
        # Diskalakan kalau bahan aktual meleset dari rencana: menarik
        # separuh bahan wajar menghasilkan separuh target.
        hasil_seharusnya = (sesi.qty_target * qty_input_aktual
                            / qty_rencana_total).quantize(Q3)
    else:
        # R&D tanpa resep tidak punya ekspektasi rendemen. Satu-satunya
        # dasar yang tersedia adalah qty bahan -- sah HANYA kalau satuan
        # hasil sama dengan satuan bahan.
        hasil_seharusnya = qty_input_aktual

    if hasil_seharusnya <= 0:
        raise ValidationError(
            'Dasar rendemen tidak bisa dihitung: rencana bahan nol.'
        )

    # min(...,1) mencegah hasil di atas ekspektasi MENCIPTAKAN nilai.
    # Kelebihan hasil bukan tambahan rupiah, hanya tambahan qty.
    rasio = min(qty_hasil / hasil_seharusnya, Decimal('1'))
    nilai_terbawa = (sesi.nilai_input * rasio).quantize(
        Q2, rounding=ROUND_HALF_UP)
    nilai_susut = sesi.nilai_input - nilai_terbawa

    if sesi.hasil_masuk_pool:
        hasil_ke_pool(
            produk_id=sesi.produk_jadi_id,
            grup_bahan_id=sesi.grup_bahan_id,
            qty=qty_hasil,
            nilai_masuk=nilai_terbawa,
            tanggal=sesi.tanggal,
            referensi=sesi.nomor,
            idem_key=f'sesi:{sesi.id}:hasil',
            tangki_id=sesi.tangki_hasil_id,
        )
        _simpan_komposisi_hasil(sesi, qty_hasil, nilai_terbawa)
        sesi.nilai_hasil = nilai_terbawa
    else:
        # Hasil tidak masuk pool: seluruh nilai input hilang dari pool.
        nilai_susut = sesi.nilai_input
        sesi.nilai_hasil = NOL

    # Nilai yang hilang WAJIB punya penanggung. Tanpa baris ini, pool
    # berkurang sementara total klaim tetap, dan setiap orang mengira
    # haknya masih utuh.
    if nilai_susut > 0:
        bebankan_rugi(
            grup_bahan_id=sesi.grup_bahan_id,
            nilai=nilai_susut,
            tanggal=sesi.tanggal,
            referensi=f'{sesi.nomor} susut',
            idem_key=f'sesi:{sesi.id}:rugi-susut',
        )

    # NOL, bukan None. Sesi selesai tanpa susut berarti kerugiannya nol
    # dan itu fakta; None berarti "belum diketahui" dan membuat
    # nilai_hasil + nilai_kerugian meledak jadi TypeError.
    sesi.nilai_kerugian = nilai_susut

    sesi.qty_hasil = qty_hasil
    sesi.status = StatusSesi.SELESAI
    sesi.save(update_fields=['qty_hasil', 'nilai_hasil', 'nilai_kerugian',
                             'status'])
    return sesi


# =========================================================
# GAGAL — nilai musnah, ada yang menanggung
# =========================================================

@transaction.atomic
def gagalkan_sesi(*, sesi_id, alasan, kategori):
    """
    Bahan sudah telanjur hangus dan tidak ada barang jadi.

    Nilai yang keluar saat mulai_sesi() dibebankan pro-rata ke pemegang
    klaim positif dalam grup. Ini bukan formalitas: tanpa baris RUGI,
    pool berkurang sementara total klaim tetap, dan setiap orang mengira
    haknya masih utuh.
    """
    sesi = SesiProduksi.objects.select_for_update().get(pk=sesi_id)
    if sesi.status != StatusSesi.BERJALAN:
        raise ValidationError(
            f'Hanya sesi Berjalan yang bisa digagalkan, sekarang '
            f'{sesi.get_status_display()}.'
        )
    if not alasan.strip():
        raise ValidationError('Alasan kegagalan wajib diisi.')

    if sesi.nilai_input > 0:
        bebankan_rugi(
            grup_bahan_id=sesi.grup_bahan_id,
            nilai=sesi.nilai_input,
            tanggal=sesi.tanggal,
            referensi=f'{sesi.nomor} GAGAL',
            idem_key=f'sesi:{sesi.id}:rugi',
        )

    sesi.status = StatusSesi.GAGAL
    sesi.kategori_kegagalan = kategori
    sesi.nilai_kerugian = sesi.nilai_input
    sesi.catatan = f'{sesi.catatan}\n[GAGAL] {alasan}'.strip()
    sesi.save(update_fields=['status', 'kategori_kegagalan',
                             'nilai_kerugian', 'catatan'])
    return sesi


@transaction.atomic
def batalkan_sesi(*, sesi_id, alasan=''):
    """Membatalkan sesi DRAFT sebelum bahan keluar."""
    sesi = SesiProduksi.objects.select_for_update().get(pk=sesi_id)
    if sesi.status != StatusSesi.DRAFT:
        raise ValidationError(
            'Bahan sudah keluar dari pool. Selesaikan atau gagalkan sesi, '
            'lalu koreksi lewat penyesuaian opname.'
        )
    sesi.status = StatusSesi.BATAL
    sesi.catatan = f'{sesi.catatan}\n[BATAL] {alasan}'.strip()
    sesi.save(update_fields=['status', 'catatan'])
    return sesi


# =========================================================
# PEMBACAAN
# =========================================================

def ringkasan_sesi(sesi_id):
    """Rincian input, output, nilai, dan susut untuk satu sesi."""
    sesi = (SesiProduksi.objects
            .select_related('produk_jadi', 'grup_bahan', 'resep',
                            'tangki_hasil')
            .prefetch_related('input__bahan', 'input__tangki')
            .get(pk=sesi_id))

    return {
        'id': sesi.id,
        'nomor': sesi.nomor,
        'tanggal': sesi.tanggal,
        'grup': sesi.grup_bahan.kode,
        'jenis_sesi': sesi.jenis_sesi,
        'produk': sesi.produk_jadi.kode,
        'target': sesi.qty_target,
        'hasil': sesi.qty_hasil,
        'susut': sesi.susut,
        'rendemen': sesi.rendemen,
        'status': sesi.get_status_display(),
        'tangki_hasil': sesi.tangki_hasil.kode if sesi.tangki_hasil_id else None,
        'nilai_input': sesi.nilai_input,
        'nilai_hasil': sesi.nilai_hasil,
        'nilai_kerugian': sesi.nilai_kerugian,
        'harga_hasil_per_satuan': sesi.harga_hasil_per_satuan,
        'input': [
            {
                'bahan': i.bahan.kode,
                'bahan_nama': i.bahan.nama,
                'tangki': i.tangki.kode if i.tangki_id else None,
                'rencana': i.qty_rencana,
                'aktual': i.qty_aktual,
                'selisih': i.selisih,
                'nilai': i.nilai_aktual,
                'harga_per_satuan': i.harga_per_satuan,
            }
            for i in sesi.input.all()
        ],
    }


def pratinjau_kerugian(sesi_id):
    """
    Rupiah yang hangus kalau sesi ini digagalkan, beserta beban per
    entitas.

    Angka di sini WAJIB identik dengan yang nanti benar-benar terbit.
    Versi lama membulatkan tiap beban sendiri-sendiri, sehingga jumlah
    kolom `menanggung` bisa meleset satu-dua sen dari `nilai_kerugian`
    di baris atasnya -- dan operator kehilangan kepercayaan pada
    layarnya sendiri. Sekarang memakai alokasi_prorata() yang sama
    persis dengan bebankan_rugi(), termasuk cara residual dialokasikan.

    Untuk sesi BERJALAN dipakai nilai yang benar-benar sudah keluar;
    untuk DRAFT diperkirakan dari harga rata tangki asal.
    """
    from inventory.models import PosisiKlaim

    sesi = (SesiProduksi.objects.select_related('grup_bahan')
            .prefetch_related('input__bahan', 'input__tangki').get(pk=sesi_id))

    rincian, total = [], NOL
    for i in sesi.input.all():
        if sesi.status == StatusSesi.BERJALAN:
            nilai = i.nilai_aktual
        else:
            stok = Stok.objects.filter(
                grup_bahan_id=sesi.grup_bahan_id, lapis=Lapis.POOL,
                produk_id=i.bahan_id, tangki_id=i.tangki_id,
            ).first()
            harga = stok.harga_rata if stok else NOL
            nilai = (i.qty_aktual * harga).quantize(Q2, rounding=ROUND_HALF_UP)
        total += nilai
        rincian.append({
            'bahan_kode': i.bahan.kode,
            'bahan_nama': i.bahan.nama,
            'tangki': i.tangki.kode if i.tangki_id else None,
            'qty': i.qty_aktual,
            'harga_per_satuan': i.harga_per_satuan if i.nilai_aktual else NOL,
            'nilai': nilai,
        })

    # Siapa menanggung berapa, memakai aturan pembagian yang sama persis.
    posisi = list(PosisiKlaim.objects
                  .filter(grup_bahan_id=sesi.grup_bahan_id, nilai_bersih__gt=0)
                  .select_related('entitas'))
    bagian = (alokasi_prorata({p.entitas_id: p.nilai_bersih for p in posisi},
                              total)
              if posisi else {})
    beban = [
        {
            'entitas': p.entitas.kode,
            'posisi_sekarang': p.nilai_bersih,
            'menanggung': bagian.get(p.entitas_id, NOL),
        }
        for p in posisi
    ]

    return {
        'nilai_kerugian': total,
        'rincian': rincian,
        'beban_entitas': beban,
        'peringatan': ('Tidak ada pemegang hak positif — kerugian tidak '
                       'bisa dibebankan.') if not posisi and total else None,
    }


def banding_batch(ids):
    """
    Matriks perbandingan beberapa sesi.

    Pengukuran berkode sama yang tercatat berkali-kali (mis. suhu tiap
    15 menit) sekarang diringkas jadi awal/akhir/min/maks/rata, bukan
    hanya yang terakhir seperti sebelumnya.

    CATATAN: keluaran fungsi ini mengandung rupiah. Penyaringan untuk
    yang tidak punya akses akunting dilakukan di view, bukan di sini.
    """
    sesi_qs = (SesiProduksi.objects.filter(id__in=ids)
               .select_related('produk_jadi')
               .prefetch_related('input__bahan', 'pengukuran__nama'))

    sesi_data, bahan_terpakai, ukur_terpakai = [], {}, {}

    for s in sesi_qs:
        dasar = s.qty_hasil if s.qty_hasil > 0 else s.qty_target
        sesi_data.append({
            'id': s.id, 'nomor': s.nomor, 'tanggal': s.tanggal,
            'jenis_sesi': s.jenis_sesi, 'status': s.status,
            'produk_jadi_kode': s.produk_jadi.kode,
            'qty_target': s.qty_target, 'qty_hasil': s.qty_hasil,
            'rendemen': s.rendemen,
            'nilai_input': s.nilai_input, 'nilai_hasil': s.nilai_hasil,
            'harga_per_satuan': s.harga_hasil_per_satuan,
            'satuan_kode': getattr(s.produk_jadi, 'satuan_kode', 'unit'),
        })

        for i in s.input.all():
            k = i.bahan.kode
            slot = bahan_terpakai.setdefault(k, {
                'kode': k, 'label': i.bahan.nama,
                'satuan': getattr(i.bahan, 'satuan_kode', 'unit'), 'nilai': {},
            })
            # Satu bahan bisa berasal dari beberapa tangki: dijumlahkan.
            sebelum = slot['nilai'].get(s.id, NOL)
            slot['nilai'][s.id] = sebelum + (
                (i.qty_aktual / dasar).quantize(Decimal('0.0001'))
                if dasar else NOL
            )

        for p in s.pengukuran.all():
            k = p.nama.kode
            slot = ukur_terpakai.setdefault(k, {
                'kode': k, 'label': p.nama.nama, 'satuan': p.nama.satuan,
                'tahap': p.tahap, 'nilai': {},
            })
            slot['nilai'].setdefault(s.id, []).append(
                p.nilai if p.nilai is not None else p.nilai_teks)

    def _ringkas(nilai_list):
        angka = [v for v in nilai_list if isinstance(v, Decimal)]
        if not angka:
            return {'terakhir': nilai_list[-1], 'jumlah_catatan': len(nilai_list)}
        return {
            'awal': angka[0], 'akhir': angka[-1],
            'min': min(angka), 'maks': max(angka),
            'rata': (sum(angka) / len(angka)).quantize(Decimal('0.0001')),
            'jumlah_catatan': len(angka),
        }

    urutan = [s['id'] for s in sesi_data]
    bahan_list = [
        {**v, 'nilai': [v['nilai'].get(i) for i in urutan]}
        for v in bahan_terpakai.values()
    ]
    ukur_list = [
        {**v, 'nilai': [_ringkas(v['nilai'][i]) if i in v['nilai'] else None
                        for i in urutan]}
        for v in ukur_terpakai.values()
    ]

    return {'sesi': sesi_data, 'pengukuran': ukur_list,
            'bahan_per_unit': bahan_list}