"""
inventory/services.py

Menyediakan API internal tingkat rendah untuk memanipulasi stok dan Ledger finansial.
Aplikasi luar (purchase, produksi, packing) WAJIB menggunakan fungsi di sini 
untuk mengubah stok, guna menjaga integritas Invariant.
"""

from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    PoolResource, RawMutasiEntity, MutasiKlaim, SaldoEntitas,
    TipeMutasi, rp, qty
)

D0 = Decimal("0")


def _kunci_saldo(entitas_id):
    """Mengunci baris SaldoEntitas untuk mencegah race condition (Double-Spend)"""
    try:
        return SaldoEntitas.objects.select_for_update().get(entitas_id=entitas_id)
    except SaldoEntitas.DoesNotExist:
        raise ValidationError(f"Entitas ID {entitas_id} belum memiliki baris SaldoEntitas.")


def _kunci_pool_resource(produk_id):
    res, _ = PoolResource.objects.select_for_update().get_or_create(produk_id=produk_id)
    return res


def _kunci_raw_pool(grup_bahan_id, produk_id):
    pool, _ = RawMutasiEntity.objects.select_for_update().get_or_create(
        grup_bahan_id=grup_bahan_id, produk_id=produk_id
    )
    return pool


@transaction.atomic
def catat_setoran_pembelian(entitas, produk, qty_kg, nilai, ref_type, ref_id, keterangan, user):
    """
    [API UNTUK MODUL PURCHASE]
    Menambah stok fisik (PoolResource) & hak (RawMutasi), serta mencatat klaim finansial (MutasiKlaim).
    """
    # 1. Tambah ke Total Gudang Fisik
    pool_res = _kunci_pool_resource(produk.id)
    pool_res.qty_kg = qty(pool_res.qty_kg + qty_kg)
    pool_res.nilai = rp(pool_res.nilai + nilai)
    pool_res.save(update_fields=["qty_kg", "nilai"])

    # 2. Tambah ke Pemisahan Grup Bahan
    raw_pool = _kunci_raw_pool(entitas.grup_bahan_id, produk.id)
    raw_pool.qty_kg = qty(raw_pool.qty_kg + qty_kg)
    raw_pool.nilai = rp(raw_pool.nilai + nilai)
    raw_pool.save(update_fields=["qty_kg", "nilai"])

    # 3. Catat Jurnal Ledger
    MutasiKlaim.objects.create(
        entitas=entitas, grup_bahan=entitas.grup_bahan,
        tipe=TipeMutasi.SETOR, arah=1,
        qty_kg=qty_kg, nilai=nilai,
        ref_type=ref_type, ref_id=ref_id,
        keterangan=keterangan, waktu=timezone.now(), dibuat_oleh=user
    )

    # 4. Update Saldo Hak Kepemilikan Entitas
    se = _kunci_saldo(entitas.id)
    se.total_setor = rp(se.total_setor + nilai)
    se.qty_setor = qty(se.qty_setor + qty_kg)
    se.saldo = rp(se.saldo + nilai)
    se.save(update_fields=["total_setor", "qty_setor", "saldo"])


@transaction.atomic
def potong_stok_untuk_produksi(grup_bahan_id, produk_id, qty_kg, nilai):
    """
    [API UNTUK MODUL PRODUKSI]
    Memotong fisik bahan baku untuk dimasak (Mixing).
    """
    pool_res = _kunci_pool_resource(produk_id)
    if pool_res.qty_kg < qty_kg:
        raise ValidationError(f"Stok global kurang. Tersedia {pool_res.qty_kg}, diminta {qty_kg}")
    
    pool_res.qty_kg = qty(pool_res.qty_kg - qty_kg)
    pool_res.nilai = rp(pool_res.nilai - nilai)
    if pool_res.qty_kg == 0:
        pool_res.nilai = D0
    pool_res.save(update_fields=["qty_kg", "nilai"])

    raw_pool = _kunci_raw_pool(grup_bahan_id, produk_id)
    if raw_pool.qty_kg < qty_kg:
        raise ValidationError(f"Stok grup bahan kurang. Tersedia {raw_pool.qty_kg}, diminta {qty_kg}")
    
    raw_pool.qty_kg = qty(raw_pool.qty_kg - qty_kg)
    raw_pool.nilai = rp(raw_pool.nilai - nilai)
    if raw_pool.qty_kg == 0:
        raw_pool.nilai = D0
    raw_pool.save(update_fields=["qty_kg", "nilai"])


@transaction.atomic
def catat_penarikan_packing(entitas, grup_bahan_id, qty_kg, nilai, ref_type, ref_id, keterangan, user):
    """
    [API UNTUK MODUL PACKING]
    Memotong klaim finansial (SaldoEntitas) karena WIP sudah berubah menjadi Barang Jadi (Packed).
    """
    MutasiKlaim.objects.create(
        entitas=entitas, grup_bahan_id=grup_bahan_id,
        tipe=TipeMutasi.TARIK, arah=-1,
        qty_kg=qty_kg, nilai=nilai,
        ref_type=ref_type, ref_id=ref_id,
        keterangan=keterangan, waktu=timezone.now(), dibuat_oleh=user
    )

    se = _kunci_saldo(entitas.id)
    se.total_tarik = rp(se.total_tarik + nilai)
    se.qty_tarik = qty(se.qty_tarik + qty_kg)
    se.saldo = rp(se.saldo - nilai)
    se.save(update_fields=["total_tarik", "qty_tarik", "saldo"])


@transaction.atomic
def bebankan_susut_produksi(grup_bahan, nilai_susut, ref_type, ref_id, keterangan, user):
    """
    [API UNTUK MODUL PRODUKSI]
    Membagikan kerugian tekor/shrinkage secara proporsional ke seluruh 
    entitas bersaldo positif di dalam grup bahan yang sama.
    """
    if nilai_susut <= 0:
        return {}

    baris = list(SaldoEntitas.objects
                 .select_for_update()
                 .filter(entitas__grup_bahan=grup_bahan, entitas__aktif=True, saldo__gt=0)
                 .order_by("entitas_id"))

    if not baris:
        raise ValidationError(f"Susut produksi gagal dibebankan: Tidak ada entitas bersaldo positif di grup {grup_bahan.kode}.")

    total_saldo = sum(b.saldo for b in baris)
    beban = {}
    terpakai = D0

    for b in baris[:-1]:
        n = rp(nilai_susut * b.saldo / total_saldo)
        beban[b.entitas_id] = n
        terpakai += n
    
    beban[baris[-1].entitas_id] = rp(nilai_susut - terpakai)

    for b in baris:
        n = beban.get(b.entitas_id, D0)
        if n <= 0:
            continue
        
        MutasiKlaim.objects.create(
            entitas=b.entitas, grup_bahan=grup_bahan,
            tipe=TipeMutasi.RUGI, arah=-1,
            qty_kg=D0, nilai=n,
            ref_type=ref_type, ref_id=ref_id,
            keterangan=keterangan, waktu=timezone.now(), dibuat_oleh=user
        )

        b.total_rugi = rp(b.total_rugi + n)
        b.saldo = rp(b.saldo - n)
        b.save(update_fields=["total_rugi", "saldo"])

    return beban


@transaction.atomic
def terbitkan_pembelian_dari_penerimaan(penerimaan, user):
    """
    Mencatat penerimaan barang dari PO ke dalam inventaris fisik dan ledger klaim entitas.
    """
    po = penerimaan.purchase_order
    entitas = po.entitas
    
    if not hasattr(entitas, 'grup_bahan_id') or not entitas.grup_bahan_id:
        raise ValidationError(f"Entitas {entitas.kode} belum dikonfigurasi memiliki Grup Bahan.")

    for item in penerimaan.item.select_related('po_item__produk').all():
        produk = item.po_item.produk
        qty_kg = item.qty_diterima
        harga_satuan = item.po_item.harga_per_kg
        nilai = qty_kg * harga_satuan

        if qty_kg > 0:
            catat_setoran_pembelian(
                entitas=entitas,
                produk=produk,
                qty_kg=qty_kg,
                nilai=nilai,
                ref_type='PENERIMAAN',
                ref_id=penerimaan.id,
                keterangan=f"Penerimaan No. {penerimaan.nomor} dari PO {po.no_po}",
                user=user
            )

    return penerimaan
