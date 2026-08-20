"""
Tes logistik — logistik/tests.py
"""
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

# 1. Pastikan GrupBahan diimpor di sini
from core.models import Entitas, GrupBahan
from staff_user.models import Role

from .models import (
    Kendaraan, Pengiriman, Perhentian, Retur, StatusPengiriman,
    StatusPerhentian, TarifOngkos,
)

User = get_user_model()

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
        # 2. Buat GrupBahan dummy agar Entitas tidak error NotNullViolation
        cls.grup = GrupBahan.objects.create(kode='GB-TEST', nama='Grup Tes')
        cls.entitas = Entitas.objects.create(
            kode='PCJM', 
            nama='PT Pracindo Jaya Mandiri',
            grup_bahan=cls.grup
        )

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
        r = self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kid]))
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.data)
        for h in [h['id'] for h in r.data['perhentian']]:
            r = self.client.post(f"/api/v1/logistik/pengiriman/{kid}/perhentian/{h}/bukti/", {'foto': foto()}, format='multipart')
        self.assertEqual(Pengiriman.objects.get(pk=kid).status, StatusPengiriman.SELESAI)

    def test_tidak_bisa_berangkat_tanpa_perhentian(self):
        kirim = Pengiriman.objects.create(entitas=self.entitas, kurir=self.kurir, dibuat_oleh=self.petugas)
        r = self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kirim.id]))
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_distribusi_tidak_bisa_masuk_dua_pengiriman(self):
        self.rakit(ids=(101,))
        self.assertEqual(self.rakit(ids=(101, 102)).status_code, status.HTTP_400_BAD_REQUEST)

    def test_batalkan_hanya_saat_disiapkan(self):
        kid = self.rakit().data['id']
        self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kid]))
        self.assertEqual(self.client.post(reverse('logistik:pengiriman-batalkan', args=[kid]), {'alasan': 'Mogok'}, format='json').status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_patch_delete_405(self):
        url = reverse('logistik:pengiriman-detail', args=[self.rakit().data['id']])
        for metode in (self.client.put, self.client.patch, self.client.delete):
            self.assertEqual(metode(url, {'status': 'SELESAI'}, format='json').status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class TidakMenulisStokTest(BasisLogistik):
    def test_merakit_tidak_memicu_warehouse(self):
        self.rakit()
        self.mock_terkirim.assert_not_called()

    def test_berangkat_tidak_memicu_warehouse(self):
        self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[self.rakit().data['id']]))
        self.mock_terkirim.assert_not_called()

    def test_bukti_terima_memicu_tandai_terkirim_sekali(self):
        kid = self.rakit(ids=(101,)).data['id']
        self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kid]))
        hid = Perhentian.objects.get(pengiriman_id=kid).id
        self.client.post(f"/api/v1/logistik/pengiriman/{kid}/perhentian/{hid}/bukti/", {'foto': foto()}, format='multipart')
        self.client.post(f"/api/v1/logistik/pengiriman/{kid}/perhentian/{hid}/bukti/", {'foto': foto()}, format='multipart')
        self.assertEqual(self.mock_terkirim.call_count, 1)

    def test_batal_tidak_mengembalikan_stok(self):
        self.client.post(reverse('logistik:pengiriman-batalkan', args=[self.rakit().data['id']]), {'alasan': 'X'}, format='json')
        self.mock_kembalikan.assert_not_called()


class IdempotensiTest(BasisLogistik):
    def test_kunci_sama_tidak_membuat_dua_bukti(self):
        kid = self.rakit(ids=(101,)).data['id']
        self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kid]))
        hid = Perhentian.objects.get(pengiriman_id=kid).id
        url = f"/api/v1/logistik/pengiriman/{kid}/perhentian/{hid}/bukti/"
        kunci = 'a1b2c3d4-0000'
        self.client.post(url, {'foto': foto()}, format='multipart', HTTP_IDEMPOTENCY_KEY=kunci)
        self.client.post(url, {'foto': foto()}, format='multipart', HTTP_IDEMPOTENCY_KEY=kunci)
        self.assertEqual(Perhentian.objects.get(pk=hid).bukti.count(), 1)


class ReturTest(BasisLogistik):
    def _retur(self):
        kid = self.rakit(ids=(101,)).data['id']
        self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kid]))
        hid = Perhentian.objects.get(pengiriman_id=kid).id
        r = self.client.post(f"/api/v1/logistik/pengiriman/{kid}/perhentian/{hid}/retur/", {'alasan': 'Tolak'}, format='multipart')
        return kid, hid, r

    def test_retur_tidak_langsung_mengembalikan_stok(self):
        self.assertEqual(self._retur()[2].status_code, status.HTTP_200_OK)
        self.mock_kembalikan.assert_not_called()

    def test_hanya_supervisor_yang_menyetujui(self):
        _, hid, _ = self._retur()
        retur = Retur.objects.get(perhentian_id=hid)
        self.client.force_authenticate(self.bos)
        self.client.post(reverse('logistik:retur-setujui', args=[retur.id]))
        self.mock_kembalikan.assert_called_once()

    def test_alasan_wajib(self):
        kid = self.rakit(ids=(101,)).data['id']
        self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kid]))
        hid = Perhentian.objects.get(pengiriman_id=kid).id
        self.assertEqual(self.client.post(f"/api/v1/logistik/pengiriman/{kid}/perhentian/{hid}/retur/", {'alasan': ''}, format='multipart').status_code, status.HTTP_400_BAD_REQUEST)


class PelacakanTest(BasisLogistik):
    def test_posisi_ditolak_sebelum_berangkat(self):
        self.client.force_authenticate(self.kurir)
        self.assertEqual(self.client.post(reverse('logistik:pengiriman-posisi', args=[self.rakit().data['id']]), {'lat': '-6.2', 'lng': '106.8'}, format='json').status_code, status.HTTP_400_BAD_REQUEST)

    def test_posisi_diterima_saat_berangkat(self):
        kid = self.rakit().data['id']
        self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kid]))
        self.client.force_authenticate(self.kurir)
        self.assertEqual(self.client.post(reverse('logistik:pengiriman-posisi', args=[kid]), {'lat': '-6.2', 'lng': '106.8'}, format='json').status_code, status.HTTP_204_NO_CONTENT)

    def test_posisi_ditolak_setelah_selesai(self):
        kid = self.rakit(ids=(101,)).data['id']
        self.client.post(reverse('logistik:pengiriman-berangkatkan', args=[kid]))
        hid = Perhentian.objects.get(pengiriman_id=kid).id
        self.client.post(f"/api/v1/logistik/pengiriman/{kid}/perhentian/{hid}/bukti/", {'foto': foto()}, format='multipart')
        self.client.force_authenticate(self.kurir)
        self.assertEqual(self.client.post(reverse('logistik:pengiriman-posisi', args=[kid]), {'lat': '-6.2', 'lng': '106.8'}, format='json').status_code, status.HTTP_400_BAD_REQUEST)


class CakupanKurirTest(BasisLogistik):
    def test_kurir_tidak_melihat_pengiriman_kurir_lain(self):
        self.rakit(ids=(101,), kurir=self.kurir)
        self.rakit(ids=(102,), kurir=self.kurir_lain)
        self.client.force_authenticate(self.kurir)
        r = self.client.get(reverse('logistik:pengiriman-list'))
        self.assertEqual(len(r.data['results'] if isinstance(r.data, dict) else r.data), 1)

    def test_kurir_tidak_bisa_membuka_pengiriman_orang_lain(self):
        kid = self.rakit(ids=(102,), kurir=self.kurir_lain).data['id']
        self.client.force_authenticate(self.kurir)
        self.assertEqual(self.client.get(reverse('logistik:pengiriman-detail', args=[kid])).status_code, status.HTTP_404_NOT_FOUND)

    def test_kurir_tidak_bisa_merakit_pengiriman(self):
        self.client.force_authenticate(self.kurir)
        self.assertEqual(self.rakit().status_code, status.HTTP_403_FORBIDDEN)

    def test_petugas_gudang_melihat_semua(self):
        self.rakit(ids=(101,), kurir=self.kurir)
        self.rakit(ids=(102,), kurir=self.kurir_lain)
        self.assertEqual(len(self.client.get(reverse('logistik:pengiriman-list')).data.get('results', self.client.get(reverse('logistik:pengiriman-list')).data)), 2)


class RuteTest(BasisLogistik):
    def test_urutan_usulan_tersimpan_tanpa_menimpa(self):
        kid = self.rakit(ids=(103, 101, 102)).data['id']
        self.assertTrue(all(b.urutan_usulan is not None for b in Perhentian.objects.filter(pengiriman_id=kid)))

    def test_urutkan_manual_menimpa(self):
        kid = self.rakit(ids=(101, 102)).data['id']
        ids = list(Perhentian.objects.filter(pengiriman_id=kid).order_by('urutan').values_list('id', flat=True))
        self.client.post(reverse('logistik:pengiriman-urutkan', args=[kid]), {'urutan': list(reversed(ids))}, format='json')
        self.assertEqual(list(Perhentian.objects.filter(pengiriman_id=kid).order_by('urutan').values_list('id', flat=True)), list(reversed(ids)))

    def test_urutan_harus_lengkap(self):
        kid = self.rakit(ids=(101, 102)).data['id']
        self.assertEqual(self.client.post(reverse('logistik:pengiriman-urutkan', args=[kid]), {'urutan': [Perhentian.objects.filter(pengiriman_id=kid).first().id]}, format='json').status_code, status.HTTP_400_BAD_REQUEST)


class SambunganBelumSiapTest(APITestCase):
    def test_distribusi_tersedia_503(self):
        user = User.objects.create_superuser(username='bos2', password='rahasia123', email='b2@pracindo.test')
        self.client.force_authenticate(user)
        # 3. PASTIKAN SELALU PAKAI REVERSE AGAR DJANGO MEMBACA '/api/v1/logistik/...' SECARA OTOMATIS
        r = self.client.get(reverse('logistik:distribusi-tersedia'))
        self.assertEqual(r.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)