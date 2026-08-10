"""
Logika bisnis produksi — produksi/services.py

DUA HAL YANG TIDAK BOLEH DICAMPUR

  KELAYAKAN FISIK    berapa unit yang BISA diproduksi.
                     min() atas semua bahan dalam resep. Per produk.
                     Nilai ekuivalen TIDAK berlaku di sini -- klaim
                     senilai Rp 50.000 tidak bisa jadi teh kemasan kalau
                     teh celupnya habis.

  PENYELESAIAN       siapa berhutang berapa.
                     Di sinilah nilai ekuivalen bekerja: N produk x M
                     entitas runtuh jadi M angka. Ditangani modul
                     inventory lewat buku klaim.

Semua operasi bekerja di lapis POOL. Entitas tidak pernah muncul di sini.
"""
from decimal import ROUND_DOWN, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from inventory.models import Lapis, Stok
from inventory.services import hasil_ke_pool, pakai_dari_pool

from .models import Resep, SesiInput, SesiProduksi, StatusSesi

Q3 = Decimal('0.001')


# =========================================================
# KAPASITAS
# =========================================================

def hitung_kapasitas(grup_bahan_id, produk_jadi_id, tanggal=None):
    """
    Berapa unit yang bisa diproduksi dari isi pool saat ini.

    Bahan yang paling sedikit menentukan batasnya -- bahan pembatas.
    Contoh: pool berisi 45 g gula dan 22 teh celup, resep 1 celup + 2 g
    gula. Gula cukup untuk 22 unit, celup untuk 22 unit, jadi maksimum
    22 unit dan gula tersisa 1 g.

    Return:
        {
          'maksimum': 22,
          'pembatas': ['CELUP'],
          'rincian': [{'bahan','tersedia','per_unit','cukup_untuk'}, ...],
          'sisa_bila_maksimum': {'GULA': 1, 'CELUP': 0},
        }
    """
    resep = Resep.berlaku(produk_jadi_id, tanggal)
    item = list(resep.item.select_related('bahan'))
    if not item:
        raise ValidationError(f'Resep {resep} belum punya bahan.')

    tersedia = {
        s.produk_id: s.qty
        for s in Stok.objects.filter(
            grup_bahan_id=grup_bahan_id, lapis=Lapis.POOL,
            produk_id__in=[i.bahan_id for i in item],
        )
    }

    rincian, kapasitas = [], []
    for i in item:
        ada = tersedia.get(i.bahan_id, Decimal('0'))
        per_unit = i.qty / resep.hasil_per_batch
        cukup = (ada / per_unit).quantize(Q3, rounding=ROUND_DOWN) if per_unit else Decimal('0')
        kapasitas.append(cukup)
        rincian.append({
            'bahan': i.bahan.kode, 'bahan_id': i.bahan_id,
            'tersedia': ada, 'per_unit': per_unit, 'cukup_untuk': cukup,
        })

    maksimum = min(kapasitas) if kapasitas else Decimal('0')
    pembatas = [r['bahan'] for r in rincian if r['cukup_untuk'] == maksimum]

    sisa = {}
    for r in rincian:
        sisa[r['bahan']] = (
            r['tersedia'] - (maksimum * r['per_unit'])
        ).quantize(Q3)

    return {
        'resep': str(resep),
        'maksimum': maksimum,
        'pembatas': pembatas,
        'rincian': rincian,
        'sisa_bila_maksimum': sisa,
    }


# =========================================================
# ALUR SESI
# =========================================================

@transaction.atomic
def buat_sesi(*, grup_bahan_id, produk_jadi_id, qty_target, tanggal,
              user, tangki_hasil_id=None, catatan=''):
    """
    Membuat sesi DRAFT beserta rencana pemakaian bahan.

    Belum menyentuh stok sama sekali -- rencana bisa diubah sampai
    mulai_sesi() dipanggil.
    """
    resep = Resep.berlaku(produk_jadi_id, tanggal)
    qty_target = Decimal(qty_target).quantize(Q3)

    kap = hitung_kapasitas(grup_bahan_id, produk_jadi_id, tanggal)
    if qty_target > kap['maksimum']:
        raise ValidationError(
            f"Bahan hanya cukup untuk {kap['maksimum']} unit "
            f"(dibatasi {', '.join(kap['pembatas'])}), diminta {qty_target}."
        )

    sesi = SesiProduksi.objects.create(
        grup_bahan_id=grup_bahan_id, tanggal=tanggal, resep=resep,
        qty_target=qty_target, tangki_hasil_id=tangki_hasil_id,
        catatan=catatan, dibuat_oleh=user,
    )
    for bahan_id, qty in resep.kebutuhan(qty_target).items():
        SesiInput.objects.create(
            sesi=sesi, bahan_id=bahan_id,
            qty_rencana=qty, qty_aktual=qty,
        )
    return sesi


@transaction.atomic
def mulai_sesi(*, sesi_id, qty_aktual=None):
    """
    Mengambil bahan dari pool. Setelah ini stok pool benar-benar berkurang.

    qty_aktual: {bahan_id: qty} untuk menimpa rencana. Berat timbangan
    jarang persis sama dengan hitungan resep, dan yang dicatat harus
    angka nyata -- bukan angka rencana.
    """
    sesi = SesiProduksi.objects.select_for_update().get(pk=sesi_id)
    if sesi.status != StatusSesi.DRAFT:
        raise ValidationError(f'Sesi sudah {sesi.get_status_display()}.')

    qty_aktual = qty_aktual or {}
    for inp in sesi.input.select_for_update().select_related('bahan'):
        if inp.bahan_id in qty_aktual:
            inp.qty_aktual = Decimal(qty_aktual[inp.bahan_id]).quantize(Q3)
            inp.save(update_fields=['qty_aktual'])

        pakai_dari_pool(
            produk_id=inp.bahan_id,
            grup_bahan_id=sesi.grup_bahan_id,
            qty=inp.qty_aktual,
            tanggal=sesi.tanggal,
            referensi=sesi.nomor,
            idem_key=f'sesi:{sesi.id}:pakai:{inp.bahan_id}',
            tangki_id=inp.tangki_id,
        )

    sesi.status = StatusSesi.BERJALAN
    sesi.save(update_fields=['status'])
    return sesi


@transaction.atomic
def selesaikan_sesi(*, sesi_id, qty_hasil):
    """
    Hasil produksi masuk ke pool, masih tanpa pemilik.

    Susut dicatat apa adanya. Nilai bahan yang hilang TIDAK ikut hilang --
    hasil yang lebih sedikit menyerap seluruh nilai bahan masuk, sehingga
    kerapatan nilai per unit naik. Itu invariant DEM.

    Pemilik hasil ditetapkan belakangan lewat inventory.klaim_hasil().
    """
    sesi = SesiProduksi.objects.select_for_update().get(pk=sesi_id)
    if sesi.status != StatusSesi.BERJALAN:
        raise ValidationError(
            f'Sesi harus berstatus Berjalan, sekarang {sesi.get_status_display()}.'
        )

    qty_hasil = Decimal(qty_hasil).quantize(Q3)
    if qty_hasil <= 0:
        raise ValidationError('Qty hasil harus lebih dari nol.')
    if qty_hasil > sesi.qty_target:
        raise ValidationError(
            f'Hasil {qty_hasil} melebihi target {sesi.qty_target}. '
            f'Periksa timbangan atau resepnya.'
        )

    hasil_ke_pool(
        produk_id=sesi.resep.produk_jadi_id,
        grup_bahan_id=sesi.grup_bahan_id,
        qty=qty_hasil,
        tanggal=sesi.tanggal,
        referensi=sesi.nomor,
        idem_key=f'sesi:{sesi.id}:hasil',
        tangki_id=sesi.tangki_hasil_id,
    )

    sesi.qty_hasil = qty_hasil
    sesi.status = StatusSesi.SELESAI
    sesi.save(update_fields=['qty_hasil', 'status'])
    return sesi


@transaction.atomic
def batalkan_sesi(*, sesi_id, alasan=''):
    """
    Membatalkan sesi DRAFT. Sesi yang sudah BERJALAN tidak bisa dibatalkan
    -- bahan sudah keluar dari pool, dan pengembaliannya harus lewat
    penyesuaian opname supaya tetap ada jejaknya.
    """
    sesi = SesiProduksi.objects.select_for_update().get(pk=sesi_id)
    if sesi.status != StatusSesi.DRAFT:
        raise ValidationError(
            'Bahan sudah keluar dari pool. Selesaikan sesi, '
            'lalu koreksi lewat penyesuaian opname.'
        )
    sesi.status = StatusSesi.BATAL
    sesi.catatan = f'{sesi.catatan}\n[BATAL] {alasan}'.strip()
    sesi.save(update_fields=['status', 'catatan'])
    return sesi


# =========================================================
# LAPORAN
# =========================================================

def ringkasan_sesi(sesi_id):
    """Rincian input, output, dan susut untuk satu sesi."""
    sesi = (SesiProduksi.objects
            .select_related('resep', 'resep__produk_jadi', 'grup_bahan')
            .prefetch_related('input__bahan').get(pk=sesi_id))

    return {
        'nomor': sesi.nomor,
        'tanggal': sesi.tanggal,
        'grup': sesi.grup_bahan.kode,
        'produk': sesi.resep.produk_jadi.kode,
        'target': sesi.qty_target,
        'hasil': sesi.qty_hasil,
        'susut': sesi.susut,
        'rendemen': sesi.rendemen,
        'status': sesi.get_status_display(),
        'input': [
            {
                'bahan': i.bahan.kode,
                'rencana': i.qty_rencana,
                'aktual': i.qty_aktual,
                'selisih': i.selisih,
            }
            for i in sesi.input.all()
        ],
    }
