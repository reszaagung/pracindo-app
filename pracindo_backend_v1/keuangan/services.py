import uuid
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import Entitas
from .models import RekeningBank, MutasiKas, PengeluaranKas
from akunting.services import posting # Memanggil modul akunting sesuai aturan

@transaction.atomic
def catat_pengeluaran(entitas_id, kategori, keterangan, pemohon, nominal, user, bukti_nota=None):
    # 1. Simpan form nota pengeluaran
    pengeluaran = PengeluaranKas.objects.create(
        entitas_id=entitas_id,
        kategori=kategori,
        keterangan=keterangan,
        pemohon=pemohon,
        nominal=nominal,
        bukti_nota=bukti_nota
    )

    # 2. Tarik Rekening KAS KECIL milik entitas terkait dengan mode Lock (mencegah bentrok data)
    rekening = RekeningBank.objects.select_for_update().filter(
        entitas_id=entitas_id, jenis='KAS_KECIL'
    ).first()
    
    if not rekening:
        raise ValidationError(f"Rekening Kas Kecil untuk entitas ini belum dikonfigurasi.")
    
    if rekening.saldo < nominal:
        raise ValidationError(f"Saldo kas kecil tidak cukup! Sisa saldo: {rekening.saldo}")

    # 3. Potong Saldo dan Catat Mutasi Keuangan
    rekening.urutan_terakhir += 1
    rekening.saldo -= nominal
    rekening.save(update_fields=['urutan_terakhir', 'saldo'])

    referensi_trx = f"PC-{timezone.now().strftime('%y%m%d')}-{pengeluaran.id}"
    
    mutasi = MutasiKas.objects.create(
        rekening=rekening,
        urutan=rekening.urutan_terakhir,
        kredit=nominal, # Uang keluar dicatat di sisi kredit
        saldo_akhir=rekening.saldo,
        keterangan=keterangan,
        referensi=referensi_trx,
        idempotency_key=f"pc-{pengeluaran.id}-{uuid.uuid4()}"
    )
    pengeluaran.mutasi = mutasi
    pengeluaran.save(update_fields=['mutasi'])

    # 4. Tembak otomatis ke Jurnal Akunting (Beban vs Kas)
    posting(
        kejadian='BEBAN_KAS',
        entitas_id=entitas_id,
        tanggal=timezone.localdate(),
        referensi=referensi_trx,
        nilai={'nominal': nominal},
        idem_key=mutasi.idempotency_key,
        user=user,
        keterangan=f"Kas Kecil: {keterangan}"
    )

    return pengeluaran