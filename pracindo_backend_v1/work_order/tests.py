"""
Tes Papan Tugas — work_order/tests.py

Enam pemblokir dari PRD §13 masing-masing punya tes yang gagal sebelum
diperbaiki. Ditulis begitu supaya kalau ada yang mengembalikan perilaku
lamanya, tesnya langsung merah.

DUA HAL YANG PALING DIJAGA

    approve harus BEKERJA. Versi lama memakai profil_staff_id yang tidak
    pernah ada, sehingga setiap orang dijawab 403 tanpa error di log.

    PRIVATE tidak boleh bocor di endpoint list. Izin objek DRF tidak berlaku
    untuk list, dan kebocoran ini tidak pernah ketahuan kecuali ada yang
    mencari.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.timezone import localdate
from rest_framework import status
from rest_framework.test import APITestCase

from staff_user.models import Role

from .models import AturanSelesai, Kategori, WorkOrder, WorkOrderPenugasan

User = get_user_model()


class BasisWO(APITestCase):

    @classmethod
    def setUpTestData(cls):
        def buat(nama, role):
            return User.objects.create_user(
                username=nama, password='rahasia123', role=role,
                first_name=nama.title())

        cls.andi = buat('andi', Role.PRODUKSI)
        cls.budi = buat('budi', Role.GUDANG)
        cls.citra = buat('citra', Role.SALES)
        cls.bos = User.objects.create_superuser(
            username='bos', password='rahasia123', email='bos@pracindo.test')
        cls.spv = buat('spv', Role.SUPERVISOR)

    def setUp(self):
        self.client.force_authenticate(self.andi)

    def buat_wo(self, **ubah):
        badan = {
            'judul': 'Siapkan berkas faktur Juli',
            'kategori': Kategori.UMUM,
            'aturan_penyelesaian': AturanSelesai.SALAH_SATU,
            'staff_ids': [self.budi.id],
        }
        badan.update(ubah)
        return self.client.post(reverse('work_order:workorder-list'),
                                badan, format='json')


class PenyelesaianTest(BasisWO):
    """Pemblokir 1 dan 2: approve harus benar-benar bisa menutup WO."""

    def test_salah_satu_ditutup_oleh_yang_ditandai(self):
        wid = self.buat_wo(staff_ids=[self.budi.id, self.citra.id]).data['id']

        self.client.force_authenticate(self.budi)
        r = self.client.post(reverse('work_order:workorder-approve', args=[wid]))
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.data)
        self.assertTrue(r.data['tuntas'])
        self.assertTrue(WorkOrder.objects.get(pk=wid).selesai)

    def test_yang_tidak_ditandai_ditolak(self):
        wid = self.buat_wo(staff_ids=[self.budi.id]).data['id']
        self.client.force_authenticate(self.citra)
        r = self.client.post(reverse('work_order:workorder-approve', args=[wid]))
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(WorkOrder.objects.get(pk=wid).selesai)

    def test_aturan_semua_menunggu_anggota_terakhir(self):
        wid = self.buat_wo(
            aturan_penyelesaian=AturanSelesai.SEMUA,
            staff_ids=[self.budi.id, self.citra.id]).data['id']

        self.client.force_authenticate(self.budi)
        r = self.client.post(reverse('work_order:workorder-approve', args=[wid]))
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.data)
        self.assertFalse(r.data['tuntas'])
        self.assertIn('1 dari 2', r.data['detail'])
        self.assertFalse(WorkOrder.objects.get(pk=wid).selesai)

        self.client.force_authenticate(self.citra)
        r = self.client.post(reverse('work_order:workorder-approve', args=[wid]))
        self.assertTrue(r.data['tuntas'])
        self.assertTrue(WorkOrder.objects.get(pk=wid).selesai)

    def test_aturan_pic_hanya_pic(self):
        wid = self.buat_wo(
            aturan_penyelesaian=AturanSelesai.PIC,
            staff_ids=[self.budi.id, self.citra.id],
            pic_id=self.citra.id).data['id']

        self.client.force_authenticate(self.budi)
        r = self.client.post(reverse('work_order:workorder-approve', args=[wid]))
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('PIC', r.data['detail'])

        self.client.force_authenticate(self.citra)
        r = self.client.post(reverse('work_order:workorder-approve', args=[wid]))
        self.assertTrue(r.data['tuntas'])

    def test_aturan_pic_tanpa_pic_ditolak_saat_dibuat(self):
        """Tanpa ini, WO-nya tidak bisa diselesaikan siapa pun -- dan itu baru
        ketahuan setelah orang mengerjakan tugasnya."""
        r = self.buat_wo(aturan_penyelesaian=AturanSelesai.PIC)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_supervisor_bisa_menutup_paksa(self):
        wid = self.buat_wo(staff_ids=[self.budi.id]).data['id']
        self.client.force_authenticate(self.spv)
        r = self.client.post(reverse('work_order:workorder-approve', args=[wid]))
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.data)
        self.assertTrue(WorkOrder.objects.get(pk=wid).selesai)

    def test_tidak_bisa_disetujui_dua_kali(self):
        wid = self.buat_wo().data['id']
        self.client.force_authenticate(self.budi)
        self.client.post(reverse('work_order:workorder-approve', args=[wid]))
        r = self.client.post(reverse('work_order:workorder-approve', args=[wid]))
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_aturan_tak_dikenal_tidak_menghasilkan_500(self):
        """Versi lama jatuh ke akhir fungsi tanpa return -- 500 dengan pesan
        'view didn't return an HttpResponse'."""
        wid = self.buat_wo().data['id']
        WorkOrder.objects.filter(pk=wid).update(aturan_penyelesaian='ENTAH')
        self.client.force_authenticate(self.budi)
        r = self.client.post(reverse('work_order:workorder-approve', args=[wid]))
        self.assertLess(r.status_code, 500)


class VisibilitasTest(BasisWO):
    """Pemblokir 3 dan 4: mading dan list."""

    def test_private_tidak_bocor_di_list(self):
        self.client.force_authenticate(self.budi)
        self.buat_wo(kategori=Kategori.PRIVATE, staff_ids=[self.citra.id])

        self.client.force_authenticate(self.andi)
        r = self.client.get(reverse('work_order:workorder-list'))
        hasil = r.data['results'] if isinstance(r.data, dict) else r.data
        self.assertEqual(len(hasil), 0)

    def test_private_terlihat_yang_ditandai(self):
        self.client.force_authenticate(self.budi)
        self.buat_wo(kategori=Kategori.PRIVATE, staff_ids=[self.citra.id])

        self.client.force_authenticate(self.citra)
        r = self.client.get(reverse('work_order:workorder-list'))
        hasil = r.data['results'] if isinstance(r.data, dict) else r.data
        self.assertEqual(len(hasil), 1)

    def test_produksi_terlihat_semua_orang(self):
        self.buat_wo(
            kategori=Kategori.PRODUKSI, staff_ids=[self.budi.id],
            detail_produksi={'nama_item': 'Super White SC',
                             'unit': 'PAIL_25', 'stiker': 'PT'})
        self.client.force_authenticate(self.citra)
        r = self.client.get(reverse('work_order:workorder-list'))
        hasil = r.data['results'] if isinstance(r.data, dict) else r.data
        self.assertEqual(len(hasil), 1)

    def test_mading_memuat_umum_yang_menandai_saya(self):
        """Versi lama hanya memunculkan PRODUKSI untuk semua orang."""
        self.buat_wo(kategori=Kategori.UMUM, staff_ids=[self.budi.id])

        self.client.force_authenticate(self.budi)
        r = self.client.get(reverse('work_order:workorder-mading'))
        self.assertEqual(len(r.data), 1)
        self.assertEqual(r.data[0]['kategori'], 'UMUM')

    def test_mading_tidak_memuat_yang_selesai(self):
        wid = self.buat_wo().data['id']
        self.client.force_authenticate(self.budi)
        self.client.post(reverse('work_order:workorder-approve', args=[wid]))
        r = self.client.get(reverse('work_order:workorder-mading'))
        self.assertEqual(len(r.data), 0)

    def test_mading_terlambat_di_atas(self):
        self.buat_wo(judul='Tanpa tenggat', staff_ids=[self.budi.id])
        self.buat_wo(judul='Besok', staff_ids=[self.budi.id],
                     deadline=str(localdate() + timedelta(days=1)))
        self.buat_wo(judul='Kemarin', staff_ids=[self.budi.id],
                     deadline=str(localdate() - timedelta(days=1)))

        self.client.force_authenticate(self.budi)
        r = self.client.get(reverse('work_order:workorder-mading'))
        self.assertEqual([w['judul'] for w in r.data],
                         ['Kemarin', 'Besok', 'Tanpa tenggat'])
        self.assertTrue(r.data[0]['terlambat'])


class PenyuntinganTest(BasisWO):
    """Pemblokir 5: PATCH tidak boleh 500, penugasan harus bisa diubah."""

    def test_patch_dengan_detail_produksi_tidak_500(self):
        wid = self.buat_wo(
            kategori=Kategori.PRODUKSI, staff_ids=[self.budi.id],
            detail_produksi={'nama_item': 'Super White SC',
                             'unit': 'PAIL_25', 'stiker': 'PT'}).data['id']

        r = self.client.patch(
            reverse('work_order:workorder-detail', args=[wid]),
            {'detail_produksi': {'nama_item': 'Blue 102',
                                 'unit': 'GALON_5', 'stiker': 'CV'}},
            format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.data)
        self.assertEqual(r.data['detail_produksi']['nama_item'], 'Blue 102')

    def test_penugasan_bisa_diubah(self):
        wid = self.buat_wo(staff_ids=[self.budi.id]).data['id']
        r = self.client.patch(
            reverse('work_order:workorder-detail', args=[wid]),
            {'staff_ids': [self.citra.id], 'pic_id': self.citra.id},
            format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.data)
        staf = {p['staff'] for p in r.data['penugasan']}
        self.assertEqual(staf, {self.citra.id})

    def test_mengganti_staf_tidak_menghanguskan_konfirmasi_yang_tinggal(self):
        wid = self.buat_wo(
            aturan_penyelesaian=AturanSelesai.SEMUA,
            staff_ids=[self.budi.id, self.citra.id]).data['id']

        self.client.force_authenticate(self.budi)
        self.client.post(reverse('work_order:workorder-approve', args=[wid]))

        self.client.force_authenticate(self.andi)
        self.client.patch(
            reverse('work_order:workorder-detail', args=[wid]),
            {'staff_ids': [self.budi.id, self.bos.id]}, format='json')

        budi = WorkOrderPenugasan.objects.get(work_order_id=wid, staff=self.budi)
        self.assertTrue(budi.is_selesai_personal)

    def test_bukan_pembuat_tidak_bisa_mengubah(self):
        wid = self.buat_wo(staff_ids=[self.budi.id]).data['id']
        self.client.force_authenticate(self.budi)
        r = self.client.patch(
            reverse('work_order:workorder-detail', args=[wid]),
            {'judul': 'Diubah orang lain'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_ditolak(self):
        wid = self.buat_wo().data['id']
        r = self.client.delete(reverse('work_order:workorder-detail', args=[wid]))
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(WorkOrder.objects.filter(pk=wid).exists())

    def test_pic_harus_termasuk_yang_ditandai(self):
        r = self.buat_wo(staff_ids=[self.budi.id], pic_id=self.citra.id)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class PenomoranTest(BasisWO):
    """Pemblokir 6."""

    def test_nomor_berurut_dan_unik(self):
        nomor = [self.buat_wo().data['nomor'] for _ in range(5)]
        self.assertEqual(len(set(nomor)), 5)
        self.assertTrue(all(n.startswith('WO/') for n in nomor))
        self.assertEqual(nomor[-1].split('/')[-1], '005')

    def test_penghitung_tidak_bergantung_urutan_string(self):
        """Versi lama membaca nomor terakhir dengan order_by('nomor'),
        yang salah begitu melewati 999 dalam satu bulan."""
        from .models import CounterWorkOrder
        periode = localdate().strftime('%Y/%m')
        CounterWorkOrder.objects.update_or_create(
            periode=periode, defaults={'urutan': 999})
        self.assertEqual(self.buat_wo().data['nomor'].split('/')[-1], '1000')


class DiskusiTest(BasisWO):

    def test_kirim_dan_baca_pesan(self):
        wid = self.buat_wo().data['id']
        r = self.client.post(
            reverse('work_order:workorder-kirim-pesan', args=[wid]),
            {'teks': 'Berkasnya ada di lemari kedua.'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.data)
        self.assertEqual(r.data['pengirim_nama'], 'Andi')

        r = self.client.get(reverse('work_order:workorder-pesan', args=[wid]))
        self.assertEqual(len(r.data), 1)

    def test_pesan_kosong_ditolak(self):
        wid = self.buat_wo().data['id']
        r = self.client.post(
            reverse('work_order:workorder-kirim-pesan', args=[wid]),
            {'teks': '   '}, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_daftar_tidak_membawa_seluruh_pesan(self):
        """Payload daftar harus ringan: jumlahnya saja, bukan isinya."""
        wid = self.buat_wo().data['id']
        for i in range(3):
            self.client.post(
                reverse('work_order:workorder-kirim-pesan', args=[wid]),
                {'teks': f'pesan {i}'}, format='json')

        r = self.client.get(reverse('work_order:workorder-list'))
        item = (r.data['results'] if isinstance(r.data, dict) else r.data)[0]
        self.assertNotIn('pesan_chat', item)
        self.assertEqual(item['jumlah_pesan'], 3)

        r = self.client.get(reverse('work_order:workorder-detail', args=[wid]))
        self.assertEqual(len(r.data['pesan_chat']), 3)


class BukaKembaliTest(BasisWO):

    def test_hanya_supervisor(self):
        wid = self.buat_wo().data['id']
        self.client.force_authenticate(self.budi)
        self.client.post(reverse('work_order:workorder-approve', args=[wid]))

        r = self.client.post(
            reverse('work_order:workorder-buka-kembali', args=[wid]),
            {'alasan': 'Berkasnya kurang satu.'}, format='json')
        self.assertIn(r.status_code,
                      (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED))

        self.client.force_authenticate(self.spv)
        r = self.client.post(
            reverse('work_order:workorder-buka-kembali', args=[wid]),
            {'alasan': 'Berkasnya kurang satu.'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.data)
        self.assertFalse(WorkOrder.objects.get(pk=wid).selesai)
