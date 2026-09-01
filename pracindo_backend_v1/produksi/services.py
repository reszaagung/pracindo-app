"""
Layanan produksi — produksi/services.py

ALUR: SIMPAN lalu POSTING, terpisah tapi berpasangan

    buat_batch_mixing()/buat_batch_blending()   -> simpan DRAFT (baris BOM/
                                                    sumber ikut tersimpan,
                                                    belum menyentuh pool)
    posting_mixing()/posting_blending()         -> kunci pool/batch sumber,
                                                    hitung nilai, ubah status
                                                    jadi POSTED

    simpan_dan_posting_*()  memanggil keduanya berurutan TANPA @atomic di
    level dirinya sendiri. Ini disengaja: begitu buat_batch_* selesai,
    transaksinya sudah COMMIT sungguhan (bukan savepoint), jadi kalau
    posting_* berikutnya gagal, draft yang sudah tersimpan TIDAK ikut
    rollback. Itulah yang memungkinkan tombol "Posting Ulang" di frontend
    cukup memanggil posting_mixing(batch, user) lagi tanpa user mengulang
    isi form.

KENAPA TIDAK ADA grup_bahan_id DI SINI

Pool sekarang patungan (PoolResource, satu saldo per produk, lintas
entitas/grup). Batch cuma tahu dia menarik qty X dari produk Y di pool
global — bukan grup mana. Siapa berhak atas berapa rupiah baru dihitung
nanti saat Packing menarik dari batch dan membebankan ke SaldoEntitas
(lihat inventory/services.py). Karena itu juga tidak ada pemeriksaan
periode-tutup di sini — periode-tutup itu konsep per-entitas, dan Batch
tidak terikat entitas manapun. Pemeriksaannya baru relevan di titik
klaim (posting_packing), yang sudah ada di inventory/services.py.

SUSUT (SHRINKAGE)

Harga per kg dijaga TETAP sebelum/sesudah susut (lihat _selesaikan_posting):
nilai_hasil = nilai_masuk - nilai_susut, qty_hasil = qty_masuk - susut_kg,
sehingga nilai_hasil/qty_hasil secara aljabar sama dengan nilai_masuk/qty_masuk.
nilai_susut itu lalu didorong ke inventory.services.bebankan_susut() supaya
dibebankan sebagai MutasiKlaim RUGI ke entitas — itulah satu-satunya momen
"perhitungan bisnis" boleh terjadi di luar Packing, karena susut adalah
kehilangan fisik riil yang harus mengurangi total hak entitas juga (kalau
tidak, invariant konservasi rupiah I1 di inventory akan pecah).

CATATAN: bebankan_susut() di inventory/services.py saat ini masih
mengasumsikan batch.grup_bahan_id (yang sudah tidak ada). Sampai itu
diperbaiki, posting_mixing()/posting_blending() dengan susut > 0 akan
gagal di titik itu. Ini pending fix di sisi inventory, sudah diketahui.
"""
from collections import namedtuple
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import (
    Batch, BatchInputRaw, StatusBatch, Tangki, TipeProses, TransferWip,
    harga, qty, rp,
)

D0 = Decimal("0")
D0_QTY = Decimal("0.000")
D0_RP = Decimal("0.00")
TOL_QTY = Decimal("0.001")
TOL_RP = Decimal("0.01")

F_QTY = DecimalField(max_digits=18, decimal_places=3)
F_RP = DecimalField(max_digits=20, decimal_places=2)

SaldoBatch = namedtuple("SaldoBatch", ["sisa_qty", "sisa_nilai", "harga_per_kg"])


class GalatProduksi(ValidationError):
    http = 422


class KonflikBatch(GalatProduksi):
    http = 409


class InvariantMelenceng(GalatProduksi):
    http = 500


# =========================================================
# Pembantu internal
# =========================================================

def _wajib_user(user):
    if not getattr(user, "is_authenticated", False):
        raise GalatProduksi("Operasi ini wajib punya pembuat yang tercatat.")
    return user


def _kunci_tangki(tangki_id):
    try:
        t = Tangki.objects.select_for_update().get(pk=tangki_id)
    except Tangki.DoesNotExist:
        raise GalatProduksi(f"Tangki id {tangki_id} tidak ditemukan.")
    if not t.aktif:
        raise GalatProduksi(f"Tangki {t.kode} nonaktif.")
    return t

@transaction.atomic
def _nomor_batch(jenis, tanggal):
    """
    Penomoran lokal, bukan lewat core.CounterDokumen — Batch tidak punya
    entitas untuk discope-kan ke CounterDokumen.berikutnya(entitas, ...).
    Constraint unik di Batch.nomor jadi jaring pengaman terakhir kalau ada
    tabrakan di detik yang sama.
    """
    prefix = "MIX" if jenis == TipeProses.MIXING else "BLD"
    stempel = tanggal.strftime("%y%m%d")
    awalan = f"{prefix}-{stempel}-"
    terakhir = (Batch.objects
                .select_for_update()
                .filter(nomor__startswith=awalan)
                .order_by("-nomor")
                .first())
    urut = int(terakhir.nomor[len(awalan):]) + 1 if terakhir else 1
    return f"{awalan}{urut:04d}"


def _normalisasi_baris_mixing(baris):
    if not baris:
        raise GalatProduksi("BOM Mixing tidak boleh kosong.")
    kebutuhan = {}
    for b in baris:
        try:
            pid = int(b["produk_id"])
            q = qty(Decimal(str(b["qty_kg"])))
        except (KeyError, TypeError, ValueError, ArithmeticError):
            raise GalatProduksi(f"Baris BOM tidak valid: {b}")
        if q <= 0:
            raise GalatProduksi(f"Qty produk id {pid} harus lebih dari 0.")
        kebutuhan[pid] = kebutuhan.get(pid, D0_QTY) + q
    return kebutuhan


def _normalisasi_baris_blending(baris_sumber):
    if not baris_sumber:
        raise GalatProduksi("Sumber Blending tidak boleh kosong.")
    kebutuhan = {}
    for b in baris_sumber:
        try:
            bid = int(b["batch_sumber_id"])
            q = qty(Decimal(str(b["qty_kg"])))
        except (KeyError, TypeError, ValueError, ArithmeticError):
            raise GalatProduksi(f"Baris sumber blending tidak valid: {b}")
        if q <= 0:
            raise GalatProduksi(f"Qty batch sumber id {bid} harus lebih dari 0.")
        kebutuhan[bid] = kebutuhan.get(bid, D0_QTY) + q
    return kebutuhan


def _selesaikan_posting(batch, total_qty_masuk, total_nilai_masuk, user):
    """
    Dipakai bersama oleh posting_mixing & posting_blending: terapkan susut
    (harga/kg tetap), tutup status batch jadi POSTED, lalu dorong nilai
    susut (kalau ada) ke inventory.services.bebankan_susut().
    """
    if batch.susut_kg > total_qty_masuk + TOL_QTY:
        raise GalatProduksi(
            f"Susut {batch.susut_kg} Kg melebihi total bahan masuk "
            f"{total_qty_masuk} Kg pada {batch.nomor}.")

    harga_masuk = harga(total_nilai_masuk / total_qty_masuk) if total_qty_masuk > 0 else D0
    nilai_susut = rp(harga_masuk * batch.susut_kg) if batch.susut_kg > 0 else D0_RP
    qty_hasil = qty(total_qty_masuk - batch.susut_kg)
    nilai_hasil = rp(total_nilai_masuk - nilai_susut)

    if qty_hasil <= 0:
        raise GalatProduksi(f"Hasil {batch.nomor} nol/negatif setelah susut. Periksa kembali angka susut.")

    batch.qty_hasil = qty_hasil
    batch.nilai_hasil = nilai_hasil
    batch.nilai_susut = nilai_susut
    batch.status = StatusBatch.POSTED
    batch.posted_at = timezone.now()
    batch.save(update_fields=["qty_hasil", "nilai_hasil", "nilai_susut", "status", "posted_at"])

    if nilai_susut > 0:
        from inventory.services import bebankan_susut
        bebankan_susut(batch, user=user)

    from inventory.services import assert_invarian
    assert_invarian()

    return batch


# =========================================================
# Mixing
# =========================================================

@transaction.atomic
def buat_batch_mixing(*, nama_hasil, tangki_id, baris, susut_kg=None, tanggal=None, user=None):
    user = _wajib_user(user)
    tangki = _kunci_tangki(tangki_id)
    kebutuhan = _normalisasi_baris_mixing(baris)

    susut_kg = qty(susut_kg) if susut_kg is not None else D0_QTY
    if susut_kg < 0:
        raise GalatProduksi("Susut tidak boleh negatif.")

    tgl = tanggal or timezone.localdate()
    batch = Batch.objects.create(
        nomor=_nomor_batch(TipeProses.MIXING, tgl),
        jenis=TipeProses.MIXING,
        nama_hasil=nama_hasil,
        tangki=tangki,
        susut_kg=susut_kg,
        tanggal=tgl,
        status=StatusBatch.DRAFT,
        dibuat_oleh=user,
    )
    BatchInputRaw.objects.bulk_create([
        BatchInputRaw(batch=batch, produk_id=pid, qty_kg=q)
        for pid, q in kebutuhan.items()
    ])
    return batch


@transaction.atomic
def posting_mixing(batch, user=None):
    user = _wajib_user(user)
    batch = Batch.objects.select_for_update().get(pk=batch.pk)

    if batch.jenis != TipeProses.MIXING:
        raise GalatProduksi(f"{batch.nomor} bukan batch Mixing.")
    if batch.status != StatusBatch.DRAFT:
        raise KonflikBatch(f"Batch {batch.nomor} sudah {batch.status}.")

    baris = list(batch.input_raw.order_by("produk_id"))
    if not baris:
        raise GalatProduksi(f"Batch {batch.nomor} tidak punya baris BOM.")

    from inventory.models import PoolResource
    produk_ids = sorted({b.produk_id for b in baris})
    pools = {p.produk_id: p for p in PoolResource.objects
             .select_for_update()
             .select_related("produk")
             .filter(produk_id__in=produk_ids)}

    total_qty_masuk, total_nilai_masuk = D0_QTY, D0_RP
    perubahan = []

    for b in baris:
        pool = pools.get(b.produk_id)
        tersedia_qty = pool.qty_kg if pool else D0_QTY
        tersedia_nilai = pool.nilai if pool else D0_RP

        if b.qty_kg > tersedia_qty + TOL_QTY:
            label = pool.produk.kode if pool else f"id {b.produk_id}"
            raise KonflikBatch(
                f"Pool {label} tinggal {tersedia_qty} Kg, batch {batch.nomor} butuh {b.qty_kg} Kg.")

        habis = abs(b.qty_kg - tersedia_qty) <= TOL_QTY
        nilai_tarik = tersedia_nilai if habis else rp(pool.harga_rata * b.qty_kg)
        harga_snapshot = harga(nilai_tarik / b.qty_kg) if b.qty_kg > 0 else D0

        pool.qty_kg = qty(pool.qty_kg - b.qty_kg)
        pool.nilai = rp(pool.nilai - nilai_tarik)
        if pool.qty_kg <= 0:
            pool.qty_kg = D0_QTY
            pool.nilai = D0_RP
        pool.save(update_fields=["qty_kg", "nilai"])

        b.harga_per_kg = harga_snapshot
        b.nilai = nilai_tarik
        perubahan.append(b)

        total_qty_masuk = qty(total_qty_masuk + b.qty_kg)
        total_nilai_masuk = rp(total_nilai_masuk + nilai_tarik)

    BatchInputRaw.objects.bulk_update(perubahan, ["harga_per_kg", "nilai"])

    return _selesaikan_posting(batch, total_qty_masuk, total_nilai_masuk, user)


def simpan_dan_posting_mixing(*, nama_hasil, tangki_id, baris, susut_kg=None, tanggal=None, user=None):
    """'Simpan & Posting' — kalau posting gagal, batch DRAFT tetap ada.
    Retry lewat posting_mixing(batch, user) = 'Posting Ulang'."""
    batch = buat_batch_mixing(nama_hasil=nama_hasil, tangki_id=tangki_id, baris=baris,
                               susut_kg=susut_kg, tanggal=tanggal, user=user)
    posting_mixing(batch, user=user)
    return batch


# =========================================================
# Blending
# =========================================================

@transaction.atomic
def buat_batch_blending(*, nama_hasil, tangki_id, baris_sumber, susut_kg=None, tanggal=None, user=None):
    user = _wajib_user(user)
    tangki = _kunci_tangki(tangki_id)
    kebutuhan = _normalisasi_baris_blending(baris_sumber)

    susut_kg = qty(susut_kg) if susut_kg is not None else D0_QTY
    if susut_kg < 0:
        raise GalatProduksi("Susut tidak boleh negatif.")

    jumlah_ditemukan = Batch.objects.filter(pk__in=kebutuhan.keys(), status=StatusBatch.POSTED).count()
    if jumlah_ditemukan != len(kebutuhan):
        raise GalatProduksi("Salah satu batch sumber tidak ditemukan atau belum POSTED.")

    tgl = tanggal or timezone.localdate()
    batch = Batch.objects.create(
        nomor=_nomor_batch(TipeProses.BLENDING, tgl),
        jenis=TipeProses.BLENDING,
        nama_hasil=nama_hasil,
        tangki=tangki,
        susut_kg=susut_kg,
        tanggal=tgl,
        status=StatusBatch.DRAFT,
        dibuat_oleh=user,
    )
    TransferWip.objects.bulk_create([
        TransferWip(batch_sumber_id=bid, batch_tujuan=batch, qty_kg=q, dibuat_oleh=user)
        for bid, q in kebutuhan.items()
    ])
    return batch


@transaction.atomic
def posting_blending(batch, user=None):
    user = _wajib_user(user)
    batch = Batch.objects.select_for_update().get(pk=batch.pk)

    if batch.jenis != TipeProses.BLENDING:
        raise GalatProduksi(f"{batch.nomor} bukan batch Blending.")
    if batch.status != StatusBatch.DRAFT:
        raise KonflikBatch(f"Batch {batch.nomor} sudah {batch.status}.")

    baris = list(batch.transfer_masuk.select_related("batch_sumber").order_by("batch_sumber_id"))
    if not baris:
        raise GalatProduksi(f"Batch {batch.nomor} tidak punya sumber blending.")

    sumber_ids = sorted({t.batch_sumber_id for t in baris})
    if batch.pk in sumber_ids:
        raise GalatProduksi(f"Batch {batch.nomor} tidak bisa mengambil dari dirinya sendiri.")

    sumber_terkunci = {b.pk: b for b in Batch.objects.select_for_update().filter(pk__in=sumber_ids).order_by("pk")}

    total_qty_masuk, total_nilai_masuk = D0_QTY, D0_RP
    perubahan = []

    for t in baris:
        sumber = sumber_terkunci.get(t.batch_sumber_id)
        if sumber is None or sumber.status != StatusBatch.POSTED:
            raise KonflikBatch(f"Batch sumber id {t.batch_sumber_id} tidak POSTED, tidak bisa dipakai untuk blending.")

        s = saldo_batch(sumber)
        if t.qty_kg > s.sisa_qty + TOL_QTY:
            raise KonflikBatch(
                f"Batch {sumber.nomor} tinggal {s.sisa_qty} Kg, blending {batch.nomor} butuh {t.qty_kg} Kg.")

        habis = abs(t.qty_kg - s.sisa_qty) <= TOL_QTY
        nilai_tarik = s.sisa_nilai if habis else rp(s.harga_per_kg * t.qty_kg)

        t.nilai = nilai_tarik
        perubahan.append(t)

        total_qty_masuk = qty(total_qty_masuk + t.qty_kg)
        total_nilai_masuk = rp(total_nilai_masuk + nilai_tarik)

    TransferWip.objects.bulk_update(perubahan, ["nilai"])

    return _selesaikan_posting(batch, total_qty_masuk, total_nilai_masuk, user)


def simpan_dan_posting_blending(*, nama_hasil, tangki_id, baris_sumber, susut_kg=None, tanggal=None, user=None):
    batch = buat_batch_blending(nama_hasil=nama_hasil, tangki_id=tangki_id, baris_sumber=baris_sumber,
                                 susut_kg=susut_kg, tanggal=tanggal, user=user)
    posting_blending(batch, user=user)
    return batch


# =========================================================
# Query: dipakai inventory/services.py (posting_packing, get_kartu_stok)
# =========================================================

def saldo_batch(batch):
    """Sisa qty/nilai/harga-per-kg batch yang belum ditarik Packing atau Blending lain."""
    from inventory.models import Packing, StatusDokumen

    if batch.status != StatusBatch.POSTED:
        return SaldoBatch(sisa_qty=D0_QTY, sisa_nilai=D0_RP, harga_per_kg=D0)

    agg_pack = Packing.objects.filter(batch=batch, status=StatusDokumen.POSTED).aggregate(
        q=Coalesce(Sum("qty_kg"), Value(D0_QTY), output_field=F_QTY),
        n=Coalesce(Sum("cost_nom"), Value(D0_RP), output_field=F_RP),
    )
    agg_wip = TransferWip.objects.filter(batch_sumber=batch).aggregate(
        q=Coalesce(Sum("qty_kg"), Value(D0_QTY), output_field=F_QTY),
        n=Coalesce(Sum("nilai"), Value(D0_RP), output_field=F_RP),
    )

    sisa_qty = qty(batch.qty_hasil - agg_pack["q"] - agg_wip["q"])
    sisa_nilai = rp(batch.nilai_hasil - agg_pack["n"] - agg_wip["n"])
    if sisa_qty < 0:
        sisa_qty = D0_QTY
    if sisa_nilai < 0:
        sisa_nilai = D0_RP

    harga_pk = harga(sisa_nilai / sisa_qty) if sisa_qty > 0 else D0
    return SaldoBatch(sisa_qty=sisa_qty, sisa_nilai=sisa_nilai, harga_per_kg=harga_pk)


def porsi_raw(batch, sisa_qty, _depth=0):
    """
    {produk_id: qty_kg} penyusun `sisa_qty` dari batch ini, ditelusuri
    sampai bahan baku aslinya. MIXING dibaca langsung dari BatchInputRaw;
    BLENDING direkursikan lewat TransferWip ke tiap batch sumbernya.
    """
    if _depth > 25:
        raise InvariantMelenceng(f"Rantai blending {batch.nomor} terlalu dalam (>25). Kemungkinan siklus data.")
    if batch.qty_hasil <= 0 or sisa_qty <= 0:
        return {}

    rasio = sisa_qty / batch.qty_hasil
    hasil = {}

    if batch.jenis == TipeProses.MIXING:
        for b in batch.input_raw.all():
            hasil[b.produk_id] = hasil.get(b.produk_id, D0_QTY) + qty(b.qty_kg * rasio)
        return hasil

    for t in batch.transfer_masuk.select_related("batch_sumber").all():
        sub = porsi_raw(t.batch_sumber, qty(t.qty_kg * rasio), _depth=_depth + 1)
        for pid, q in sub.items():
            hasil[pid] = hasil.get(pid, D0_QTY) + q
    return hasil


# =========================================================
# Pratinjau — buat "Projected Output" / "WIP Cost" live di form sebelum posting
# =========================================================

def pratinjau_mixing(baris, susut_kg=None):
    from inventory.models import PoolResource

    try:
        kebutuhan = _normalisasi_baris_mixing(baris)
    except GalatProduksi as e:
        return {"valid": False, "kode": "BOM_TIDAK_VALID", "pesan": str(e)}

    pools = {p.produk_id: p for p in PoolResource.objects
             .select_related("produk").filter(produk_id__in=kebutuhan.keys())}

    rincian, total_qty, total_nilai, peringatan = [], D0_QTY, D0_RP, []
    for pid, q in kebutuhan.items():
        pool = pools.get(pid)
        tersedia = pool.qty_kg if pool else D0_QTY
        harga_pk = pool.harga_rata if pool else D0
        cukup = q <= tersedia + TOL_QTY
        if not cukup:
            label = pool.produk.kode if pool else f"id {pid}"
            peringatan.append(f"Pool {label} tinggal {tersedia} Kg, diminta {q} Kg.")

        nilai_baris = rp(harga_pk * q)
        rincian.append({
            "produk_id": pid,
            "produk_kode": pool.produk.kode if pool else None,
            "qty_kg": str(q),
            "pool_balance": str(tersedia),
            "harga_per_kg": str(harga_pk),
            "subtotal": str(nilai_baris),
            "cukup": cukup,
        })
        total_qty = qty(total_qty + q)
        total_nilai = rp(total_nilai + nilai_baris)

    susut_kg = qty(susut_kg) if susut_kg is not None else D0_QTY
    if susut_kg > total_qty:
        peringatan.append(f"Susut {susut_kg} Kg melebihi total bahan {total_qty} Kg.")

    proyeksi_qty = qty(total_qty - susut_kg) if susut_kg <= total_qty else D0_QTY
    wip_cost = harga(total_nilai / total_qty) if total_qty > 0 else D0

    return {
        "valid": not peringatan,
        "rincian": rincian,
        "total_qty_masuk": str(total_qty),
        "total_nilai_masuk": str(total_nilai),
        "susut_kg": str(susut_kg),
        "proyeksi_output_kg": str(proyeksi_qty),
        "wip_cost_per_kg": str(wip_cost),
        "peringatan": peringatan,
    }


def pratinjau_blending(baris_sumber, susut_kg=None):
    try:
        kebutuhan = _normalisasi_baris_blending(baris_sumber)
    except GalatProduksi as e:
        return {"valid": False, "kode": "SUMBER_TIDAK_VALID", "pesan": str(e)}

    batch_map = {b.pk: b for b in Batch.objects.filter(pk__in=kebutuhan.keys())}

    rincian, total_qty, total_nilai, peringatan = [], D0_QTY, D0_RP, []
    for bid, q in kebutuhan.items():
        sumber = batch_map.get(bid)
        if sumber is None or sumber.status != StatusBatch.POSTED:
            peringatan.append(f"Batch sumber id {bid} tidak ditemukan atau belum POSTED.")
            rincian.append({"batch_sumber_id": bid, "batch_nomor": None, "qty_kg": str(q), "cukup": False})
            continue

        s = saldo_batch(sumber)
        cukup = q <= s.sisa_qty + TOL_QTY
        if not cukup:
            peringatan.append(f"Batch {sumber.nomor} tinggal {s.sisa_qty} Kg, diminta {q} Kg.")

        nilai_baris = rp(s.harga_per_kg * q)
        rincian.append({
            "batch_sumber_id": bid,
            "batch_nomor": sumber.nomor,
            "qty_kg": str(q),
            "sisa_batch": str(s.sisa_qty),
            "harga_per_kg": str(s.harga_per_kg),
            "subtotal": str(nilai_baris),
            "cukup": cukup,
        })
        total_qty = qty(total_qty + q)
        total_nilai = rp(total_nilai + nilai_baris)

    susut_kg = qty(susut_kg) if susut_kg is not None else D0_QTY
    if susut_kg > total_qty:
        peringatan.append(f"Susut {susut_kg} Kg melebihi total bahan {total_qty} Kg.")

    proyeksi_qty = qty(total_qty - susut_kg) if susut_kg <= total_qty else D0_QTY
    wip_cost = harga(total_nilai / total_qty) if total_qty > 0 else D0

    return {
        "valid": not peringatan,
        "rincian": rincian,
        "total_qty_masuk": str(total_qty),
        "total_nilai_masuk": str(total_nilai),
        "susut_kg": str(susut_kg),
        "proyeksi_output_kg": str(proyeksi_qty),
        "wip_cost_per_kg": str(wip_cost),
        "peringatan": peringatan,
    }