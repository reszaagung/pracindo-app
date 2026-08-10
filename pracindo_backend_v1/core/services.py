"""
Service `core` — penguncian periode akuntansi.

pastikan_periode_terbuka() dipanggil empat app:
    warehouse.terima_barang()
    akunting.posting()
    keuangan.post_mutasi()
    inventory  — penyesuaian stok manual

Empat app, satu aturan. Itu sebabnya PeriodeAkuntansi tinggal di core:
kalau dia tinggal di akunting, keempatnya harus mengimpor akunting cuma
untuk memeriksa tanggal — dan inventory yang ada di lapis 3 jadi
bergantung ke lapis 4.
"""
from django.db import transaction
from django.utils import timezone

from .exceptions import PeriodeTertutup
from .models import PeriodeAkuntansi


def pastikan_periode_terbuka(entitas_id, tanggal):
    """
    Raise PeriodeTertutup kalau periode sudah dikunci. Return None kalau aman.

    Periode yang belum pernah dibuat dianggap TERBUKA. Penguncian bersifat
    opt-in — tidak ada yang tiba-tiba terkunci hanya karena barisnya belum
    ada di tabel.
    """
    tertutup = PeriodeAkuntansi.objects.filter(
        entitas_id=entitas_id,
        tahun=tanggal.year,
        bulan=tanggal.month,
        ditutup=True,
    ).exists()

    if tertutup:
        raise PeriodeTertutup(
            f'Periode {tanggal.month:02d}/{tanggal.year} sudah ditutup. '
            f'Gunakan jurnal balik bertanggal periode berjalan.'
        )


@transaction.atomic
def tutup_periode(entitas_id, tahun, bulan, user):
    """
    Idempoten — menutup periode yang sudah tertutup tidak melempar error.
    Pemanggil bertanggung jawab memastikan user adalah Supervisor.
    """
    periode, _ = PeriodeAkuntansi.objects.select_for_update().get_or_create(
        entitas_id=entitas_id, tahun=tahun, bulan=bulan,
    )
    if periode.ditutup:
        return periode

    periode.ditutup      = True
    periode.ditutup_pada = timezone.now()
    periode.ditutup_oleh = user
    periode.save(update_fields=['ditutup', 'ditutup_pada', 'ditutup_oleh'])
    return periode


@transaction.atomic
def buka_periode(entitas_id, tahun, bulan, user, alasan):
    """
    Membuka kembali periode tertutup. Alasan wajib diisi dan tersimpan
    permanen sebagai jejak audit.
    """
    if not alasan or not alasan.strip():
        raise ValueError('Alasan pembukaan periode wajib diisi.')

    periode = PeriodeAkuntansi.objects.select_for_update().get(
        entitas_id=entitas_id, tahun=tahun, bulan=bulan,
    )
    jejak = (
        f'[{timezone.now():%Y-%m-%d %H:%M}] dibuka oleh {user} — {alasan.strip()}'
    )
    periode.ditutup     = False
    periode.alasan_buka = f'{periode.alasan_buka}\n{jejak}'.strip()
    periode.save(update_fields=['ditutup', 'alasan_buka'])
    return periode
