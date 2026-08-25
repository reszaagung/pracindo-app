from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from core.models import CounterDokumen, PeriodeAkuntansi
from .models import (
    Kemasan, MutasiKlaim, Packing, Pembelian, SaldoEntitas, RawMutasiEntity,
    StatusDokumen, SumberPembelian, TipeMutasi, harga, qty, rp, PoolResource
)

D0 = Decimal("0")
D0_RP = Decimal("0.00")
D0_QTY = Decimal("0.000")
TOL_QTY = Decimal("0.001")
TOL_RP = Decimal("0.01")

F_RP = DecimalField(max_digits=20, decimal_places=2)

class GalatInventory(ValidationError):
    http = 422

class KonflikSaldo(GalatInventory):
    http = 409

class InvariantMelenceng(GalatInventory):
    http = 500

def _wajib_user(user):
    if not getattr(user, "is_authenticated", False):
        raise GalatInventory("Operasi ini wajib punya pembuat yang tercatat.")
    return user

def _pastikan_periode_terbuka(entitas, tanggal):
    if PeriodeAkuntansi.objects.filter(entitas=entitas, tahun=tanggal.year, bulan=tanggal.month, ditutup=True).exists():
        raise GalatInventory(f"Periode {tanggal.month:02d}/{tanggal.year} untuk {entitas.kode} sudah ditutup.")

def _kunci_pool(grup_bahan_id, produk_ids):
    pools = {p.produk_id: p for p in RawMutasiEntity.objects
             .select_for_update()
             .filter(grup_bahan_id=grup_bahan_id, produk_id__in=produk_ids)
             .order_by("produk_id")}
    for pid in sorted(produk_ids):
        if pid not in pools:
            pools[pid], _ = RawMutasiEntity.objects.get_or_create(grup_bahan_id=grup_bahan_id, produk_id=pid)
    return pools

def _kunci_saldo(entitas_id):
    try:
        return SaldoEntitas.objects.select_for_update().get(entitas_id=entitas_id)
    except SaldoEntitas.DoesNotExist:
        raise InvariantMelenceng(f"Entitas id {entitas_id} tidak punya baris SaldoEntitas.")

def _turunkan_pool(pool, q, nilai, label):
    pool.qty_kg = qty(pool.qty_kg - q)
    pool.nilai = rp(pool.nilai - nilai)
    if pool.qty_kg < 0 or pool.nilai < 0:
        raise InvariantMelenceng(f"Pool {label} menjadi negatif.")
    if pool.qty_kg == 0:
        pool.nilai = D0_RP   
    pool.save(update_fields=["qty_kg", "nilai"])

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
    if pembelian.grup_bahan_id != pembelian.entitas.grup_bahan_id:
        raise GalatInventory(f"Entitas {pembelian.entitas.kode} termasuk grup {pembelian.entitas.grup_bahan.kode}, tidak bisa menyetor ke pool {pembelian.grup_bahan.kode}.")

    _pastikan_periode_terbuka(pembelian.entitas, pembelian.tanggal)

    nilai = rp(pembelian.qty_kg * pembelian.harga_per_kg)
    pembelian.nilai = nilai

    pool = _kunci_pool(pembelian.grup_bahan_id, [pembelian.produk_id])[pembelian.produk_id]
    pool.qty_kg = qty(pool.qty_kg + pembelian.qty_kg)
    pool.nilai = rp(pool.nilai + nilai)
    pool.save(update_fields=["qty_kg", "nilai"])

    tambah_ke_pool_resource(pembelian.produk_id, pembelian.qty_kg, nilai)

    MutasiKlaim.objects.create(
        entitas=pembelian.entitas, grup_bahan=pembelian.grup_bahan,
        tipe=TipeMutasi.SETOR, arah=1,
        qty_kg=pembelian.qty_kg, nilai=nilai,
        ref_type="Pembelian", ref_id=pembelian.id,
        keterangan=f"{pembelian.nomor} - {pembelian.produk}",
        waktu=pembelian.waktu, dibuat_oleh=user)

    se = _kunci_saldo(pembelian.entitas_id)
    se.total_setor = rp(se.total_setor + nilai)
    se.qty_setor = qty(se.qty_setor + pembelian.qty_kg)
    se.saldo = rp(se.saldo + nilai)
    se.save(update_fields=["total_setor", "qty_setor", "saldo"])

    pembelian.status = StatusDokumen.POSTED
    pembelian.posted_at = timezone.now()
    pembelian.save(update_fields=["status", "nilai", "posted_at"])

    assert_invarian()
    return pembelian

@transaction.atomic
def void_pembelian(pembelian, alasan, user=None):
    user = _wajib_user(user)
    pembelian = Pembelian.objects.select_for_update().get(pk=pembelian.pk)

    if pembelian.sumber == SumberPembelian.PENERIMAAN:
        raise KonflikSaldo(f"{pembelian.nomor} melekat pada penerimaan {pembelian.penerimaan_item.penerimaan.nomor}.")
    if pembelian.status != StatusDokumen.POSTED:
        raise KonflikSaldo(f"Hanya pembelian POSTED yang bisa di-VOID. {pembelian.nomor} berstatus {pembelian.status}.")
    if not alasan or not alasan.strip():
        raise GalatInventory("Alasan VOID wajib diisi.")

    _pastikan_periode_terbuka(pembelian.entitas, timezone.localdate())

    pool = _kunci_pool(pembelian.grup_bahan_id, [pembelian.produk_id])[pembelian.produk_id]

    bergerak = Pembelian.objects.filter(
        grup_bahan_id=pembelian.grup_bahan_id, produk_id=pembelian.produk_id,
        status=StatusDokumen.POSTED, waktu__gt=pembelian.waktu).exists()
    
    if bergerak or _pool_terpakai_sejak(pembelian):
        raise KonflikSaldo(f"Pool {pembelian.produk} sudah bergerak sejak {pembelian.nomor} diposting.")
    if pool.qty_kg < pembelian.qty_kg - TOL_QTY:
        raise KonflikSaldo(f"Pool {pembelian.produk} tinggal {pool.qty_kg} Kg, kurang dari {pembelian.qty_kg} Kg yang akan dibatalkan.")

    _turunkan_pool(pool, pembelian.qty_kg, pembelian.nilai, f"{pembelian.produk}")
    potong_dari_pool_resource(pembelian.produk_id, pembelian.qty_kg)

    MutasiKlaim.objects.create(
        entitas=pembelian.entitas, grup_bahan=pembelian.grup_bahan,
        tipe=TipeMutasi.PENYESUAIAN, arah=-1,
        qty_kg=pembelian.qty_kg, nilai=pembelian.nilai,
        ref_type="VoidPembelian", ref_id=pembelian.id,
        keterangan=f"VOID {pembelian.nomor}: {alasan}",
        waktu=timezone.now(), dibuat_oleh=user)

    se = _kunci_saldo(pembelian.entitas_id)
    se.total_setor = rp(se.total_setor - pembelian.nilai)
    se.qty_setor = qty(se.qty_setor - pembelian.qty_kg)
    se.saldo = rp(se.saldo - pembelian.nilai)
    se.save(update_fields=["total_setor", "qty_setor", "saldo"])

    pembelian.status = StatusDokumen.VOID
    pembelian.catatan = f"{pembelian.catatan}\n[VOID] {alasan}".strip()
    pembelian.save(update_fields=["status", "catatan"])

    assert_invarian()
    return pembelian

def _pool_terpakai_sejak(pembelian):
    from produksi.models import BatchInputRaw, StatusBatch
    return BatchInputRaw.objects.filter(
        produk_id=pembelian.produk_id,
        batch__grup_bahan_id=pembelian.grup_bahan_id,
        batch__status=StatusBatch.POSTED,
        batch__posted_at__gte=pembelian.posted_at or pembelian.waktu,
    ).exists()

@transaction.atomic
def terbitkan_pembelian_dari_penerimaan(penerimaan, user=None):
    user = _wajib_user(user)
    po = penerimaan.purchase_order
    entitas = getattr(po, "entitas", None)

    if entitas is None:
        raise GalatInventory(f"PO pada {penerimaan.nomor} tidak punya entitas pemilik hak.")
    if not entitas.aktif:
        raise GalatInventory(f"Entitas {entitas.kode} nonaktif dan tidak bisa menyetor.")

    _pastikan_periode_terbuka(entitas, penerimaan.tanggal)

    grup = entitas.grup_bahan
    baris = list(penerimaan.item.select_related("po_item", "po_item__produk").order_by("po_item__produk_id"))
    
    if not baris:
        raise GalatInventory(f"Penerimaan {penerimaan.nomor} tidak punya item.")

    produk_ids = sorted({b.po_item.produk_id for b in baris})
    pools = _kunci_pool(grup.id, produk_ids)       
    se = _kunci_saldo(entitas.id)                     
    terbit = []

    for b in baris:
        if Pembelian.objects.filter(penerimaan_item=b).exists():
            continue
        
        q = qty(b.qty_diterima or 0)
        if q <= 0:
            continue

        item = b.po_item
        h = harga(item.harga_per_kg)
        nilai = rp(q * h)
        sekarang = timezone.now()

        p = Pembelian.objects.create(
            nomor=CounterDokumen.berikutnya(entitas, "PB", penerimaan.tanggal),
            no_po=str(po),
            entitas=entitas,
            grup_bahan=grup,
            produk=item.produk,
            qty_kg=q,
            harga_per_kg=h,
            nilai=nilai,
            tanggal=penerimaan.tanggal,
            waktu=sekarang,
            status=StatusDokumen.POSTED,
            posted_at=sekarang,
            sumber=SumberPembelian.PENERIMAAN,
            penerimaan_item=b,
            catatan=f"Otomatis dari {penerimaan.nomor} - SJ {penerimaan.no_surat_jalan}",
            dibuat_oleh=user,
        )

        pool = pools[item.produk_id]
        pool.qty_kg = qty(pool.qty_kg + q)
        pool.nilai = rp(pool.nilai + nilai)
        pool.save(update_fields=["qty_kg", "nilai"])

        tambah_ke_pool_resource(item.produk_id, q, nilai)

        MutasiKlaim.objects.create(
            entitas=entitas, grup_bahan=grup,
            tipe=TipeMutasi.SETOR, arah=1,
            qty_kg=q, nilai=nilai,
            ref_type="Pembelian", ref_id=p.id,
            keterangan=f"{p.nomor} - {item.produk} - {penerimaan.nomor}",
            waktu=p.waktu, dibuat_oleh=user)

        se.total_setor = rp(se.total_setor + nilai)
        se.qty_setor = qty(se.qty_setor + q)
        se.saldo = rp(se.saldo + nilai)
        terbit.append(p)

    if terbit:
        se.save(update_fields=["total_setor", "qty_setor", "saldo"])

    assert_invarian()
    return terbit

@transaction.atomic
def posting_packing(packing, user=None):
    from produksi.models import Batch
    from produksi.services import saldo_batch

    user = _wajib_user(user)
    packing = Packing.objects.select_for_update().get(pk=packing.pk)

    if packing.status != StatusDokumen.DRAFT:
        raise KonflikSaldo(f"Packing {packing.nomor} sudah {packing.status}.")
    if not packing.entitas.aktif:
        raise GalatInventory(f"Entitas {packing.entitas.kode} nonaktif.")

    _pastikan_periode_terbuka(packing.entitas, packing.tanggal)

    batch = Batch.objects.select_for_update().get(pk=packing.batch_id)
    if batch.grup_bahan_id != packing.entitas.grup_bahan_id:
        raise GalatInventory(f"Batch {batch.nomor} milik grup {batch.grup_bahan.kode}, sementara {packing.entitas.kode} termasuk grup {packing.entitas.grup_bahan.kode}.")

    s = saldo_batch(batch)
    if s.sisa_qty <= 0:
        raise KonflikSaldo(f"Batch {batch.nomor} sudah kosong.")
    if packing.qty_kg > s.sisa_qty + TOL_QTY:
        raise KonflikSaldo(f"Batch {batch.nomor} tinggal {s.sisa_qty:,.3f} Kg. Anda mengambil {packing.qty_kg:,.3f} Kg.")
    
    menghabiskan = abs(packing.qty_kg - s.sisa_qty) <= TOL_QTY
    nilai_hpp = s.sisa_nilai if menghabiskan else rp(packing.qty_kg * s.harga_per_kg)

    packing.harga_per_kg = s.harga_per_kg
    packing.nilai_hpp = nilai_hpp
    packing.menghabiskan = menghabiskan
    packing.status = StatusDokumen.POSTED
    packing.posted_at = timezone.now()
    packing.save(update_fields=["harga_per_kg", "nilai_hpp", "menghabiskan", "status", "posted_at"])

    MutasiKlaim.objects.create(
        entitas=packing.entitas, grup_bahan=batch.grup_bahan,
        tipe=TipeMutasi.TARIK, arah=-1,
        qty_kg=packing.qty_kg, nilai=nilai_hpp,
        ref_type="Packing", ref_id=packing.id,
        keterangan=f"{packing.nomor} - {batch.nomor} - {packing.kemasan}",
        waktu=packing.waktu, dibuat_oleh=user)

    se = _kunci_saldo(packing.entitas_id)                                
    se.total_tarik = rp(se.total_tarik + nilai_hpp)
    se.qty_tarik = qty(se.qty_tarik + packing.qty_kg)
    se.saldo = rp(se.saldo - nilai_hpp)
    se.save(update_fields=["total_tarik", "qty_tarik", "saldo"])

    assert_invarian()
    return packing

def pratinjau_packing(batch_id, qty_diminta):
    from produksi.models import Batch
    from produksi.services import saldo_batch

    try:
        batch = Batch.objects.select_related("tangki").get(pk=batch_id)
    except (Batch.DoesNotExist, ValueError, TypeError):
        return {"valid": False, "kode": "BATCH_TIDAK_DITEMUKAN", "pesan": f"Batch id {batch_id} tidak ditemukan."}
    try:
        q = qty(Decimal(str(qty_diminta)))
    except Exception:
        return {"valid": False, "kode": "QTY_TIDAK_VALID", "pesan": "Qty harus berupa angka."}
    if q <= 0:
        return {"valid": False, "kode": "QTY_TIDAK_VALID", "pesan": "Qty harus lebih dari 0."}

    s = saldo_batch(batch)
    if q > s.sisa_qty + TOL_QTY:
        return {"valid": False, "kode": "SISA_BATCH_KURANG", "pesan": f"Batch {batch.nomor} tinggal {s.sisa_qty} Kg."}

    menghabiskan = abs(q - s.sisa_qty) <= TOL_QTY
    nilai = s.sisa_nilai if menghabiskan else rp(q * s.harga_per_kg)
    
    return {
        "valid": True, "batch": batch.nomor, "tangki": batch.tangki.kode,
        "qty_kg": str(q), "harga_per_kg": str(s.harga_per_kg),
        "nilai_tagihan": str(nilai), "menghabiskan": menghabiskan,
        "peringatan": ([f"Pengambilan ini MENGHABISKAN batch {batch.nomor}. Seluruh sisa nilainya ikut keluar."] if menghabiskan else []),
    }

@transaction.atomic
def bebankan_susut(batch, user=None):
    user = _wajib_user(user)
    nilai_susut = rp(batch.nilai_susut or 0)
    if nilai_susut <= 0:
        return {}

    baris = list(SaldoEntitas.objects
                 .select_for_update()
                 .filter(entitas__grup_bahan_id=batch.grup_bahan_id, entitas__aktif=True, saldo__gt=0)
                 .select_related("entitas")
                 .order_by("entitas_id"))
    if not baris:
        raise InvariantMelenceng(f"Susut Rp{nilai_susut:,.2f} pada batch {batch.nomor} tidak bisa dibebankan: tidak ada entitas bersaldo positif di grup {batch.grup_bahan.kode}.")

    total = sum(b.saldo for b in baris)
    urut = sorted(baris, key=lambda b: (-b.saldo, b.entitas_id))

    beban, terpakai = {}, D0_RP
    for b in urut[1:]:
        n = rp(nilai_susut * b.saldo / total)
        beban[b.entitas_id] = n
        terpakai += n
    beban[urut[0].entitas_id] = rp(nilai_susut - terpakai)

    peta = {b.entitas_id: b for b in baris}
    for eid, n in beban.items():
        if n <= 0:
            continue
        se = peta[eid]
        MutasiKlaim.objects.create(
            entitas=se.entitas, grup_bahan=batch.grup_bahan,
            tipe=TipeMutasi.RUGI, arah=-1,
            qty_kg=D0_QTY, nilai=n,
            ref_type="Batch", ref_id=batch.id,
            keterangan=f"Susut produksi {batch.nomor}",
            waktu=batch.posted_at or timezone.now(), dibuat_oleh=user)
        se.total_rugi = rp(se.total_rugi + n)
        se.saldo = rp(se.saldo - n)
        se.save(update_fields=["total_rugi", "saldo"])

    if abs(sum(beban.values()) - nilai_susut) > TOL_RP:
        raise InvariantMelenceng(f"Pembagian susut tidak berjumlah Rp{nilai_susut:,.2f}.")
    return beban

def assert_invarian(raise_on_fail=True):
    from core.models import GrupBahan
    catatan = []
    rincian = []

    for grup in GrupBahan.objects.all():
        hak = SaldoEntitas.objects.filter(entitas__grup_bahan=grup).aggregate(t=Coalesce(Sum("saldo"), Value(D0_RP), output_field=F_RP))["t"]
        pool = RawMutasiEntity.objects.filter(grup_bahan=grup).aggregate(t=Coalesce(Sum("nilai"), Value(D0_RP), output_field=F_RP))["t"]
        nilai_batch, n_batch = _nilai_batch(grup.id)

        fisik = rp(pool + nilai_batch)
        selisih = rp(hak - fisik)
        n = (SaldoEntitas.objects.filter(entitas__grup_bahan=grup).count()
             + RawMutasiEntity.objects.filter(grup_bahan=grup).count()
             + n_batch + 1)
        if abs(selisih) > TOL_RP * n:
            catatan.append(f"I1 [{grup.kode}] KONSERVASI RUPIAH: hak entitas Rp{hak:,.2f} != nilai barang Rp{fisik:,.2f} (pool Rp{pool:,.2f} + batch Rp{nilai_batch:,.2f}). Selisih Rp{selisih:,.2f}.")

        rincian.append({"grup": grup.kode, "hak": hak, "pool": pool, "batch": nilai_batch, "selisih": selisih})

    if RawMutasiEntity.objects.filter(Q(qty_kg__lt=0) | Q(nilai__lt=0)).exists():
        catatan.append("I2 POOL NEGATIF: ada baris RawMutasiEntity bernilai minus.")

    if RawMutasiEntity.objects.filter(qty_kg=0).exclude(nilai=0).exists():
        catatan.append("I2b POOL KOSONG TAPI BERNILAI: isinya akan keluar gratis pada pengambilan berikutnya.")
    
    try:
        from warehouse.models import PenerimaanItem
        yatim = PenerimaanItem.objects.filter(qty_diterima__gt=0, pembelian__isnull=True).count()
        if yatim:
            catatan.append(f"I7 PENERIMAAN YATIM: {yatim} baris timbangan belum melahirkan setoran.")
    except Exception:
        pass

    if catatan and raise_on_fail:
        raise InvariantMelenceng(" | ".join(catatan))
    return {"cocok": not catatan, "catatan": catatan, "rincian": rincian}

def _nilai_batch(grup_bahan_id):
    from produksi.models import Batch, StatusBatch, TransferWip

    qs = Batch.objects.filter(status=StatusBatch.POSTED, grup_bahan_id=grup_bahan_id)
    masuk = qs.aggregate(t=Coalesce(Sum("nilai_hasil"), Value(D0_RP), output_field=F_RP))["t"]
    n = qs.count()

    keluar_pack = Packing.objects.filter(status=StatusDokumen.POSTED, batch__grup_bahan_id=grup_bahan_id).aggregate(t=Coalesce(Sum("nilai_hpp"), Value(D0_RP), output_field=F_RP))["t"]
    keluar_wip = TransferWip.objects.filter(batch_tujuan__status=StatusBatch.POSTED, batch_sumber__grup_bahan_id=grup_bahan_id).aggregate(t=Coalesce(Sum("nilai"), Value(D0_RP), output_field=F_RP))["t"]

    return rp(masuk - keluar_pack - keluar_wip), n

def jalankan_pemeriksaan_invarian():
    h = assert_invarian(raise_on_fail=False)
    return {
        "status": "SEIMBANG" if h["cocok"] else "MELENCENG",
        "catatan": h["catatan"],
        "per_grup": [{
            "grup": r["grup"],
            "hak_entitas": str(r["hak"]),
            "nilai_pool": str(r["pool"]),
            "nilai_batch": str(r["batch"]),
            "nilai_ada": str(rp(r["pool"] + r["batch"])),
            "selisih": str(r["selisih"]),
        } for r in h["rincian"]],
    }

def get_raw_mutasi_entity_all(grup_bahan_id=None):
    qs = RawMutasiEntity.objects.select_related("produk", "grup_bahan").filter(qty_kg__gt=0)
    if grup_bahan_id:
        qs = qs.filter(grup_bahan_id=grup_bahan_id)

    data, total = [], D0_RP
    for p in qs.order_by("grup_bahan__kode", "produk__kode"):
        data.append({
            "grup": p.grup_bahan.kode,
            "produk_id": p.produk_id, 
            "produk_kode": p.produk.kode, 
            "produk_nama": str(p.produk), 
            "qty_kg": str(p.qty_kg), 
            "nilai": str(p.nilai),
            "harga_rata": str(p.harga_rata),
        })
        total += p.nilai
    return {"rincian": data, "total_nilai_pool": str(rp(total))}

def get_rekap_klaim(grup_bahan_id=None):
    qs = SaldoEntitas.objects.select_related("entitas", "entitas__grup_bahan").filter(entitas__aktif=True)
    if grup_bahan_id:
        qs = qs.filter(entitas__grup_bahan_id=grup_bahan_id)

    grup = {}
    for e in qs.order_by("entitas__grup_bahan__kode", "entitas__kode"):
        g = grup.setdefault(e.entitas.grup_bahan.kode, {"grup": e.entitas.grup_bahan.kode, "entitas": [], "total": D0_RP})
        g["entitas"].append({
            "entitas_id": e.entitas_id, "kode": e.entitas.kode,
            "nama": e.entitas.nama,
            "qty_setor": str(e.qty_setor), "qty_tarik": str(e.qty_tarik),
            "total_setor": str(e.total_setor),
            "total_tarik": str(e.total_tarik),
            "total_rugi": str(e.total_rugi), "saldo": str(e.saldo),
            "status": ("IMPAS" if e.saldo == 0 else "KLAIM" if e.saldo > 0 else "HUTANG"),
        })
        g["total"] += e.saldo

    return {"grup": [{**g, "total": str(rp(g["total"]))} for g in grup.values()]}

def get_kartu_stok(produk_id, grup_bahan_id):
    from produksi.models import Batch, StatusBatch
    from produksi.services import porsi_raw, saldo_batch

    pool = RawMutasiEntity.objects.select_related("produk", "grup_bahan").get(produk_id=produk_id, grup_bahan_id=grup_bahan_id)

    di_wip, rincian = D0_QTY, []
    for b in Batch.objects.filter(status=StatusBatch.POSTED, grup_bahan_id=grup_bahan_id).select_related("tangki"):
        s = saldo_batch(b)
        if s.sisa_qty <= 0:
            continue
        for kunci, q in porsi_raw(b, s.sisa_qty).items():
            pid = kunci[0] if isinstance(kunci, tuple) else kunci
            if pid != int(produk_id):
                continue
            di_wip += q
            rincian.append({"batch": b.nomor, "tangki": b.tangki.kode, "qty_kg": str(qty(q))})

    return {
        "grup": pool.grup_bahan.kode,
        "produk_id": pool.produk_id, "produk_kode": pool.produk.kode,
        "qty_di_pool": str(pool.qty_kg),
        "qty_di_wip": str(qty(di_wip)),
        "total_fisik": str(qty(pool.qty_kg + di_wip)),
        "rincian_wip": rincian,
    }

def get_barang_jadi(grup_bahan_id=None):
    qs = Packing.objects.filter(status=StatusDokumen.POSTED).select_related("entitas", "kemasan")
    if grup_bahan_id:
        qs = qs.filter(entitas__grup_bahan_id=grup_bahan_id)

    hasil = {}
    for p in qs:
        k = (p.entitas.kode, p.kemasan.nama)
        d = hasil.setdefault(k, {"entitas": p.entitas.kode, "kemasan": p.kemasan.nama, "unit": D0, "qty_kg": D0_QTY, "nilai": D0_RP})
        d["unit"] += p.total_unit
        d["qty_kg"] += p.qty_kg
        d["nilai"] += p.nilai_hpp

    rincian = [{
        "entitas": v["entitas"], "kemasan": v["kemasan"],
        "unit": str(v["unit"]), "qty_kg": str(v["qty_kg"]),
        "nilai": str(rp(v["nilai"])),
        "harga_rata": str(harga(v["nilai"] / v["qty_kg"]) if v["qty_kg"] else D0),
    } for v in sorted(hasil.values(), key=lambda x: (x["entitas"], x["kemasan"]))]

    return {"rincian": rincian, "total_nilai": str(rp(sum((Decimal(r["nilai"]) for r in rincian), D0_RP)))}

def tambah_ke_pool_resource(produk_id, qty_tambah, nilai_tambah):
    with transaction.atomic():
        pool_res, created = PoolResource.objects.select_for_update().get_or_create(
            produk_id=produk_id,
            defaults={'qty_kg': D0_QTY, 'nilai': D0_RP}
        )
        pool_res.qty_kg = qty(pool_res.qty_kg + qty_tambah)
        pool_res.nilai = rp(pool_res.nilai + nilai_tambah)
        pool_res.save(update_fields=["qty_kg", "nilai"])
        return pool_res

def potong_dari_pool_resource(produk_id, qty_potong):
    with transaction.atomic():
        pool_res = PoolResource.objects.select_for_update().get(produk_id=produk_id)
        nilai_potong = rp(pool_res.harga_rata * qty_potong)
        pool_res.qty_kg = qty(pool_res.qty_kg - qty_potong)
        pool_res.nilai = rp(pool_res.nilai - nilai_potong)
        if pool_res.qty_kg == 0:
            pool_res.nilai = D0_RP
        pool_res.save(update_fields=["qty_kg", "nilai"])
        return nilai_potong