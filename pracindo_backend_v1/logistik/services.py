"""
Logika bisnis logistik — logistik/services.py

SATU ATURAN DI ATAS SEGALANYA

    Modul ini tidak pernah menulis stok. Tidak lewat model, tidak lewat
    inventory.services, tidak lewat mana pun. Warehouse yang menulis, dan
    logistik hanya memicu lewat integrasi_warehouse.

APA YANG BOLEH OFFLINE

    Bukti terima dan retur boleh diantre klien: keduanya append-only, tidak
    berebut sumber daya, dan urutan pengirimannya tidak mengubah hasil.

    Perubahan status pengiriman TIDAK boleh diantre. Kurir yang mengantre
    "berangkat" berarti sistem mengira dia di jalan padahal belum, dan
    petugas gudang membuat keputusan muatan berdasarkan itu.
"""
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from . import integrasi_warehouse as gudang
from . import peta
from .models import (
    BuktiTerima, JejakPosisi, Pengiriman, Perhentian, Retur,
    StatusPengiriman, StatusPerhentian, TarifOngkos,
)

# Jejak posisi lebih lama dari ini dihapus. Sengketa pengiriman selalu muncul
# dalam hitungan hari; menyimpan berbulan-bulan menambah risiko tanpa
# menambah kegunaan.
SIMPAN_JEJAK_HARI = 30


# =========================================================
# PERAKITAN
# =========================================================

def distribusi_tersedia(entitas_id=None):
    """
    Distribusi yang sudah dikurangi stoknya di warehouse tapi belum masuk
    pengiriman mana pun yang masih aktif.
    """
    calon = gudang.distribusi_siap_kirim(entitas_id=entitas_id)
    sudah_dipakai = set(
        Perhentian.objects
        .exclude(pengiriman__status=StatusPengiriman.BATAL)
        .values_list('distribusi_id', flat=True)
    )
    return [d for d in calon if d['id'] not in sudah_dipakai]


@transaction.atomic
def rakit_pengiriman(*, entitas_id, kurir_id, distribusi_ids, tanggal=None,
                     kendaraan_id=None, catatan='', user=None):
    """
    Membuat pengiriman DISIAPKAN beserta perhentiannya.

    Belum menyentuh apa pun di warehouse -- muatan masih bisa diubah sampai
    berangkatkan() dipanggil.
    """
    if not distribusi_ids:
        raise ValidationError('Pilih minimal satu distribusi untuk dikirim.')

    ganda = {d for d in distribusi_ids if distribusi_ids.count(d) > 1}
    if ganda:
        raise ValidationError(f'Distribusi dipilih lebih dari sekali: {sorted(ganda)}.')

    terpakai = set(
        Perhentian.objects
        .filter(distribusi_id__in=distribusi_ids)
        .exclude(pengiriman__status=StatusPengiriman.BATAL)
        .values_list('distribusi_id', flat=True)
    )
    if terpakai:
        raise ValidationError(
            f'Distribusi berikut sudah masuk pengiriman lain: {sorted(terpakai)}.'
        )

    kirim = Pengiriman.objects.create(
        entitas_id=entitas_id,
        tanggal=tanggal or timezone.localdate(),
        kurir_id=kurir_id,
        kendaraan_id=kendaraan_id,
        catatan=catatan,
        dibuat_oleh=user,
    )

    for urut, dist_id in enumerate(distribusi_ids, start=1):
        rincian = gudang.rincian_distribusi(dist_id)
        Perhentian.objects.create(
            pengiriman=kirim,
            distribusi_id=dist_id,
            # Disalin, bukan dirujuk. Riwayat perjalanan harus tetap terbaca
            # walau data pelanggan di hulu berubah nanti.
            nomor_distribusi=rincian.get('nomor', ''),
            pelanggan_nama=rincian.get('pelanggan_nama', ''),
            alamat=rincian.get('alamat', ''),
            lat=rincian.get('lat'),
            lng=rincian.get('lng'),
            urutan=urut,
        )

    hitung_rute(kirim.id)
    return kirim


@transaction.atomic
def hitung_rute(pengiriman_id, *, pakai_usulan=False):
    """
    Menghitung jarak dan waktu tiap perhentian, dan menyimpan urutan usulan.

    pakai_usulan=True menerapkan urutan usulan sebagai urutan sebenarnya.
    Default False: usulan disimpan tapi TIDAK menimpa urutan yang sudah ada.
    Kurir yang hafal jalan sering lebih benar daripada garis lurus.
    """
    kirim = Pengiriman.objects.select_for_update().get(pk=pengiriman_id)
    if kirim.status in (StatusPengiriman.SELESAI, StatusPengiriman.BATAL):
        raise ValidationError('Rute pengiriman yang sudah tuntas tidak dihitung ulang.')

    baris = list(kirim.perhentian.all())
    if not baris:
        return kirim

    usulan = peta.urutkan_terdekat(
        None,
        [{'id': b.id, 'lat': b.lat, 'lng': b.lng} for b in baris],
    )
    peringkat = {pid: i + 1 for i, pid in enumerate(usulan)}
    for b in baris:
        b.urutan_usulan = peringkat.get(b.id)

    if pakai_usulan:
        for b in baris:
            b.urutan = b.urutan_usulan or b.urutan

    baris.sort(key=lambda b: b.urutan)

    total = Decimal('0')
    sebelum = None
    for b in baris:
        if sebelum is None:
            b.jarak_dari_sebelum_km = Decimal('0.00')
        else:
            b.jarak_dari_sebelum_km = peta.jarak_perkiraan(
                sebelum.lat, sebelum.lng, b.lat, b.lng)
        b.estimasi_menit = peta.menit_perkiraan(b.jarak_dari_sebelum_km)
        total += b.jarak_dari_sebelum_km
        sebelum = b
        b.save(update_fields=['urutan', 'urutan_usulan',
                              'jarak_dari_sebelum_km', 'estimasi_menit'])

    tarif = TarifOngkos.berlaku(kirim.tanggal)
    kirim.jarak_total_km = total
    kirim.ongkos_perkiraan = (
        (tarif.biaya_tetap + total * tarif.tarif_per_km).quantize(Decimal('0.01'))
        if tarif else Decimal('0')
    )
    kirim.save(update_fields=['jarak_total_km', 'ongkos_perkiraan'])
    return kirim


# =========================================================
# ALUR PERJALANAN
# =========================================================

@transaction.atomic
def berangkatkan(*, pengiriman_id, oleh):
    kirim = Pengiriman.objects.select_for_update().get(pk=pengiriman_id)
    if kirim.status != StatusPengiriman.DISIAPKAN:
        raise ValidationError(
            f'Pengiriman sudah {kirim.get_status_display()}.')
    if not kirim.perhentian.exists():
        raise ValidationError('Pengiriman tanpa perhentian tidak bisa berangkat.')

    kirim.status = StatusPengiriman.BERANGKAT
    kirim.waktu_berangkat = timezone.now()
    kirim.save(update_fields=['status', 'waktu_berangkat'])
    return kirim


@transaction.atomic
def batalkan_pengiriman(*, pengiriman_id, alasan=''):
    """
    Hanya pengiriman DISIAPKAN. Distribusi kembali ke antrean perakitan,
    dan stok TIDAK dikembalikan -- stok berkurang saat warehouse membuat
    Distribusi, jauh sebelum logistik terlibat.
    """
    kirim = Pengiriman.objects.select_for_update().get(pk=pengiriman_id)
    if kirim.status != StatusPengiriman.DISIAPKAN:
        raise ValidationError(
            'Pengiriman yang sudah berangkat tidak bisa dibatalkan. '
            'Catat retur pada perhentian yang tidak jadi.'
        )
    kirim.status = StatusPengiriman.BATAL
    kirim.catatan = f'{kirim.catatan}\n[BATAL] {alasan}'.strip()
    kirim.save(update_fields=['status', 'catatan'])
    return kirim


@transaction.atomic
def tandai_sampai(*, perhentian_id, oleh):
    hentian = Perhentian.objects.select_for_update().select_related('pengiriman').get(
        pk=perhentian_id)
    if hentian.pengiriman.status != StatusPengiriman.BERANGKAT:
        raise ValidationError('Pengiriman belum berangkat.')
    if hentian.tuntas:
        raise ValidationError(
            f'Perhentian sudah {hentian.get_status_display()}.')

    hentian.status = StatusPerhentian.SAMPAI
    hentian.waktu_sampai = timezone.now()
    hentian.save(update_fields=['status', 'waktu_sampai'])
    return hentian


def _tutup_bila_tuntas(kirim):
    """Pengiriman selesai sendiri begitu semua perhentiannya tuntas."""
    if kirim.status == StatusPengiriman.BERANGKAT and kirim.semua_perhentian_tuntas:
        kirim.status = StatusPengiriman.SELESAI
        kirim.waktu_selesai = timezone.now()
        kirim.save(update_fields=['status', 'waktu_selesai'])


# =========================================================
# BUKTI TERIMA
# =========================================================

@transaction.atomic
def unggah_bukti(*, perhentian_id, foto, oleh, catatan='',
                 lat=None, lng=None, idem_key=''):
    """
    Bukti terima = foto. Boleh datang dari antrean offline berjam-jam
    kemudian, jadi status pengiriman TIDAK diwajibkan BERANGKAT di sini --
    yang diwajibkan hanya pengirimannya belum dibatalkan.
    """
    if idem_key:
        ada = BuktiTerima.objects.filter(idem_key=idem_key).first()
        if ada:
            return ada

    hentian = Perhentian.objects.select_for_update().select_related('pengiriman').get(
        pk=perhentian_id)
    kirim = hentian.pengiriman

    if kirim.status == StatusPengiriman.BATAL:
        raise ValidationError('Pengiriman sudah dibatalkan.')
    if hentian.status == StatusPerhentian.DIRETUR:
        raise ValidationError('Perhentian ini sudah dicatat sebagai retur.')

    bukti = BuktiTerima.objects.create(
        perhentian=hentian, foto=foto, catatan=catatan,
        lat=lat, lng=lng, diunggah_oleh=oleh, idem_key=idem_key,
    )

    if hentian.status != StatusPerhentian.DITERIMA:
        hentian.status = StatusPerhentian.DITERIMA
        if not hentian.waktu_sampai:
            hentian.waktu_sampai = timezone.now()
        hentian.save(update_fields=['status', 'waktu_sampai'])
        gudang.tandai_terkirim(hentian.distribusi_id, waktu=timezone.now(), oleh=oleh)

    _tutup_bila_tuntas(kirim)
    return bukti


# =========================================================
# RETUR
# =========================================================

@transaction.atomic
def catat_retur(*, perhentian_id, alasan, oleh, foto=None, idem_key=''):
    """
    Mencatat penolakan. Stok BELUM kembali -- butuh persetujuan Supervisor,
    dan pengembaliannya dieksekusi warehouse.
    """
    if not alasan.strip():
        raise ValidationError('Alasan retur wajib diisi.')

    if idem_key:
        ada = Retur.objects.filter(idem_key=idem_key).first()
        if ada:
            return ada

    hentian = Perhentian.objects.select_for_update().select_related('pengiriman').get(
        pk=perhentian_id)
    if hentian.pengiriman.status == StatusPengiriman.BATAL:
        raise ValidationError('Pengiriman sudah dibatalkan.')
    if hentian.status == StatusPerhentian.DITERIMA:
        raise ValidationError(
            'Perhentian sudah diterima. Retur setelah barang diterima '
            'ditangani lewat retur penjualan, bukan lewat pengiriman.'
        )

    retur = Retur.objects.create(
        perhentian=hentian, alasan=alasan, foto=foto, dicatat_oleh=oleh,
        idem_key=idem_key,
    )
    hentian.status = StatusPerhentian.DIRETUR
    hentian.save(update_fields=['status'])
    _tutup_bila_tuntas(hentian.pengiriman)
    return retur


@transaction.atomic
def setujui_retur(*, retur_id, oleh):
    """
    Supervisor menyetujui, lalu warehouse mengembalikan stok.

    Warehouse yang menentukan barang kembali ke stok badan hukum mana --
    stiker sudah menutup klaimnya, jadi tidak ada pembagian yang perlu
    dihitung ulang di sini.
    """
    if not getattr(oleh, 'supervisor', False):
        raise ValidationError('Hanya Supervisor yang boleh menyetujui retur.')

    retur = Retur.objects.select_for_update().select_related('perhentian').get(pk=retur_id)
    if retur.stok_dikembalikan:
        raise ValidationError('Retur ini sudah disetujui sebelumnya.')

    gudang.kembalikan_stok(
        retur.perhentian.distribusi_id, alasan=retur.alasan, oleh=oleh)

    retur.disetujui_oleh = oleh
    retur.disetujui_pada = timezone.now()
    retur.stok_dikembalikan = True
    retur.save(update_fields=['disetujui_oleh', 'disetujui_pada', 'stok_dikembalikan'])
    return retur


# =========================================================
# PELACAKAN
# =========================================================

@transaction.atomic
def catat_posisi(*, pengiriman_id, lat, lng, akurasi_m=None, oleh=None):
    """
    Posisi HANYA direkam saat pengiriman berstatus BERANGKAT.

    Penolakan di sini disengaja, bukan sekadar mengandalkan klien berhenti
    mengirim. Aplikasi yang lupa mematikan pelacakan akan terus mengirim,
    dan merekamnya berarti melacak kurir di luar jam bertugas.
    """
    kirim = Pengiriman.objects.get(pk=pengiriman_id)
    if kirim.status != StatusPengiriman.BERANGKAT:
        raise ValidationError('Posisi hanya direkam saat pengiriman berjalan.')
    if oleh is not None and kirim.kurir_id != oleh.id:
        raise ValidationError('Anda bukan kurir pengiriman ini.')

    return JejakPosisi.objects.create(
        pengiriman=kirim, lat=lat, lng=lng, akurasi_m=akurasi_m)


def bersihkan_jejak_lama(hari=SIMPAN_JEJAK_HARI):
    """Dipanggil terjadwal. Kembalikan jumlah baris yang dihapus."""
    batas = timezone.now() - timedelta(days=hari)
    jumlah, _ = JejakPosisi.objects.filter(waktu__lt=batas).delete()
    return jumlah


# =========================================================
# LAPORAN
# =========================================================

def ringkasan_pengiriman(pengiriman_id):
    kirim = (Pengiriman.objects
             .select_related('kurir', 'kendaraan', 'entitas')
             .prefetch_related('perhentian__bukti', 'perhentian__retur')
             .get(pk=pengiriman_id))

    return {
        'nomor': kirim.nomor,
        'tanggal': kirim.tanggal,
        'status': kirim.status,
        'status_label': kirim.get_status_display(),
        'kurir': kirim.kurir.nama_lengkap,
        'kendaraan': kirim.kendaraan.nama if kirim.kendaraan_id else None,
        'jarak_total_km': kirim.jarak_total_km,
        'ongkos_perkiraan': kirim.ongkos_perkiraan,
        'perhentian': [
            {
                'id': h.id,
                'urutan': h.urutan,
                'pelanggan': h.pelanggan_nama,
                'alamat': h.alamat,
                'status': h.status,
                'jumlah_bukti': h.bukti.count(),
                'diretur': hasattr(h, 'retur'),
            }
            for h in kirim.perhentian.all()
        ],
    }
