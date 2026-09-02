from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.db.models import DecimalField, Sum, Value, Q
from django.db.models.functions import Coalesce
from django.utils import timezone

# Impor Model Produksi
from .models import Batch, BatchInputRaw, Tangki, TransferWip, TipeProses

# Impor Lintas-Aplikasi (Inventory & Core)
from inventory.models import (
    MutasiKlaim, Packing, Pembelian, SaldoEntitas,
    StatusDokumen, SumberPembelian, TipeMutasi, PoolResource, PoolKemasan
)
from core.models import CounterDokumen, PeriodeAkuntansi

# ==========================================
# KONSTANTA & EXCEPTION
# ==========================================
D0 = Decimal("0")
D0_RP = Decimal("0.00")
D0_QTY = Decimal("0.000")
TOL_QTY = Decimal("0.001")
TOL_RP = Decimal("0.01")
Q_RP = Decimal("0.01")
Q_QTY = Decimal("0.001")
Q_HARGA = Decimal("0.000001")
F_RP = DecimalField(max_digits=20, decimal_places=2)

class GalatInventory(ValidationError):
    http = 422

class KonflikSaldo(GalatInventory):
    http = 409

class InvariantMelenceng(GalatInventory):
    http = 500

class GalatProduksi(ValidationError):
    http = 422

class KonflikBatch(GalatProduksi):
    http = 409


def rp(x):
    return Decimal(str(x)).quantize(Q_RP, rounding=ROUND_HALF_UP)

def qty(x):
    return Decimal(str(x)).quantize(Q_QTY, rounding=ROUND_HALF_UP)

def harga(x):
    return Decimal(str(x)).quantize(Q_HARGA, rounding=ROUND_HALF_UP)

def _wajib_user(user):
    if not getattr(user, "is_authenticated", False):
        raise GalatInventory("Operasi ini wajib punya pembuat yang tercatat.")
    return user

def _pastikan_periode_terbuka(entitas, tanggal):
    if PeriodeAkuntansi.objects.filter(entitas=entitas, tahun=tanggal.year, bulan=tanggal.month, ditutup=True).exists():
        raise GalatInventory(f"Periode {tanggal.month:02d}/{tanggal.year} untuk {entitas.kode} sudah ditutup.")

def _kunci_saldo(entitas_id):
    try:
        return SaldoEntitas.objects.select_for_update().get(entitas_id=entitas_id)
    except SaldoEntitas.DoesNotExist:
        raise InvariantMelenceng(f"Entitas id {entitas_id} tidak punya baris SaldoEntitas.")


# ==========================================
# MANAJEMEN POOL RESOURCE (BAHAN BAKU & KEMASAN)
# ==========================================
def tambah_ke_pool_resource(produk_id, q, nilai_tambahan):
    pool, _ = PoolResource.objects.select_for_update().get_or_create(produk_id=produk_id)
    pool.qty_kg = qty(pool.qty_kg + q)
    pool.nilai = rp(pool.nilai + nilai_tambahan)
    pool.save(update_fields=["qty_kg", "nilai"])

def potong_dari_pool_resource(produk_id, q, nilai_potongan):
    try:
        pool = PoolResource.objects.select_for_update().get(produk_id=produk_id)
    except PoolResource.DoesNotExist:
        raise InvariantMelenceng(f"PoolResource produk ID {produk_id} tidak ditemukan.")
    
    pool.qty_kg = qty(pool.qty_kg - q)
    pool.nilai = rp(pool.nilai - nilai_potongan)
    
    if pool.qty_kg < 0 or pool.nilai < 0:
        raise InvariantMelenceng("Pengurangan PoolResource menyebabkan nilai negatif.")
    if pool.qty_kg == 0:
        pool.nilai = D0_RP   
    pool.save(update_fields=["qty_kg", "nilai"])

def tambah_ke_pool_kemasan(produk_id, q_unit, nilai_tambahan):
    pool, _ = PoolKemasan.objects.select_for_update().get_or_create(produk_id=produk_id)
    pool.qty_unit = pool.qty_unit + int(q_unit)
    pool.nilai = rp(pool.nilai + nilai_tambahan)
    pool.save(update_fields=["qty_unit", "nilai"])

def potong_dari_pool_kemasan(produk_id, q_unit, nilai_potongan):
    try:
        pool = PoolKemasan.objects.select_for_update().get(produk_id=produk_id)
    except PoolKemasan.DoesNotExist:
        raise InvariantMelenceng(f"PoolKemasan produk ID {produk_id} tidak ditemukan.")
    
    q_unit_int = int(q_unit)
    pool.qty_unit = pool.qty_unit - q_unit_int
    pool.nilai = rp(pool.nilai - nilai_potongan)
    
    if pool.qty_unit < 0 or pool.nilai < 0:
        raise InvariantMelenceng("Pengurangan PoolKemasan menyebabkan nilai negatif.")
    if pool.qty_unit == 0:
        pool.nilai = D0_RP   
    pool.save(update_fields=["qty_unit", "nilai"])


# ==========================================
# GENERATOR ID BATCH (MIX-DDMMYY-XXXX)
# ==========================================
def _nomor_batch(jenis, tanggal=None):
    if tanggal is None:
        tanggal = timezone.localdate()
        
    awalan = "MIX" if jenis == "MIXING" else "BLD"
    tgl_str = tanggal.strftime("%d%m%y")
    
    last_batch = Batch.objects.filter(jenis=jenis, tanggal=tanggal).order_by("-id").first()
    urut = 1
    if last_batch and last_batch.nomor:
        parts = last_batch.nomor.split("-")
        if len(parts) == 3:
            try:
                urut = int(parts[2]) + 1
            except ValueError:
                pass
                
    return f"{awalan}-{tgl_str}-{urut:04d}"


# ==========================================
# KALKULASI SALDO BATCH
# ==========================================
class SaldoBatchData:
    def __init__(self, sisa_qty, sisa_nilai, harga_per_kg):
        self.sisa_qty = sisa_qty
        self.sisa_nilai = sisa_nilai
        self.harga_per_kg = harga_per_kg

def saldo_batch(batch):
    if not batch.posted_at or batch.qty_hasil <= 0:
        return SaldoBatchData(D0_QTY, D0_RP, D0_RP)
        
    transfer_keluar = sum((t.qty_kg for t in batch.transfer_keluar.all()), D0_QTY)
    packing_keluar = sum((p.qty_kg for p in Packing.objects.filter(batch_id=batch.id, status="POSTED")), D0_QTY)
    
    sisa_qty = qty(batch.qty_hasil - transfer_keluar - packing_keluar)
    if sisa_qty <= 0:
        return SaldoBatchData(D0_QTY, D0_RP, batch.harga_per_kg)
        
    sisa_nilai = rp(sisa_qty * batch.harga_per_kg)
    return SaldoBatchData(sisa_qty, sisa_nilai, batch.harga_per_kg)


# ==========================================
# PRATINJAU BATCH PRODUKSI
# ==========================================
def pratinjau_mixing(baris, susut_kg):
    total_qty_masuk = D0_QTY
    total_nilai_masuk = D0_RP
    rincian = []
    valid = True
    peringatan = []
    susut = qty(susut_kg or 0)

    for b in baris:
        q = qty(b.get("qty_kg", 0))
        if q <= 0: continue
        try:
            pool = PoolResource.objects.get(produk_id=b["raw"])
            if pool.qty_kg < q:
                valid = False
                peringatan.append(f"Saldo pool {pool.produk.nama} tidak cukup. Diminta {q}, tersedia {pool.qty_kg}.")
            h = pool.harga_rata
            sub = rp(q * h)
        except PoolResource.DoesNotExist:
            valid = False
            peringatan.append(f"Bahan ID {b.get('raw')} tidak ada di pool.")
            h = D0_RP
            sub = D0_RP
            pool = None

        total_qty_masuk += q
        total_nilai_masuk += sub
        rincian.append({
            "produk_kode": pool.produk.kode if pool else str(b.get('raw')),
            "qty_kg": str(q),
            "harga_per_kg": str(h),
            "subtotal": str(sub),
            "cukup": (pool.qty_kg >= q) if pool else False
        })

    proyeksi_output = total_qty_masuk - susut
    if proyeksi_output <= 0:
        valid = False
        peringatan.append("Yield output tidak boleh nol atau negatif setelah dikurangi susut.")

    cost_per_kg = rp(total_nilai_masuk / proyeksi_output) if proyeksi_output > 0 else D0_RP

    return {
        "valid": valid,
        "rincian": rincian,
        "peringatan": peringatan,
        "total_qty_masuk": str(total_qty_masuk),
        "total_nilai_masuk": str(total_nilai_masuk),
        "susut_kg": str(susut),
        "proyeksi_output_kg": str(proyeksi_output),
        "wip_cost_per_kg": str(cost_per_kg)
    }

def pratinjau_blending(baris_sumber, susut_kg):
    total_qty_masuk = D0_QTY
    total_nilai_masuk = D0_RP
    rincian = []
    valid = True
    peringatan = []
    susut = qty(susut_kg or 0)

    for b in baris_sumber:
        q = qty(b.get("qty_kg", 0))
        if q <= 0: continue
        try:
            batch_sumber = Batch.objects.get(nomor=b["batch"])
            s = saldo_batch(batch_sumber)
            if s.sisa_qty < q:
                valid = False
                peringatan.append(f"Saldo batch {batch_sumber.nomor} kurang. Diminta {q}, tersedia {s.sisa_qty}.")
            h = s.harga_per_kg
            sub = rp(q * h)
        except Batch.DoesNotExist:
            valid = False
            peringatan.append(f"Batch {b.get('batch')} tidak ditemukan.")
            h = D0_RP
            sub = D0_RP
            batch_sumber = None

        total_qty_masuk += q
        total_nilai_masuk += sub
        rincian.append({
            "batch_nomor": batch_sumber.nomor if batch_sumber else str(b.get('batch')),
            "qty_kg": str(q),
            "harga_per_kg": str(h),
            "subtotal": str(sub),
            "cukup": (s.sisa_qty >= q) if batch_sumber else False
        })

    proyeksi_output = total_qty_masuk - susut
    if proyeksi_output <= 0:
        valid = False
        peringatan.append("Yield output tidak boleh nol atau negatif.")

    cost_per_kg = rp(total_nilai_masuk / proyeksi_output) if proyeksi_output > 0 else D0_RP

    return {
        "valid": valid,
        "rincian": rincian,
        "peringatan": peringatan,
        "total_qty_masuk": str(total_qty_masuk),
        "total_nilai_masuk": str(total_nilai_masuk),
        "susut_kg": str(susut),
        "proyeksi_output_kg": str(proyeksi_output),
        "wip_cost_per_kg": str(cost_per_kg)
    }


# ==========================================
# POSTING BATCH PRODUKSI
# ==========================================
@transaction.atomic
def simpan_dan_posting_mixing(nama_hasil, tangki_id, baris, susut_kg=0, tanggal=None, user=None, nomor_custom=None):
    user = _wajib_user(user)
    tanggal = tanggal or timezone.localdate()
    susut = qty(susut_kg or 0)
    nomor = nomor_custom or _nomor_batch("MIXING", tanggal)
    
    cek = pratinjau_mixing(baris, susut)
    if not cek["valid"]:
        raise GalatProduksi(" | ".join(cek["peringatan"]))
        
    tangki = Tangki.objects.get(pk=tangki_id)
    batch = Batch.objects.create(
        nomor=nomor,
        jenis="MIXING",
        nama_hasil=nama_hasil,
        tangki=tangki,
        susut_kg=susut,
        tanggal=tanggal,
        dibuat_oleh=user,
    )
    
    for b in baris:
        q = qty(b.get("qty_kg", 0))
        if q <= 0: continue
        pool = PoolResource.objects.get(produk_id=b["raw"])
        BatchInputRaw.objects.create(
            batch=batch,
            produk_id=b["raw"],
            qty_kg=q,
            harga_per_kg=pool.harga_rata,
            nilai=rp(q * pool.harga_rata)
        )
        
    return posting_mixing(batch, user)


@transaction.atomic
def posting_mixing(batch, user=None):
    user = _wajib_user(user)
    if batch.posted_at:
        raise KonflikBatch(f"Batch {batch.nomor} sudah di-posting.")
        
    total_qty_masuk = D0_QTY
    total_nilai_masuk = D0_RP
    
    for raw in batch.input_raw.all():
        potong_dari_pool_resource(raw.produk_id, raw.qty_kg, raw.nilai)
        total_qty_masuk += raw.qty_kg
        total_nilai_masuk += raw.nilai
        
    qty_output = total_qty_masuk - batch.susut_kg
    if qty_output <= 0:
        raise GalatProduksi("Yield output <= 0 setelah dipotong susut.")
        
    batch.qty_hasil = qty_output
    batch.nilai_hasil = total_nilai_masuk
    batch.posted_at = timezone.now()
    batch.save()
    return batch


@transaction.atomic
def simpan_dan_posting_blending(nama_hasil, tangki_id, baris_sumber, susut_kg=0, tanggal=None, user=None, nomor_custom=None):
    user = _wajib_user(user)
    tanggal = tanggal or timezone.localdate()
    susut = qty(susut_kg or 0)
    nomor = nomor_custom or _nomor_batch("BLENDING", tanggal)
    
    cek = pratinjau_blending(baris_sumber, susut)
    if not cek["valid"]:
        raise GalatProduksi(" | ".join(cek["peringatan"]))
        
    tangki = Tangki.objects.get(pk=tangki_id)
    batch = Batch.objects.create(
        nomor=nomor,
        jenis="BLENDING",
        nama_hasil=nama_hasil,
        tangki=tangki,
        susut_kg=susut,
        tanggal=tanggal,
        dibuat_oleh=user,
    )
    
    for b in baris_sumber:
        q = qty(b.get("qty_kg", 0))
        if q <= 0: continue
        batch_sumber = Batch.objects.get(nomor=b["batch"])
        s = saldo_batch(batch_sumber)
        TransferWip.objects.create(
            batch_sumber=batch_sumber,
            batch_tujuan=batch,
            qty_kg=q,
            nilai=rp(q * s.harga_per_kg),
            dibuat_oleh=user
        )
        
    return posting_blending(batch, user)


@transaction.atomic
def posting_blending(batch, user=None):
    user = _wajib_user(user)
    if batch.posted_at:
        raise KonflikBatch(f"Batch {batch.nomor} sudah di-posting.")
        
    total_qty_masuk = D0_QTY
    total_nilai_masuk = D0_RP
    
    for transfer in batch.transfer_masuk.all():
        total_qty_masuk += transfer.qty_kg
        total_nilai_masuk += transfer.nilai
        
    qty_output = total_qty_masuk - batch.susut_kg
    if qty_output <= 0:
        raise GalatProduksi("Yield output <= 0 setelah dipotong susut.")
        
    batch.qty_hasil = qty_output
    batch.nilai_hasil = total_nilai_masuk
    batch.posted_at = timezone.now()
    batch.save()
    return batch


@transaction.atomic
def hapus_batch_dan_kembalikan_stok(batch_id, user=None):
    raise GalatProduksi("Operasi penghapusan batch produksi dilarang. Lakukan jurnal pembalik jika terjadi kesalahan.")


# ==========================================
# FUNGSI PEMBELIAN & PACKING LAMA
# ==========================================
@transaction.atomic
def posting_pembelian(pembelian, user=None):
    user = _wajib_user(user)
    pembelian = Pembelian.objects.select_for_update().get(pk=pembelian.pk)

    if pembelian.sumber == SumberPembelian.PENERIMAAN:
        raise KonflikSaldo(f"{pembelian.nomor} terbit dari penerimaan gudang dan sudah POSTED sejak lahir.")
    if pembelian.status != StatusDokumen.DRAFT:
        raise KonflikSaldo(f"Pembelian {pembelian.nomor} sudah {pembelian.status}.")
    if not pembelian.entitas.aktif:
        raise GalatInventory(f"Entitas {pembelian.entitas.kode} nonaktif dan tidak bisa menyetor.")

    _pastikan_periode_terbuka(pembelian.entitas, pembelian.tanggal)
    nilai = rp(pembelian.qty_kg * pembelian.harga_per_kg)
    pembelian.nilai = nilai

    if pembelian.produk.jenis == 'KEMASAN':
        tambah_ke_pool_kemasan(pembelian.produk_id, pembelian.qty_kg, nilai)
        keterangan_mutasi = f"PO Kemasan {pembelian.nomor} - {pembelian.produk}"
    else:
        tambah_ke_pool_resource(pembelian.produk_id, pembelian.qty_kg, nilai)
        keterangan_mutasi = f"{pembelian.nomor} - {pembelian.produk}"

    MutasiKlaim.objects.create(
        entitas=pembelian.entitas, grup_bahan=pembelian.grup_bahan,
        tipe=TipeMutasi.SETOR, arah=1, qty_kg=pembelian.qty_kg, nilai=nilai,
        ref_type="Pembelian", ref_id=pembelian.id,
        keterangan=keterangan_mutasi,
        waktu=pembelian.waktu, dibuat_oleh=user)

    se = _kunci_saldo(pembelian.entitas_id)
    se.total_setor = rp(se.total_setor + nilai)
    se.qty_setor = qty(se.qty_setor + pembelian.qty_kg)
    se.saldo = rp(se.saldo + nilai)
    se.save(update_fields=["total_setor", "qty_setor", "saldo"])

    pembelian.status = StatusDokumen.POSTED
    pembelian.posted_at = timezone.now()
    pembelian.save(update_fields=["status", "nilai", "posted_at"])

    return pembelian

@transaction.atomic
def posting_packing(packing, user=None):
    user = _wajib_user(user)
    packing = Packing.objects.select_for_update().select_related("entitas", "kemasan").get(pk=packing.pk)

    if packing.status != StatusDokumen.DRAFT:
        raise KonflikSaldo(f"Packing {packing.nomor} sudah {packing.status}.")
    if not packing.entitas.aktif:
        raise GalatInventory(f"Entitas {packing.entitas.kode} nonaktif.")

    _pastikan_periode_terbuka(packing.entitas, packing.tanggal)
    batch = Batch.objects.select_for_update().get(pk=packing.batch_id)
    s = saldo_batch(batch)

    if s.sisa_qty <= 0:
        raise KonflikSaldo(f"Batch {batch.nomor} sudah kosong.")
    if packing.qty_kg > s.sisa_qty + TOL_QTY:
        raise KonflikSaldo(f"Batch {batch.nomor} tinggal {s.sisa_qty:,.3f} Kg. Anda mengambil {packing.qty_kg:,.3f} Kg.")

    menghabiskan = abs(packing.qty_kg - s.sisa_qty) <= TOL_QTY
    cost_nom_bahan = s.sisa_nilai if menghabiskan else rp(packing.qty_kg * s.harga_per_kg)
    pool_kem = PoolKemasan.objects.select_for_update().select_related("produk").get(pk=packing.kemasan_id)

    if pool_kem.qty_unit < packing.total_unit:
        raise KonflikSaldo(f"Stok {pool_kem.produk.nama} sisa {pool_kem.qty_unit} Unit. Anda butuh {packing.total_unit} Unit.")

    nilai_kemasan = rp(pool_kem.harga_satuan * packing.total_unit)
    potong_dari_pool_kemasan(pool_kem.produk_id, packing.total_unit, nilai_kemasan)
    total_cost_nom = rp(cost_nom_bahan + nilai_kemasan)

    packing.harga_per_kg = s.harga_per_kg
    packing.cost_nom = total_cost_nom
    packing.menghabiskan = menghabiskan
    packing.status = StatusDokumen.POSTED
    packing.posted_at = timezone.now()
    packing.save(update_fields=["harga_per_kg", "cost_nom", "menghabiskan", "status", "posted_at"])

    MutasiKlaim.objects.create(
        entitas=packing.entitas, grup_bahan=packing.entitas.grup_bahan,
        tipe=TipeMutasi.TARIK, arah=-1, qty_kg=packing.qty_kg, nilai=total_cost_nom,
        ref_type="Packing", ref_id=packing.id,
        keterangan=f"{packing.nomor} - {batch.nomor} - {pool_kem.produk.nama}",
        waktu=packing.waktu, dibuat_oleh=user,
    )

    se = _kunci_saldo(packing.entitas_id)
    se.total_tarik = rp(se.total_tarik + total_cost_nom)
    se.qty_tarik = qty(se.qty_tarik + packing.qty_kg)
    se.saldo = rp(se.saldo - total_cost_nom)
    se.save(update_fields=["total_tarik", "qty_tarik", "saldo"])
    return packing


# ==========================================
# PENGECEKAN INVARIAN DAN LAPORAN (OPTIONAL)
# ==========================================
def jalankan_pemeriksaan_invarian():
    try:
        res = assert_invarian(raise_on_fail=False)
        return res
    except Exception as e:
        return {"cocok": False, "catatan": [str(e)], "rincian": []}

def assert_invarian(raise_on_fail=True):
    catatan = []
    hak_total = SaldoEntitas.objects.aggregate(t=Coalesce(Sum("saldo"), Value(D0_RP), output_field=F_RP))["t"]
    pool_res_total = PoolResource.objects.aggregate(t=Coalesce(Sum("nilai"), Value(D0_RP), output_field=F_RP))["t"]
    pool_kemasan_total = PoolKemasan.objects.aggregate(t=Coalesce(Sum("nilai"), Value(D0_RP), output_field=F_RP))["t"]
    pool_total = rp(pool_res_total + pool_kemasan_total)
    
    wip_total = D0_RP
    for b in Batch.objects.filter(posted_at__isnull=False):
        wip_total += saldo_batch(b).sisa_nilai
        
    fisik_total = rp(pool_total + wip_total)
    selisih = rp(hak_total - fisik_total)
    
    rincian = [{
        "hak_global": hak_total,
        "pool_global": pool_total,
        "wip_produksi": wip_total,
        "fisik_kalkulasi": fisik_total,
        "selisih": selisih
    }]

    if catatan and raise_on_fail:
        raise InvariantMelenceng(" | ".join(catatan))
    return {"cocok": not catatan, "catatan": catatan, "rincian": rincian}