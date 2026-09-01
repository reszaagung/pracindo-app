from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.db.models import DecimalField, Sum, Value, Q 
from django.db.models.functions import Coalesce
from django.utils import timezone
from produksi.models import Batch
from produksi.services import saldo_batch
from core.models import CounterDokumen, PeriodeAkuntansi
from .models import (
    MutasiKlaim, Packing, Pembelian, SaldoEntitas,
    StatusDokumen, SumberPembelian, TipeMutasi, PoolResource, PoolKemasan
)

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
        tipe=TipeMutasi.SETOR, arah=1,
        qty_kg=pembelian.qty_kg, nilai=nilai,
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

    bergerak = Pembelian.objects.filter(
        produk_id=pembelian.produk_id,
        status=StatusDokumen.POSTED, waktu__gt=pembelian.waktu).exists()
    
    if bergerak or _pool_terpakai_sejak(pembelian):
        raise KonflikSaldo(f"Pool {pembelian.produk} sudah bergerak sejak {pembelian.nomor} diposting.")

    if pembelian.produk.jenis == 'KEMASAN':
        q_unit_int = int(pembelian.qty_kg)
        try:
            pool = PoolKemasan.objects.get(produk_id=pembelian.produk_id)
            if pool.qty_unit < q_unit_int:
                raise KonflikSaldo(f"Pool {pembelian.produk} tinggal {pool.qty_unit} Unit, kurang dari {q_unit_int} Unit yang dibatalkan.")
        except PoolKemasan.DoesNotExist:
            raise KonflikSaldo(f"Pool {pembelian.produk} kosong.")
        
        potong_dari_pool_kemasan(pembelian.produk_id, q_unit_int, pembelian.nilai)
    else:
        pool = PoolResource.objects.get(produk_id=pembelian.produk_id)
        if pool.qty_kg < pembelian.qty_kg - TOL_QTY:
            raise KonflikSaldo(f"Pool {pembelian.produk} tinggal {pool.qty_kg} Kg, kurang dari {pembelian.qty_kg} Kg yang dibatalkan.")
        
        potong_dari_pool_resource(pembelian.produk_id, pembelian.qty_kg, pembelian.nilai)

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

        if item.produk.jenis == 'KEMASAN':
            tambah_ke_pool_kemasan(item.produk_id, q, nilai)
        else:
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

    packing = (
        Packing.objects
        .select_for_update()
        .select_related("entitas", "kemasan")
        .get(pk=packing.pk)
    )

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

    if menghabiskan:
        cost_nom_bahan = s.sisa_nilai
    else:
        cost_nom_bahan = rp(packing.qty_kg * s.harga_per_kg)

    pool_kem = PoolKemasan.objects.select_for_update().select_related("produk").get(pk=packing.kemasan_id)

    if pool_kem.qty_unit < packing.total_unit:
        raise KonflikSaldo(f"Stok {pool_kem.produk.nama} di Pool hanya sisa {pool_kem.qty_unit} Unit. Anda butuh {packing.total_unit} Unit.")

    nilai_kemasan = rp(pool_kem.harga_satuan * packing.total_unit)

    potong_dari_pool_kemasan(pool_kem.produk_id, packing.total_unit, nilai_kemasan)

    total_cost_nom = rp(cost_nom_bahan + nilai_kemasan)

    packing.harga_per_kg = s.harga_per_kg
    packing.cost_nom = total_cost_nom
    packing.menghabiskan = menghabiskan
    packing.status = StatusDokumen.POSTED
    packing.posted_at = timezone.now()

    packing.save(
        update_fields=[
            "harga_per_kg",
            "cost_nom",
            "menghabiskan",
            "status",
            "posted_at",
        ]
    )

    MutasiKlaim.objects.create(
        entitas=packing.entitas,
        grup_bahan=packing.entitas.grup_bahan,
        tipe=TipeMutasi.TARIK,
        arah=-1,
        qty_kg=packing.qty_kg,
        nilai=total_cost_nom,
        ref_type="Packing",
        ref_id=packing.id,
        keterangan=f"{packing.nomor} - {batch.nomor} - {pool_kem.produk.nama}",
        waktu=packing.waktu,
        dibuat_oleh=user,
    )

    se = _kunci_saldo(packing.entitas_id)
    se.total_tarik = rp(se.total_tarik + total_cost_nom)
    se.qty_tarik = qty(se.qty_tarik + packing.qty_kg)
    se.saldo = rp(se.saldo - total_cost_nom)
    se.save(update_fields=["total_tarik", "qty_tarik", "saldo"])

    assert_invarian()
    return packing

def pratinjau_packing(batch_id, qty_diminta):
    from produksi.services import saldo_batch
    
    try:
        b_id = int(batch_id) 
        batch = Batch.objects.select_related("tangki").get(pk=b_id)
    except (ObjectDoesNotExist, ValueError, TypeError):
        return {"valid": False, "kode": "BATCH_TIDAK_DITEMUKAN", "pesan": "Batch tidak ditemukan atau ID tidak valid."}
        
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
def generate_nomor_packing(entitas_id):
    last = (
        Packing.objects
        .select_for_update()
        .filter(entitas_id=entitas_id)
        .order_by("-id")
        .first())

    nomor_urut = 1

    if last and last.nomor:
        try:
            nomor_urut = int(last.nomor.rsplit("-", 1)[1]) + 1
        except (ValueError, IndexError):
            nomor_urut = 1

    return f"PKG-{entitas_id}-{nomor_urut:03d}"

@transaction.atomic
def bebankan_susut(batch, user=None):
    user = _wajib_user(user)
    nilai_susut = rp(batch.nilai_susut or 0)
    if nilai_susut <= 0:
        return {}

    baris = list(SaldoEntitas.objects
                 .select_for_update()
                 .filter(entitas__aktif=True, saldo__gt=0)
                 .select_related("entitas", "entitas__grup_bahan")
                 .order_by("entitas_id"))
    if not baris:
        raise InvariantMelenceng(f"Susut Rp{nilai_susut:,.2f} pada batch {batch.nomor} tidak bisa dibebankan: tidak ada entitas bersaldo positif di seluruh sistem.")

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
            entitas=se.entitas, grup_bahan=se.entitas.grup_bahan,
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

def get_pool_resource_all():
    qs = PoolResource.objects.select_related("produk").all()
    rincian = []
    total_nilai = D0_RP
    for p in qs:
        rincian.append({
            "produk_id": p.produk_id,
            "produk_kode": p.produk.kode,
            "produk_nama": p.produk.nama,
            "qty_kg": str(p.qty_kg),
            "nilai": str(p.nilai),
            "harga_rata": str(p.harga_rata)
        })
        total_nilai += p.nilai
    return {"rincian": rincian, "total_nilai_pool": str(total_nilai)}

def jalankan_pemeriksaan_invarian():
    try:
        res = assert_invarian(raise_on_fail=False)
        return res
    except Exception as e:
        return {"cocok": False, "catatan": [str(e)], "rincian": []}

def assert_invarian(raise_on_fail=True):
    from produksi.models import Batch, StatusBatch
    from produksi.services import saldo_batch
    
    catatan = []
    hak_total = SaldoEntitas.objects.aggregate(t=Coalesce(Sum("saldo"), Value(D0_RP), output_field=F_RP))["t"]

    pool_res_total = PoolResource.objects.aggregate(t=Coalesce(Sum("nilai"), Value(D0_RP), output_field=F_RP))["t"]
    pool_kemasan_total = PoolKemasan.objects.aggregate(t=Coalesce(Sum("nilai"), Value(D0_RP), output_field=F_RP))["t"]
    pool_total = rp(pool_res_total + pool_kemasan_total)
    
    wip_total = D0_RP
    for b in Batch.objects.filter(status=StatusBatch.POSTED):
        wip_total += saldo_batch(b).sisa_nilai
        
    fisik_total = rp(pool_total + wip_total)
    selisih = rp(hak_total - fisik_total)
    
    if PoolResource.objects.filter(Q(qty_kg__lt=0) | Q(nilai__lt=0)).exists():
        catatan.append("POOL NEGATIF: ada baris PoolResource bernilai minus.")
    if PoolResource.objects.filter(qty_kg=0).exclude(nilai=0).exists():
        catatan.append("POOL KOSONG TAPI BERNILAI: isinya akan keluar gratis pada pengambilan berikutnya.")

    if PoolKemasan.objects.filter(Q(qty_unit__lt=0) | Q(nilai__lt=0)).exists():
        catatan.append("POOL KEMASAN NEGATIF: ada baris PoolKemasan bernilai minus.")
    if PoolKemasan.objects.filter(qty_unit=0).exclude(nilai=0).exists():
        catatan.append("POOL KEMASAN KOSONG TAPI BERNILAI: isinya akan keluar gratis pada pengambilan berikutnya.")

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

def get_rekap_klaim(grup_id=None):
    queryset = MutasiKlaim.objects.all()
    if grup_id:
        queryset = queryset.filter(grup_bahan_id=grup_id)
    
    rekap_data = list(queryset.values())
    return {
        "results": rekap_data,
        "total": len(rekap_data)
    }

def get_barang_jadi(grup=None):
    pools = PoolResource.objects.all()
    if grup:
        pools = pools.filter(produk_id__icontains=grup)
    
    return [
        {
            "produk_id": p.produk_id,
            "qty_kg": str(p.qty_kg),
            "nilai": str(p.nilai),
            "grup": grup or "UMUM"
        } 
        for p in pools
    ]