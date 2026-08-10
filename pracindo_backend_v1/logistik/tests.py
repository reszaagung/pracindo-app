"""
Tes logistik — logistik/tests.py

PENEKANANNYA: modul ini TIDAK BOLEH MENULIS STOK, dan kurir TIDAK BOLEH
MELIHAT PERJALANAN ORANG LAIN.

Keduanya jenis kesalahan yang tidak menimbulkan error. Stok yang berkurang
dua kali baru ketahuan saat opname; kebocoran data kurir tidak pernah
ketahuan sama sekali kecuali ada yang mencari.

------------------------------------------------------------------------
CATATAN PENYESUAIAN

setUpTestData() membuat objek dari core dan staff_user yang nama field-nya
mungkin berbeda. Kalau ada tes gagal saat setup, perbaikannya di blok itu
saja -- badan tesnya tidak bergantung pada nama field tersebut.

Sambungan warehouse ditambal (patch) di semua tes, karena app itu belum ada.
Tambalan itu SEKALIGUS ALAT UJI: kalau kode logistik diam-diam menulis stok
sendiri, panggilan ke tambalan ini tidak akan tercatat dan tesnya gagal.
------------------------------------------------------------------------
"""
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Entitas
from staff_user.models import Role

from .models import (
    Kendaraan, Pengiriman, Perhentian, Retur, StatusPengiriman,
    StatusPerhentian, TarifOngkos,
)

User = get_user_model()

# Satu piksel PNG. Cukup untuk ImageField tanpa berkas contoh.
PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
    b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)

DISTRIBUSI = {
    101: {'id': 101, 'nomor': 'DIST/2026/08/001', 'pelanggan_nama': 'Toko Jaya',
          'alamat': 'Jl. Merdeka 1', 'lat': Decimal('-6.2000'), 'lng': Decimal('106.8160')},
    102: {'id': 102, 'nomor': 'DIST/2026/08/002', 'pelanggan_nama': 'Toko Sentosa',
          'alamat': 'Jl. Sudirman 9', 'lat': Decimal('-6.2250'), 'lng': Decimal('106.8000')},
    103: {'id': 103, 'nomor': 'DIST/2026/08/003', 'pelanggan_nama': 'Toko Makmur',
          'alamat': 'Jl. Thamrin 5', 'lat': Decimal('-6.1900'), 'lng': Decimal('106.8230')},
}


def foto():
    return SimpleUploadedFile('bukti.png', PNG, content_type='image/png')


class BasisLogistik(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.entitas = Entitas.objects.create(kode='PCJM', nama='PT Pracindo Jaya Mandiri')

        cls.petugas = User.objects.create_user(
            username='gudang1', password='rahasia123', role=Role.GUDANG)
        cls.kurir = User.objects.create_user(
            username='kurir1', password='rahasia123', role=Role.KURIR)
        cls.kurir_lain = User.objects.create_user(
            username='kurir2', password='rahasia123', role=Role.KURIR)
        cls.bos = User.objects.create_superuser(
            username='bos', password='rahasia123', email='bos@pracindo.test')

        cls.mobil = Kendaraan.objects.create(kode='L300', nama='Mitsubishi L300')
        TarifOngkos.objects.create(
            tarif_per_km=Decimal('3500'), biaya_tetap=Decimal('20000'))

    def setUp(self):
        self.client.force_authenticate(self.petugas)

        self.p_siap = patch(
            'logistik.services.gudang.distribusi_siap_kirim',
            side_effect=lambda entitas_id=None: list(DISTRIBUSI.values()))
        self.p_rinci = patch(
            'logistik.services.gudang.rincian_distribusi',
            side_effect=lambda did: DISTRIBUSI[did])
        self.p_kirim = patch('logistik.services.gudang.tandai_terkirim')
        self.p_balik = patch('logistik.services.gudang.kembalikan_stok')

        self.p_siap.start(); self.p_rinci.start()
        self.mock_terkirim = self.p_kirim.start()
        self.mock_kembalikan = self.p_balik.start()
        self.addCleanup(self.p_siap.stop)
        self.addCleanup(self.p_rinci.stop)
        self.addCleanup(self.p_kirim.stop)
        self.addCleanup(self.p_balik.stop)

    def rakit(self, ids=(101, 102), kurir=None):
        return self.client.post(reverse('logistik:pengiriman-list'), {
            'entitas_id': self.entitas.id,
            'kurir_id': (kurir or self.kurir).id,
            'distribusi_ids': list(ids),
            'kendaraan_id': self.mobil.id,
        }, format='json')


class AlurPengirimanTest(BasisLogistik):

    def test_alur_penuh(self):
        r = self.rakit()
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.data)
        kid = r.data['id']
        self.assertEqual(r.data['status'], 'DISIAPKAN')
        self.assertEqual(len(r.data['perhentian']), 2)
        self.assertGreater(Decimal(r.data['ongkos_perkiraan']), 0)

        r = self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kid]))
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.data)
        self.assertEqual(r.data['status'], 'BERANGKAT')

        hid = [h['id'] for h in r.data['perhentian']]

        for h in hid:
            r = self.client.post(
                f"/api/logistik/pengiriman/{kid}/perhentian/{h}/bukti/",
                {'foto': foto()}, format='multipart')
            self.assertEqual(r.status_code, status.HTTP_200_OK, r.data)

        kirim = Pengiriman.objects.get(pk=kid)
        self.assertEqual(kirim.status, StatusPengiriman.SELESAI)
        self.assertIsNotNone(kirim.waktu_selesai)

    def test_tidak_bisa_berangkat_tanpa_perhentian(self):
        kirim = Pengiriman.objects.create(
            entitas=self.entitas, kurir=self.kurir, dibuat_oleh=self.petugas)
        r = self.client.post(
            reverse('logistik:pengiriman-berangkatkan', args=[kirim.id]))
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_distribusi_tidak_bisa_masuk_dua_pengiriman(self):
        self.rakit(ids=(101,))
        r = self.rakit(ids=(101, 102))
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('101', r.data['detail'])

    def test_batalkan_hanya_saat_disiapkan(self):
        kid = self.rakit().data['id']
        self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kid]))
        r = self.client.post(
            reverse('logistik:pengiriman-batalkan', args=[kid]),
            {'alasan': 'Truk mogok.'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_patch_delete_405(self):
        kid = self.rakit().data['id']
        url = reverse('logistik:pengiriman-detail', args=[kid])
        for metode in (self.client.put, self.client.patch, self.client.delete):
            r = metode(url, {'status': 'SELESAI'}, format='json')
            self.assertEqual(r.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class TidakMenulisStokTest(BasisLogistik):
    """
    Batas modul: logistik tidak pernah menulis stok, hanya memicu warehouse.
    """

    def test_merakit_tidak_memicu_warehouse(self):
        self.rakit()
        self.mock_terkirim.assert_not_called()
        self.mock_kembalikan.assert_not_called()

    def test_berangkat_tidak_memicu_warehouse(self):
        kid = self.rakit().data['id']
        self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kid]))
        self.mock_terkirim.assert_not_called()

    def test_bukti_terima_memicu_tandai_terkirim_sekali(self):
        kid = self.rakit(ids=(101,)).data['id']
        self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kid]))
        hid = Perhentian.objects.get(pengiriman_id=kid).id

        self.client.post(
            f"/api/logistik/pengiriman/{kid}/perhentian/{hid}/bukti/",
            {'foto': foto()}, format='multipart')
        self.assertEqual(self.mock_terkirim.call_count, 1)

        # Foto kedua untuk perhentian yang sama tidak memicu ulang.
        self.client.post(
            f"/api/logistik/pengiriman/{kid}/perhentian/{hid}/bukti/",
            {'foto': foto()}, format='multipart')
        self.assertEqual(self.mock_terkirim.call_count, 1)

    def test_batal_tidak_mengembalikan_stok(self):
        kid = self.rakit().data['id']
        self.client.post(
            reverse('logistik:pengiriman-batalkan', args=[kid]),
            {'alasan': 'Salah muat.'}, format='json')
        self.mock_kembalikan.assert_not_called()


class IdempotensiTest(BasisLogistik):

    def test_kunci_sama_tidak_membuat_dua_bukti(self):
        kid = self.rakit(ids=(101,)).data['id']
        self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kid]))
        hid = Perhentian.objects.get(pengiriman_id=kid).id
        url = f"/api/logistik/pengiriman/{kid}/perhentian/{hid}/bukti/"
        kunci = 'a1b2c3d4-0000-4000-8000-000000000001'

        self.client.post(url, {'foto': foto()}, format='multipart',
                         HTTP_IDEMPOTENCY_KEY=kunci)
        self.client.post(url, {'foto': foto()}, format='multipart',
                         HTTP_IDEMPOTENCY_KEY=kunci)

        hentian = Perhentian.objects.get(pk=hid)
        self.assertEqual(hentian.bukti.count(), 1)


class ReturTest(BasisLogistik):

    def _retur(self):
        kid = self.rakit(ids=(101,)).data['id']
        self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kid]))
        hid = Perhentian.objects.get(pengiriman_id=kid).id
        r = self.client.post(
            f"/api/logistik/pengiriman/{kid}/perhentian/{hid}/retur/",
            {'alasan': 'Kemasan penyok, ditolak pembeli.'}, format='multipart')
        return kid, hid, r

    def test_retur_tidak_langsung_mengembalikan_stok(self):
        _, hid, r = self._retur()
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.data)
        self.assertEqual(
            Perhentian.objects.get(pk=hid).status, StatusPerhentian.DIRETUR)
        self.mock_kembalikan.assert_not_called()

        retur = Retur.objects.get(perhentian_id=hid)
        self.assertFalse(retur.stok_dikembalikan)

    def test_hanya_supervisor_yang_menyetujui(self):
        _, hid, _ = self._retur()
        retur = Retur.objects.get(perhentian_id=hid)

        r = self.client.post(reverse('logistik:retur-setujui', args=[retur.id]))
        self.assertIn(r.status_code,
                      (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED))
        self.mock_kembalikan.assert_not_called()

        self.client.force_authenticate(self.bos)
        r = self.client.post(reverse('logistik:retur-setujui', args=[retur.id]))
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.data)
        self.mock_kembalikan.assert_called_once()
        self.assertTrue(Retur.objects.get(pk=retur.id).stok_dikembalikan)

    def test_alasan_wajib(self):
        kid = self.rakit(ids=(101,)).data['id']
        self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kid]))
        hid = Perhentian.objects.get(pengiriman_id=kid).id
        r = self.client.post(
            f"/api/logistik/pengiriman/{kid}/perhentian/{hid}/retur/",
            {'alasan': ''}, format='multipart')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class PelacakanTest(BasisLogistik):

    def test_posisi_ditolak_sebelum_berangkat(self):
        kid = self.rakit().data['id']
        self.client.force_authenticate(self.kurir)
        r = self.client.post(
            reverse('logistik:pengiriman-posisi', args=[kid]),
            {'lat': '-6.2', 'lng': '106.8'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_posisi_diterima_saat_berangkat(self):
        kid = self.rakit().data['id']
        self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kid]))
        self.client.force_authenticate(self.kurir)
        r = self.client.post(
            reverse('logistik:pengiriman-posisi', args=[kid]),
            {'lat': '-6.2', 'lng': '106.8'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Pengiriman.objects.get(pk=kid).jejak.count(), 1)

    def test_posisi_ditolak_setelah_selesai(self):
        kid = self.rakit(ids=(101,)).data['id']
        self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kid]))
        hid = Perhentian.objects.get(pengiriman_id=kid).id
        self.client.post(
            f"/api/logistik/pengiriman/{kid}/perhentian/{hid}/bukti/",
            {'foto': foto()}, format='multipart')

        self.client.force_authenticate(self.kurir)
        r = self.client.post(
            reverse('logistik:pengiriman-posisi', args=[kid]),
            {'lat': '-6.2', 'lng': '106.8'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class CakupanKurirTest(BasisLogistik):
    """Kurir hanya melihat perjalanannya sendiri. Ini kebocoran yang senyap."""

    def test_kurir_tidak_melihat_pengiriman_kurir_lain(self):
        self.rakit(ids=(101,), kurir=self.kurir)
        self.rakit(ids=(102,), kurir=self.kurir_lain)

        self.client.force_authenticate(self.kurir)
        r = self.client.get(reverse('logistik:pengiriman-list'))
        hasil = r.data['results'] if isinstance(r.data, dict) else r.data
        self.assertEqual(len(hasil), 1)
        self.assertEqual(hasil[0]['kurir'], self.kurir.id)

    def test_kurir_tidak_bisa_membuka_pengiriman_orang_lain(self):
        kid = self.rakit(ids=(102,), kurir=self.kurir_lain).data['id']
        self.client.force_authenticate(self.kurir)
        r = self.client.get(reverse('logistik:pengiriman-detail', args=[kid]))
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_kurir_tidak_bisa_merakit_pengiriman(self):
        self.client.force_authenticate(self.kurir)
        r = self.rakit()
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_petugas_gudang_melihat_semua(self):
        self.rakit(ids=(101,), kurir=self.kurir)
        self.rakit(ids=(102,), kurir=self.kurir_lain)
        r = self.client.get(reverse('logistik:pengiriman-list'))
        hasil = r.data['results'] if isinstance(r.data, dict) else r.data
        self.assertEqual(len(hasil), 2)


class RuteTest(BasisLogistik):

    def test_urutan_usulan_tersimpan_tanpa_menimpa(self):
        kid = self.rakit(ids=(103, 101, 102)).data['id']
        baris = Perhentian.objects.filter(pengiriman_id=kid).order_by('urutan')

        # Urutan tetap sesuai masukan; usulan hanya tercatat.
        self.assertEqual([b.distribusi_id for b in baris], [103, 101, 102])
        self.assertTrue(all(b.urutan_usulan is not None for b in baris))

    def test_urutkan_manual_menimpa(self):
        kid = self.rakit(ids=(101, 102)).data['id']
        ids = list(Perhentian.objects.filter(pengiriman_id=kid)
                   .order_by('urutan').values_list('id', flat=True))

        r = self.client.post(
            reverse('logistik:pengiriman-urutkan', args=[kid]),
            {'urutan': list(reversed(ids))}, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.data)

        baru = list(Perhentian.objects.filter(pengiriman_id=kid)
                    .order_by('urutan').values_list('id', flat=True))
        self.assertEqual(baru, list(reversed(ids)))

    def test_urutan_harus_lengkap(self):
        kid = self.rakit(ids=(101, 102)).data['id']
        satu = Perhentian.objects.filter(pengiriman_id=kid).first().id
        r = self.client.post(
            reverse('logistik:pengiriman-urutkan', args=[kid]),
            {'urutan': [satu]}, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class SambunganBelumSiapTest(APITestCase):
    """
    Tanpa warehouse, endpoint perakitan menjawab 503 -- bukan 400 dan bukan
    daftar kosong. Daftar kosong akan membuat layar terlihat "tidak ada yang
    perlu dikirim" padahal sebenarnya belum tersambung.
    """

    def test_distribusi_tersedia_503(self):
        user = User.objects.create_superuser(
            username='bos2', password='rahasia123', email='b2@pracindo.test')
        self.client.force_authenticate(user)
        r = self.client.get(reverse('logistik:distribusi-tersedia'))
        self.assertEqual(r.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('warehouse', r.data['detail'].lower())
