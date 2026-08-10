"""
Logika bisnis Papan Tugas — work_order/services.py

Berkas ini sebelumnya hanya berisi stub. Logika transaksi ada di serializer
dan mesin aturan ada di view, dan itu bertentangan dengan pola `produksi`
dan `staff_user` yang keduanya menaruh logika di services.

Sekarang semuanya di sini. View jadi penerjemah HTTP, serializer jadi
penerjemah bentuk.

CATATAN TENTANG IDENTITAS PENGGUNA
    AUTH_USER_MODEL ADALAH staff_user.Profil, dan WorkOrderPenugasan.staff
    menunjuk model yang sama. Jadi request.user.id LANGSUNG cocok dengan
    penugasan.staff_id.

    Versi sebelumnya memakai getattr(user, 'profil_staff_id', None), atribut
    yang tidak pernah ada. getattr dengan default None membuatnya gagal tanpa
    suara: approve selalu menjawab 403 untuk semua orang, dan mading hanya
    memunculkan kategori PRODUKSI. Tidak ada error di log.
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Q
from django.utils.timezone import now

from .models import (
    AturanSelesai, DetailPesananProduksi, Kategori, WorkOrder,
    WorkOrderPenugasan, WorkOrderPesan,
)


# =========================================================
# VISIBILITAS
# =========================================================

def wo_terlihat(qs, user):
    """
    Menyaring queryset ke Work Order yang boleh dilihat `user`.

    HARUS dipanggil dari get_queryset(), bukan diandalkan lewat
    has_object_permission. Izin objek di DRF TIDAK berlaku untuk endpoint
    list -- mengandalkannya berarti GET daftar mengembalikan seluruh WO
    termasuk yang berkategori PRIVATE milik orang lain.

    KEPUTUSAN: PRIVATE tetap privat, termasuk dari Supervisor.
    Kategorinya secara harfiah bernama "Pesan Pribadi / Rahasia". Kalau
    Supervisor bisa membacanya, dia tidak privat, dan orang akan kembali
    memakai WhatsApp -- yang justru masalah yang mau dipecahkan modul ini.
    Superuser lolos karena dia memang bisa membaca basis data langsung.

    Kalau kebijakan ini diubah, ubah di sini saja -- tidak ada tempat lain
    yang memutuskan visibilitas.
    """
    if user.is_superuser:
        return qs

    terlihat = (
        Q(kategori=Kategori.PRODUKSI)
        | Q(dibuat_oleh=user)
        | Q(penugasan__staff=user)
    )
    if getattr(user, 'supervisor', False):
        terlihat |= ~Q(kategori=Kategori.PRIVATE)

    return qs.filter(terlihat).distinct()


def boleh_ubah(wo, user):
    """Hanya pembuat, Supervisor, dan superuser yang boleh menyunting."""
    return (user.is_superuser
            or getattr(user, 'supervisor', False)
            or wo.dibuat_oleh_id == user.id)


def mading(qs, user):
    """
    Papan: yang belum selesai, tenggat terdekat di atas.

    Penyaringan `selesai` terjadi di SERVER. Menyaringnya di klien hanya
    bekerja pada halaman pertama, dan papan diam-diam menyembunyikan tugas
    aktif begitu jumlahnya melewati satu halaman.
    """
    return (
        wo_terlihat(qs, user)
        .filter(selesai=False)
        .order_by(F('deadline').asc(nulls_last=True), '-dibuat_pada')
    )


# =========================================================
# PEMBUATAN & PENYUNTINGAN
# =========================================================

def _validasi(kategori, aturan, staff_ids, pic_id, detail_produksi):
    if not staff_ids:
        raise ValidationError('Tandai minimal satu staf.')

    ganda = {s for s in staff_ids if staff_ids.count(s) > 1}
    if ganda:
        raise ValidationError(f'Staf ditandai lebih dari sekali: {sorted(ganda)}.')

    if pic_id is not None and pic_id not in staff_ids:
        raise ValidationError('PIC harus termasuk staf yang ditandai.')

    # Tanpa ini, WO beraturan PIC tanpa PIC tidak bisa diselesaikan siapa pun
    # -- dan itu baru ketahuan saat orang sudah mengerjakan tugasnya.
    if aturan == AturanSelesai.PIC and pic_id is None:
        raise ValidationError(
            'Aturan "Hanya PIC" membutuhkan satu penanggung jawab.')

    if kategori == Kategori.PRODUKSI and not detail_produksi:
        raise ValidationError(
            'Work Order kategori Produksi wajib mengisi rincian pesanan.')

    if kategori != Kategori.PRODUKSI and detail_produksi:
        raise ValidationError(
            'Rincian pesanan produksi hanya untuk kategori Produksi.')


@transaction.atomic
def buat_wo(*, user, judul, kategori=Kategori.UMUM,
            aturan_penyelesaian=AturanSelesai.SALAH_SATU, deskripsi='',
            tanggal=None, deadline=None, staff_ids=None, pic_id=None,
            detail_produksi=None):
    staff_ids = list(staff_ids or [])
    _validasi(kategori, aturan_penyelesaian, staff_ids, pic_id, detail_produksi)

    wo = WorkOrder(
        judul=judul, kategori=kategori, deskripsi=deskripsi,
        aturan_penyelesaian=aturan_penyelesaian, deadline=deadline,
        dibuat_oleh=user,
    )
    if tanggal:
        wo.tanggal = tanggal
    wo.save()

    if detail_produksi:
        DetailPesananProduksi.objects.create(work_order=wo, **detail_produksi)

    for sid in staff_ids:
        WorkOrderPenugasan.objects.create(
            work_order=wo, staff_id=sid, is_pic=(sid == pic_id))

    return wo


@transaction.atomic
def ubah_wo(*, wo_id, user, staff_ids=None, pic_id=None,
            detail_produksi=None, **field):
    """
    Menyunting WO, termasuk mengganti daftar staf yang ditandai.

    Penugasan yang tetap ada TIDAK direset -- `is_selesai_personal` milik
    orang yang sudah menandai bagiannya dipertahankan. Menghapus lalu
    membuat ulang seluruh penugasan akan menghanguskan konfirmasi mereka
    tanpa ada yang menyadarinya.
    """
    wo = WorkOrder.objects.select_for_update().get(pk=wo_id)
    if wo.selesai:
        raise ValidationError('Work Order yang sudah selesai tidak bisa diubah.')
    if not boleh_ubah(wo, user):
        raise ValidationError('Hanya pembuat atau Supervisor yang boleh mengubah.')

    kategori = field.get('kategori', wo.kategori)
    aturan = field.get('aturan_penyelesaian', wo.aturan_penyelesaian)

    if staff_ids is None:
        daftar = list(wo.penugasan.values_list('staff_id', flat=True))
        pic_kini = wo.penugasan.filter(is_pic=True).values_list('staff_id', flat=True).first()
        pic_efektif = pic_id if pic_id is not None else pic_kini
    else:
        daftar = list(staff_ids)
        pic_efektif = pic_id

    detail_efektif = detail_produksi
    if detail_efektif is None and kategori == Kategori.PRODUKSI:
        detail_efektif = getattr(wo, 'detail_produksi', None) and True

    _validasi(kategori, aturan, daftar, pic_efektif, detail_efektif)

    for nama, nilai in field.items():
        setattr(wo, nama, nilai)
    wo.save()

    if staff_ids is not None:
        _sinkron_penugasan(wo, daftar, pic_efektif)
    elif pic_id is not None:
        wo.penugasan.update(is_pic=False)
        wo.penugasan.filter(staff_id=pic_id).update(is_pic=True)

    if detail_produksi:
        DetailPesananProduksi.objects.update_or_create(
            work_order=wo, defaults=detail_produksi)

    return wo


def _sinkron_penugasan(wo, staff_ids, pic_id):
    kini = set(wo.penugasan.values_list('staff_id', flat=True))
    baru = set(staff_ids)

    wo.penugasan.filter(staff_id__in=(kini - baru)).delete()
    # PIC dikosongkan lebih dulu supaya unique constraint PIC tunggal tidak
    # bentrok saat PIC berpindah orang dalam satu transaksi.
    wo.penugasan.update(is_pic=False)

    for sid in (baru - kini):
        WorkOrderPenugasan.objects.create(work_order=wo, staff_id=sid)
    if pic_id is not None:
        wo.penugasan.filter(staff_id=pic_id).update(is_pic=True)


# =========================================================
# MESIN ATURAN PENYELESAIAN
# =========================================================

@transaction.atomic
def setujui(*, wo_id, user, catatan=''):
    """
    Menjalankan aturan penyelesaian. Return (wo, pesan, tuntas).

    `tuntas` False berarti konfirmasi tersimpan tapi WO masih terbuka --
    itu terjadi pada aturan SEMUA saat masih ada anggota lain.
    """
    wo = WorkOrder.objects.select_for_update().get(pk=wo_id)

    if wo.selesai:
        raise ValidationError('Tugas sudah diselesaikan sebelumnya.')

    penugasan = wo.penugasan.filter(staff_id=user.id).first()
    if penugasan is None:
        # Supervisor boleh menutup paksa tanpa ditandai. Tanpa jalur ini,
        # WO yang orangnya sudah keluar dari perusahaan akan menggantung
        # selamanya di papan semua orang.
        if not (user.is_superuser or getattr(user, 'supervisor', False)):
            raise ValidationError('Anda tidak berhak menyetujui tugas ini.')
        return _tutup(wo, user, catatan), 'Tugas ditutup oleh Supervisor.', True

    aturan = wo.aturan_penyelesaian

    if aturan == AturanSelesai.PIC and not penugasan.is_pic:
        raise ValidationError(
            'Hanya penanggung jawab (PIC) yang dapat menyelesaikan tugas ini.')

    if aturan == AturanSelesai.SEMUA:
        if not penugasan.is_selesai_personal:
            penugasan.is_selesai_personal = True
            penugasan.save(update_fields=['is_selesai_personal'])

        if wo.penugasan.filter(is_selesai_personal=False).exists():
            sudah, total = wo.progres_penyelesaian
            return (wo,
                    f'Konfirmasi Anda tersimpan. {sudah} dari {total} anggota '
                    f'sudah menandai, menunggu sisanya.',
                    False)

    # Semua cabang tersisa berarti tuntas. Struktur ini disengaja: versi
    # sebelumnya bisa jatuh ke akhir fungsi tanpa return apa pun, dan Django
    # menjawabnya dengan "view didn't return an HttpResponse" -- 500 yang
    # penyebabnya tidak kelihatan dari pesannya.
    return _tutup(wo, user, catatan), 'Tugas berhasil diselesaikan.', True


def _tutup(wo, user, catatan):
    wo.selesai = True
    wo.waktu_selesai = now()
    wo.diselesaikan_oleh = user
    wo.catatan_selesai = catatan
    wo.save(update_fields=['selesai', 'waktu_selesai',
                           'diselesaikan_oleh', 'catatan_selesai'])
    return wo


@transaction.atomic
def buka_kembali(*, wo_id, user, alasan=''):
    """Hanya Supervisor. Pelaksana tidak bisa membuka WO yang sudah ditutup."""
    if not (user.is_superuser or getattr(user, 'supervisor', False)):
        raise ValidationError('Hanya Supervisor yang boleh membuka kembali tugas.')

    wo = WorkOrder.objects.select_for_update().get(pk=wo_id)
    if not wo.selesai:
        raise ValidationError('Tugas ini belum ditutup.')

    wo.selesai = False
    wo.waktu_selesai = None
    wo.diselesaikan_oleh = None
    wo.catatan_selesai = f'{wo.catatan_selesai}\n[DIBUKA LAGI] {alasan}'.strip()
    wo.save(update_fields=['selesai', 'waktu_selesai',
                           'diselesaikan_oleh', 'catatan_selesai'])
    wo.penugasan.update(is_selesai_personal=False)
    return wo


# =========================================================
# DISKUSI
# =========================================================

def kirim_pesan(*, wo_id, user, teks):
    teks = (teks or '').strip()
    if not teks:
        raise ValidationError('Teks pesan tidak boleh kosong.')
    return WorkOrderPesan.objects.create(
        work_order_id=wo_id, pengirim=user, teks=teks)
