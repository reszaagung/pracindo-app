"""
Mesin valuasi produksi — produksi/services.py

TIGA LAPIS, TERPISAH DENGAN SENGAJA

    hitung_valuasi()   fungsi MURNI. Tanpa DB, tanpa Django. Diuji tanpa
                       migrasi. Ini satu-satunya tempat rumus valuasi
                       hidup.
    baca_sumber()      jembatan DB -> dict. Membaca SaldoPool dan
                       saldo_batch, mengunci barisnya kalau diminta.
    posting_batch()    orkestrator. Kunci, validasi, valuasi, tulis,
                       periksa invariant.

    Lapisan tengah adalah yang paling mudah dilupakan dan paling sering
    hilang. Tanpa dia, hitung_valuasi() benar tapi tidak pernah bisa
    dipanggil dari HTTP.

URUTAN KUNCI TIDAK BOLEH DIUBAH

    1. seluruh Batch (tujuan + sumber) dalam satu query, ORDER BY id
    2. seluruh SaldoPool, ORDER BY raw_id

    Dua transaksi yang mengunci benda sama dengan urutan berbeda akan
    saling menunggu selamanya. Mengunci batch tujuan lebih dulu -- di
    luar query terurut -- sudah cukup untuk menciptakan deadlock itu.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.apps import apps
from django.conf import settings
from django.db import models, transaction
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import Batch, BatchInputRaw, StatusBatch, TransferWip

D0 = Decimal("0.000")
D0_RP = Decimal("0.00")
TOL_QTY = Decimal("0.001")
TOL_RP = Decimal("0.01")

Q_QTY = Decimal("0.001")
Q_RP = Decimal("0.01")
Q_HARGA = Decimal("0.000001")

F_QTY = DecimalField(max_digits=18, decimal_places=3)
F_RP = DecimalField(max_digits=20, decimal_places=2)


def qty(v):
    return Decimal(v).quantize(Q_QTY, rounding=ROUND_HALF_UP)


def rp(v):
    return Decimal(v).quantize(Q_RP, rounding=ROUND_HALF_UP)


def harga(v):
    return Decimal(v).quantize(Q_HARGA, rounding=ROUND_HALF_UP)


def model_susut_aktif():
    return getattr(settings, "HPP_MODEL_SUSUT", "ABSORPSI")


# ==========================================================
# GALAT — dipetakan ke HTTP oleh views
# ==========================================================

class GalatProduksi(Exception):
    """Induk. `kode` dipakai frontend, `pesan` dipakai manusia."""
    http = 422

    def __init__(self, kode, pesan, field=None):
        self.kode, self.pesan, self.field = kode, pesan, field
        super().__init__(pesan)

    def as_dict(self):
        d = {"kode": self.kode, "pesan": self.pesan}
        if self.field:
            d["field"] = self.field
        return d


class GalatValidasi(GalatProduksi):
    """Payload tidak masuk akal. 422."""
    http = 422


class KonflikSaldo(GalatProduksi):
    """Payload masuk akal, tapi kenyataannya tidak mengizinkan. 409."""
    http = 409


class InvariantMelenceng(GalatProduksi):
    """Rupiah tercipta atau menguap. 500 + rollback."""
    http = 500


# ==========================================================
# KONTRAK KE APP INVENTORY
# ==========================================================
# Dibaca lewat apps.get_model, bukan impor langsung, supaya tidak ada
# lingkaran impor antara produksi dan inventory.

def _SaldoPool():
    return apps.get_model("inventory", "SaldoPool")


def _RawMaterial():
    return apps.get_model("inventory", "RawMaterial")


def _assert_invarian():
    """
    Panggil pemeriksa invariant milik inventory kalau ada.

    Kalau belum ditulis, JANGAN diam-diam melewatinya tanpa jejak --
    tulis peringatan. Invariant yang dilewati tanpa suara adalah cara
    paling rapi untuk kehilangan uang selama berbulan-bulan.
    """
    try:
        from inventory.services import assert_invarian
    except ImportError:
        import warnings
        warnings.warn(
            "inventory.services.assert_invarian() belum ada. Posting batch "
            "berjalan TANPA pemeriksaan konservasi rupiah.",
            RuntimeWarning, stacklevel=2)
        return
    assert_invarian()


# ==========================================================
# SALDO
# ==========================================================

@dataclass(frozen=True)
class SaldoBatch:
    sisa_qty: Decimal
    sisa_nilai: Decimal
    harga_per_kg: Decimal
    kelebihan: bool

    def as_dict(self):
        return {
            "sisa_qty": str(self.sisa_qty),
            "sisa_nilai": str(self.sisa_nilai),
            "harga_per_kg": str(self.harga_per_kg),
            "kelebihan": self.kelebihan,
        }


def saldo_batch(batch) -> SaldoBatch:
    """
    Sisa isi batch. Keluar lewat DUA pintu:

        inventory.Packing    klaim eksternal, nilai keluar sistem
        produksi.TransferWip internal, nilai pindah ke batch lain

    Keduanya sama-sama mengosongkan batch secara fisik; bedanya cuma ke
    mana nilainya pergi. Melewatkan salah satunya adalah bug yang tidak
    akan terlihat sampai seseorang mengambil dari batch yang sudah
    kosong.
    """
    if batch.status != StatusBatch.POSTED:
        return SaldoBatch(D0, D0_RP, batch.harga_hasil_per_kg, False)

    pack = _keluar_packing(batch)
    wip = batch.keluar_wip.filter(
        batch_tujuan__status=StatusBatch.POSTED
    ).aggregate(
        q=Coalesce(Sum("qty_kg"), Value(D0), output_field=F_QTY),
        n=Coalesce(Sum("nilai"), Value(D0_RP), output_field=F_RP),
    )

    keluar_q = pack["q"] + wip["q"]
    sisa_qty = batch.qty_hasil - keluar_q
    sisa_nilai = batch.nilai_hasil - pack["n"] - wip["n"]

    if abs(sisa_qty) < TOL_QTY:
        sisa_qty = D0
    if abs(sisa_nilai) < TOL_RP:
        sisa_nilai = D0_RP
    if sisa_qty == D0:
        sisa_nilai = D0_RP          # R2: habis berarti habis

    return SaldoBatch(
        sisa_qty=qty(sisa_qty),
        sisa_nilai=rp(sisa_nilai),
        harga_per_kg=batch.harga_hasil_per_kg,
        kelebihan=keluar_q > batch.qty_hasil + TOL_QTY,
    )


def _keluar_packing(batch):
    """
    Agregat packing. Ditulis defensif karena app inventory bisa belum
    punya model Packing saat produksi dikembangkan lebih dulu -- dan
    AttributeError di sini akan tampak seperti bug valuasi, bukan seperti
    dependensi yang belum ada.
    """
    rel = getattr(batch, "packing_set", None)
    if rel is None:
        return {"q": D0, "n": D0_RP}
    return rel.filter(status="POSTED").aggregate(
        q=Coalesce(Sum("qty_kg"), Value(D0), output_field=F_QTY),
        n=Coalesce(Sum("nilai_hpp"), Value(D0_RP), output_field=F_RP),
    )


def saldo_tangki(tangki):
    """
    Saldo tangki = JUMLAH SISA TIAP BATCH DI DALAMNYA.

    Tiap batch membawa harganya sendiri. Harga tangki hanyalah rata-rata
    tertimbangnya, dan itu angka TURUNAN yang tidak pernah dipakai untuk
    menilai pengambilan.

    Mengembalikan dict yang SUDAH bisa di-JSON. Versi sebelumnya
    mengembalikan list tuple (Batch, SaldoBatch) dan meledak di
    renderer, bukan di sini -- jauh dari penyebabnya.
    """
    isi = []
    total_qty, total_nilai = D0, D0_RP
    for b in tangki.batch_set.filter(status=StatusBatch.POSTED).order_by("waktu", "id"):
        s = saldo_batch(b)
        if s.sisa_qty <= 0:
            continue
        total_qty += s.sisa_qty
        total_nilai += s.sisa_nilai
        isi.append({
            "id": b.id, "nomor": b.nomor, "nama_hasil": b.nama_hasil,
            "jenis": b.jenis, "waktu": b.waktu.isoformat(),
            **s.as_dict(),
        })

    return {
        "tangki": tangki.kode,
        "qty": str(qty(total_qty)),
        "nilai": str(rp(total_nilai)),
        "harga_rata": str(harga(total_nilai / total_qty) if total_qty > 0 else D0),
        "batches": isi,
        "harga_beragam": len({b["harga_per_kg"] for b in isi}) > 1,
    }


# ==========================================================
# VALUASI — FUNGSI MURNI, TANPA I/O
# ==========================================================

@dataclass(frozen=True)
class BarisValuasi:
    sumber: str          # "RAW" | "WIP"
    id_sumber: int
    label: str
    qty_kg: Decimal
    harga_per_kg: Decimal
    nilai: Decimal
    menghabiskan: bool

    def as_dict(self):
        return {
            "sumber": self.sumber, "id_sumber": self.id_sumber,
            "label": self.label, "qty_kg": str(self.qty_kg),
            "harga_per_kg": str(self.harga_per_kg), "nilai": str(self.nilai),
            "menghabiskan": self.menghabiskan,
        }


@dataclass(frozen=True)
class ValuasiHasil:
    baris: list
    total_qty_input: Decimal
    total_nilai_input: Decimal
    tekor_kg: Decimal
    nilai_susut: Decimal
    qty_hasil: Decimal
    nilai_hasil: Decimal
    harga_masuk_per_kg: Decimal
    harga_hasil_per_kg: Decimal
    peringatan: list


def ambil(q, sisa_qty, sisa_nilai, harga_per_kg):
    """
    ATURAN R2 — penghabisan.

    Kalau pengambilan menghabiskan seluruh sisa (dalam toleransi), yang
    keluar adalah SELURUH sisa nilai. Tanpa ini, pembulatan meninggalkan
    rupiah recehan di wadah yang qty-nya sudah nol -- persis kondisi
    "kosong tapi bernilai" yang akan tertagih ke orang yang salah.

    Identik untuk sumber pool maupun sumber batch. Kalau suatu saat
    keduanya diperlakukan berbeda di sini, salah satunya pasti salah.
    """
    if abs(q - sisa_qty) <= TOL_QTY:
        return rp(sisa_nilai), True
    return rp(q * harga_per_kg), False


def hitung_valuasi(data_raw, data_wip, tekor_kg, model_susut=None):
    """
    Fungsi murni. Tanpa DB, tanpa Django.

    data_raw : [{'id','label','qty','pool_qty','pool_nilai'}]
    data_wip : [{'id','label','qty','sisa_qty','sisa_nilai','harga_per_kg'}]
    """
    model_susut = model_susut or model_susut_aktif()
    total_qty, total_nilai = D0, D0_RP
    baris, peringatan = [], []

    for r in data_raw:                                   # sumber POOL
        q = Decimal(r["qty"])
        p_qty = Decimal(r["pool_qty"])
        p_nilai = Decimal(r["pool_nilai"])
        h = harga(p_nilai / p_qty) if p_qty > 0 else D0   # R1: WAC berjalan
        nilai, habis = ambil(q, p_qty, p_nilai, h)
        baris.append(BarisValuasi("RAW", r["id"], r.get("label", ""),
                                  qty(q), h, nilai, habis))
        if habis:
            peringatan.append(
                f"Pool {r.get('label', r['id'])} akan HABIS. Seluruh sisa "
                f"nilainya ikut keluar.")
        total_qty += q
        total_nilai += nilai

    for w in data_wip:                                   # sumber BATCH
        q = Decimal(w["qty"])
        h = Decimal(w["harga_per_kg"])                   # R3: tidak bergeser
        nilai, habis = ambil(q, Decimal(w["sisa_qty"]),
                             Decimal(w["sisa_nilai"]), h)
        baris.append(BarisValuasi("WIP", w["id"], w.get("label", ""),
                                  qty(q), h, nilai, habis))
        if habis:
            peringatan.append(
                f"Batch {w.get('label', w['id'])} akan HABIS. Seluruh sisa "
                f"nilainya ikut keluar.")
        total_qty += q
        total_nilai += nilai

    tekor_kg = Decimal(tekor_kg or 0)
    if total_qty <= 0:
        raise GalatValidasi("INPUT_KOSONG",
                            "Pilih minimal satu sumber dengan qty > 0.")
    if tekor_kg < 0:
        raise GalatValidasi("TEKOR_NEGATIF",
                            "Tekor tidak boleh negatif.", "tekor_kg")

    qty_hasil = total_qty - tekor_kg
    if qty_hasil <= TOL_QTY:
        # Penjaga pembagian nol. Wajib SEBELUM pembagian di bawah.
        raise GalatValidasi(
            "TEKOR_MELEBIHI_INPUT",
            f"Tekor {tekor_kg:,.3f} Kg menghabiskan seluruh input "
            f"{total_qty:,.3f} Kg. Tidak ada hasil yang bisa dinilai.",
            "tekor_kg")

    harga_masuk = harga(total_nilai / total_qty)

    if model_susut == "ABSORPSI":
        nilai_susut = D0_RP
        nilai_hasil = total_nilai
    else:                                                # LOSS_RECOGNITION
        nilai_susut = rp(tekor_kg * harga_masuk)
        nilai_hasil = rp(total_nilai - nilai_susut)

    return ValuasiHasil(
        baris=baris,
        total_qty_input=qty(total_qty),
        total_nilai_input=rp(total_nilai),
        tekor_kg=qty(tekor_kg),
        nilai_susut=nilai_susut,
        qty_hasil=qty(qty_hasil),
        nilai_hasil=rp(nilai_hasil),
        harga_masuk_per_kg=harga_masuk,
        harga_hasil_per_kg=harga(nilai_hasil / qty_hasil),
        peringatan=peringatan,
    )


# ==========================================================
# JEMBATAN DB -> VALUASI
# ==========================================================

def _agregasi(baris, kunci_id, kunci_qty):
    """
    Gabungkan baris dengan id sama SEBELUM divalidasi.

    Memeriksa tiap baris terhadap saldo penuh secara terpisah meloloskan
    dua baris yang masing-masing 60% dari sisa. Constraint unik di DB
    adalah backstop-nya; ini pertahanan pertamanya.
    """
    hasil = {}
    for b in baris:
        i = b[kunci_id] if isinstance(b, dict) else getattr(b, kunci_id)
        q = b[kunci_qty] if isinstance(b, dict) else getattr(b, kunci_qty)
        hasil[i] = hasil.get(i, D0) + Decimal(q)
    return hasil


def baca_sumber(pakai_raw, pakai_wip, kunci=False, batch_tujuan_id=None):
    """
    Baca saldo nyata dari DB dan bentuk payload untuk hitung_valuasi.

    pakai_raw : {raw_id: qty}
    pakai_wip : {batch_sumber_id: qty}

    kunci=True saat posting: select_for_update dengan urutan tetap.
    kunci=False saat pratinjau: baca biasa, tanpa mengunci apa pun.
    """
    # --- BATCH (tujuan + sumber) dalam satu query terurut ---
    ids_batch = set(pakai_wip)
    if batch_tujuan_id:
        ids_batch.add(batch_tujuan_id)
    qs_batch = Batch.objects.filter(id__in=ids_batch).order_by("id")
    if kunci:
        qs_batch = qs_batch.select_for_update()
    peta_batch = {b.id: b for b in qs_batch}

    # --- POOL terurut raw_id ---
    qs_pool = _SaldoPool().objects.select_related("raw").filter(
        raw_id__in=pakai_raw).order_by("raw_id")
    if kunci:
        qs_pool = qs_pool.select_for_update()
    peta_pool = {p.raw_id: p for p in qs_pool}

    data_raw = []
    for raw_id, q in sorted(pakai_raw.items()):
        pool = peta_pool.get(raw_id)
        if pool is None:
            raise KonflikSaldo(
                "RAW_TIDAK_ADA_DI_POOL",
                f"Raw material id {raw_id} belum pernah masuk pool.",
                f"input_raw[{raw_id}]")
        if q > pool.qty_kg + TOL_QTY:
            raise KonflikSaldo(
                "SALDO_POOL_KURANG",
                f"Pool {pool.raw} sisa {pool.qty_kg:,.3f} Kg. "
                f"Anda memakai {q:,.3f} Kg.",
                f"input_raw[{raw_id}]")
        data_raw.append({
            "id": raw_id, "label": str(pool.raw), "qty": q,
            "pool_qty": pool.qty_kg, "pool_nilai": pool.nilai,
        })

    data_wip = []
    for b_id, q in sorted(pakai_wip.items()):
        sumber = peta_batch.get(b_id)
        if sumber is None:
            raise KonflikSaldo("BATCH_TIDAK_DITEMUKAN",
                               f"Batch sumber id {b_id} tidak ditemukan.",
                               f"input_wip[{b_id}]")
        if sumber.status != StatusBatch.POSTED:
            raise KonflikSaldo(
                "BATCH_BELUM_POSTED",
                f"Batch {sumber.nomor} berstatus {sumber.status}, "
                f"belum bisa ditarik.",
                f"input_wip[{b_id}]")
        if batch_tujuan_id and b_id == batch_tujuan_id:
            raise GalatValidasi("TRANSFER_KE_DIRI_SENDIRI",
                                "Batch tidak bisa menjadi sumbernya sendiri.",
                                f"input_wip[{b_id}]")
        s = saldo_batch(sumber)
        if q > s.sisa_qty + TOL_QTY:
            raise KonflikSaldo(
                "SISA_BATCH_KURANG",
                f"Batch {sumber.nomor} tinggal {s.sisa_qty:,.3f} Kg. "
                f"Anda memakai {q:,.3f} Kg.",
                f"input_wip[{b_id}]")
        data_wip.append({
            "id": b_id,
            "label": f"{sumber.nomor} ({sumber.nama_hasil})",
            "qty": q, "sisa_qty": s.sisa_qty, "sisa_nilai": s.sisa_nilai,
            "harga_per_kg": s.harga_per_kg,
        })

    return data_raw, data_wip, peta_batch, peta_pool


def pratinjau(pakai_raw, pakai_wip, tekor_kg, batch_tujuan_id=None):
    """
    Kalkulator. Tidak menyimpan, tidak mengunci, tidak melempar ke HTTP.

    Mengembalikan (valuasi, None) atau (None, galat). Pratinjau adalah
    kalkulator, bukan gerbang -- galat dikembalikan sebagai data supaya
    frontend bisa menampilkannya sambil operator masih mengetik.
    """
    try:
        data_raw, data_wip, _, _ = baca_sumber(
            pakai_raw, pakai_wip, kunci=False,
            batch_tujuan_id=batch_tujuan_id)
        return hitung_valuasi(data_raw, data_wip, tekor_kg), None
    except GalatProduksi as e:
        return None, e


# ==========================================================
# LELUHUR / KETURUNAN — anti lingkaran
# ==========================================================

def leluhur(batch_id, terlihat=None):
    """Semua batch yang nilainya mengalir MASUK ke batch_id."""
    terlihat = terlihat if terlihat is not None else set()
    for sid in TransferWip.objects.filter(
            batch_tujuan_id=batch_id).values_list("batch_sumber_id", flat=True):
        if sid in terlihat:
            continue
        terlihat.add(sid)
        leluhur(sid, terlihat)
    return terlihat


# ==========================================================
# POSTING
# ==========================================================

@transaction.atomic
def posting_batch(batch, user=None):
    """
    Fase B PRD: kunci -> validasi -> valuasi -> tulis -> periksa.

    SELURUHNYA dalam satu atomic, termasuk pemeriksaan invariant.
    Memanggil pemeriksa di luar blok berarti kesalahan terdeteksi setelah
    ia sudah tersimpan permanen.
    """
    batch = Batch.objects.select_for_update().get(pk=batch.pk)
    if batch.status != StatusBatch.DRAFT:
        raise KonflikSaldo("BATCH_TERKUNCI",
                           f"Batch {batch.nomor} sudah {batch.status}.")

    raws = list(batch.input_raw.all())
    wips = list(batch.input_wip.all())
    if not raws and not wips:
        raise GalatValidasi("INPUT_KOSONG",
                            "Batch tidak punya baris input sama sekali.")

    pakai_raw = _agregasi(raws, "raw_id", "qty_kg")
    pakai_wip = _agregasi(wips, "batch_sumber_id", "qty_kg")

    for sid in pakai_wip:
        if batch.pk in leluhur(sid):
            raise GalatValidasi(
                "LINGKARAN_BLENDING",
                f"Batch sumber id {sid} sudah menerima nilai dari batch ini.",
                f"input_wip[{sid}]")

    data_raw, data_wip, peta_batch, peta_pool = baca_sumber(
        pakai_raw, pakai_wip, kunci=True, batch_tujuan_id=batch.pk)

    v = hitung_valuasi(data_raw, data_wip, batch.tekor_kg)

    # --- TULIS: pool berkurang ---
    for b in v.baris:
        if b.sumber != "RAW":
            continue
        pool = peta_pool[b.id_sumber]
        pool.qty_kg = qty(pool.qty_kg - b.qty_kg)
        pool.nilai = rp(pool.nilai - b.nilai)
        if pool.qty_kg < 0 or pool.nilai < 0:
            raise InvariantMelenceng(
                "POOL_NEGATIF",
                f"Pool {pool.raw} menjadi negatif setelah posting.")
        if pool.qty_kg == 0:
            pool.nilai = D0_RP      
        pool.save(update_fields=["qty_kg", "nilai"])


    nilai_per = {(b.sumber, b.id_sumber): b for b in v.baris}
    for r in raws:
        b = nilai_per[("RAW", r.raw_id)]
        r.harga_per_kg, r.nilai, r.menghabiskan = (b.harga_per_kg, b.nilai,
                                                    b.menghabiskan)
        r.save(update_fields=["harga_per_kg", "nilai", "menghabiskan"])
    for w in wips:
        if w.batch_sumber.grup_bahan_id != batch.grup_bahan_id:
            raise GalatValidasi(
                "GRUP_BERBEDA",
                f"Batch {w.batch_sumber.nomor} milik grup "
                f"{w.batch_sumber.grup_bahan.kode}, tidak bisa masuk ke "
                f"batch grup {batch.grup_bahan.kode}.")


    batch.jenis = "BLENDING" if wips else "MIXING"
    batch.total_qty_input = v.total_qty_input
    batch.total_nilai_input = v.total_nilai_input
    batch.nilai_susut = v.nilai_susut
    batch.qty_hasil = v.qty_hasil
    batch.nilai_hasil = v.nilai_hasil
    batch.harga_masuk_per_kg = v.harga_masuk_per_kg
    batch.harga_hasil_per_kg = v.harga_hasil_per_kg
    batch.status = StatusBatch.POSTED
    batch.posted_by = user if getattr(user, "is_authenticated", False) else None
    batch.posted_at = timezone.now()
    batch.save()

    if abs((batch.nilai_hasil + batch.nilai_susut)
           - batch.total_nilai_input) > TOL_RP:
        raise InvariantMelenceng(
            "P1_KONSERVASI_NILAI",
            f"nilai_hasil + nilai_susut != total_nilai_input pada "
            f"{batch.nomor}.")
    if abs((batch.qty_hasil + batch.tekor_kg)
           - batch.total_qty_input) > TOL_QTY:
        raise InvariantMelenceng(
            "P2_KONSERVASI_MASSA",
            f"qty_hasil + tekor != total_qty_input pada {batch.nomor}.")

    if v.nilai_susut > 0:
        _bebankan_susut(batch)

    _assert_invarian()
    return batch


def _bebankan_susut(batch):
    """
    Mode LOSS_RECOGNITION: susut dibebankan ke pemegang klaim, pro-rata
    saldo positif. Dilakukan lewat inventory, bukan dengan menyentuh
    MutasiKlaim dari sini -- app produksi tidak boleh punya jalan masuk
    ke buku klaim.
    """
    try:
        from inventory.services import bebankan_susut
    except ImportError:
        raise InvariantMelenceng(
            "SUSUT_TIDAK_TERBEBANKAN",
            f"Mode LOSS_RECOGNITION aktif tapi "
            f"inventory.services.bebankan_susut() belum ada. Susut "
            f"Rp{batch.nilai_susut:,.2f} pada {batch.nomor} akan menguap.")
    bebankan_susut(batch)


@transaction.atomic
def void_batch(batch, alasan, user=None):
    """
    Membatalkan batch POSTED dan mengembalikan nilainya.

    HANYA boleh kalau belum ada apa pun yang keluar. Membatalkan batch
    yang isinya sudah ditagihkan berarti menghapus dasar tagihan yang
    sudah terbit.

    Batch sumber pulih dengan sendirinya: saldo_batch() menyaring
    keluar_wip pada batch_tujuan__status=POSTED, jadi begitu status
    berubah jadi VOID, transfernya berhenti dihitung.
    """
    batch = Batch.objects.select_for_update().get(pk=batch.pk)
    if batch.status != StatusBatch.POSTED:
        raise KonflikSaldo("BATCH_BUKAN_POSTED",
                           f"Batch {batch.nomor} berstatus {batch.status}.")
    if not alasan or not alasan.strip():
        raise GalatValidasi("ALASAN_KOSONG", "Alasan VOID wajib diisi.")

    s = saldo_batch(batch)
    if abs(s.sisa_qty - batch.qty_hasil) > TOL_QTY:
        raise KonflikSaldo(
            "BATCH_SUDAH_TERPAKAI",
            f"Batch {batch.nomor} sudah dikeluarkan sebagian "
            f"({batch.qty_hasil - s.sisa_qty:,.3f} Kg). Koreksi lewat batch "
            f"penyesuaian, bukan pembatalan.")
    if batch.nilai_susut > 0:
        raise KonflikSaldo(
            "SUSUT_SUDAH_DIBEBANKAN",
            f"Susut Rp{batch.nilai_susut:,.2f} sudah dibebankan ke pemegang "
            f"klaim. Pembalikannya harus lewat penyesuaian di inventory.")

    ids = sorted({r.raw_id for r in batch.input_raw.all()})
    pools = {p.raw_id: p for p in _SaldoPool().objects
             .select_for_update().filter(raw_id__in=ids).order_by("raw_id")}
    for r in batch.input_raw.all():
        pool = pools[r.raw_id]
        pool.qty_kg = qty(pool.qty_kg + r.qty_kg)
        pool.nilai = rp(pool.nilai + r.nilai)
        pool.save(update_fields=["qty_kg", "nilai"])

    batch.status = StatusBatch.VOID
    batch.catatan = f"{batch.catatan}\n[VOID] {alasan}".strip()
    batch.save(update_fields=["status", "catatan"])

    _assert_invarian()
    return batch


# ==========================================================
# BOM EXPLOSION
# ==========================================================

def komposisi_raw(batch, _memo=None, _jejak=frozenset()):
    """
    Kg raw ASAL yang terkandung dalam SELURUH hasil batch, menembus
    berapa pun lapis blending.

    Konsekuensi yang benar dan sering disalahpahami: hasil 157 Kg bisa
    membawa 165 Kg raw asal. Selisihnya adalah tekor batch-batch
    induknya, yang memang sudah menguap sebelum sampai ke sini.
    """
    _memo = _memo if _memo is not None else {}
    if batch.id in _memo:
        return _memo[batch.id]
    if batch.id in _jejak:
        return {}                                        # lingkaran
    _jejak = _jejak | {batch.id}

    hasil = {}
    for i in batch.input_raw.select_related("raw"):
        k = (i.raw_id, str(i.raw))
        hasil[k] = hasil.get(k, D0) + i.qty_kg
    for t in batch.input_wip.select_related("batch_sumber"):
        for k, q in porsi_raw(t.batch_sumber, t.qty_kg, _memo, _jejak).items():
            hasil[k] = hasil.get(k, D0) + q

    _memo[batch.id] = hasil
    return hasil


def porsi_raw(batch, q, _memo=None, _jejak=frozenset()):
    """Kg raw asal yang terbawa oleh `q` Kg hasil batch ini."""
    if batch.qty_hasil <= 0:
        return {}
    f = Decimal(q) / batch.qty_hasil
    return {k: v * f
            for k, v in komposisi_raw(batch, _memo, _jejak).items()}


def komposisi_json(batch):
    komp = komposisi_raw(batch)
    return {
        "batch": batch.nomor,
        "qty_hasil": str(batch.qty_hasil),
        "total_raw_kg": str(qty(sum(komp.values(), D0))),
        "raw": [{"id": rid, "nama": nama, "qty_kg": str(qty(v))}
                for (rid, nama), v in sorted(komp.items(), key=lambda x: x[0][1])],
    }


# ==========================================================
# DAFTAR BATCH TERSEDIA
# ==========================================================

def get_batch_tersedia(tangki_id=None):
    """Batch POSTED dengan sisa > 0. Dipakai selector sumber di form."""
    qs = Batch.objects.filter(status=StatusBatch.POSTED).select_related("tangki")
    if tangki_id:
        qs = qs.filter(tangki_id=tangki_id)
    hasil = []
    for b in qs.order_by("tangki__kode", "waktu", "id"):
        s = saldo_batch(b)
        if s.sisa_qty <= 0:
            continue
        hasil.append({
            "id": b.id, "nomor": b.nomor, "nama_hasil": b.nama_hasil,
            "tangki_id": b.tangki_id, "tangki": b.tangki.kode,
            "jenis": b.jenis, **s.as_dict(),
        })
    return hasil