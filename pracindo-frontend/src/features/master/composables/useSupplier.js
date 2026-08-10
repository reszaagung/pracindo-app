// src/features/master/composables/useSupplier.js
// master/suplier/ sudah hidup di backend (diverifikasi manual oleh pengguna
// terhadap server yang jalan — lihat SPEK-BACKEND.md §3.4). Tidak ada mock.

import { ref } from 'vue'
import api from '@/utils/api'
import { bacaError as bacaPesan, errorPerField } from '@/utils/error'

// Backend pakai PageNumberPagination dengan PAGE_SIZE=25. Ukuran halaman
// ditentukan server — angka ini cuma untuk menghitung offset Paginator di UI.
const PER_HALAMAN = 25

// django-filter menolak `aktif=` kosong, dan `search=` kosong bikin backend
// jalan lewat SearchFilter tanpa perlu. Buang param yang tidak diisi.
const bersih = (params) =>
    Object.fromEntries(
        Object.entries(params).filter(([, nilai]) => nilai !== undefined && nilai !== null && nilai !== '')
    )

/**
 * Pecah error DRF jadi dua bagian: pesan untuk banner + peta error per field,
 * supaya "kode sudah dipakai" nempel di input kode, bukan numpuk di atas form.
 *
 * Bukan implementasi baru — bacaError/errorPerField di @/utils/error sudah
 * hafal bentuk error backend (detail / per-field / non_field_errors / network);
 * di sini cuma dibungkus jadi satu bentuk yang enak dipakai form.
 */
const bacaError = (err, fallback = 'Terjadi kesalahan.') => {
    const data = err?.response?.data

    // DRF bisa membalas array telanjang atau { detail: [...] } — tidak terikat field.
    if (Array.isArray(data)) return { pesanUmum: data.join(' '), errorField: {} }
    if (Array.isArray(data?.detail)) return { pesanUmum: data.detail.join(' '), errorField: {} }

    const errorField = errorPerField(err) // {} kalau errornya bukan per field
    if (!Object.keys(errorField).length) return { pesanUmum: bacaPesan(err, fallback), errorField: {} }

    // non_field_errors sengaja dilewati errorPerField — angkat ke banner.
    const umum = data.non_field_errors
    return {
        pesanUmum: Array.isArray(umum) ? umum.join(' ') : 'Periksa kembali isian yang ditandai merah.',
        errorField
    }
}

export function useSupplier() {
    const daftarSuplier = ref([])
    const sedangProses = ref(false)
    const pesanError = ref('')
    // Dipakai form untuk menandai input yang ditolak backend.
    const errorField = ref({})

    // Paginasi mengikuti respons { count, next, previous, results }.
    const totalData = ref(0)
    const halaman = ref(1)
    const perHalaman = PER_HALAMAN

    /**
     * Mengambil data lengkap untuk tabel Master Suplier
     * Menerima params seperti { search: 'kata kunci', aktif: true, halaman: 2 }
     */
    const ambilSuplier = async (params = {}) => {
        const ke = params.halaman || 1
        sedangProses.value = true
        pesanError.value = ''
        try {
            const { data } = await api.get('master/suplier/', {
                params: bersih({ search: params.search, aktif: params.aktif, page: ke })
            })
            daftarSuplier.value = data.results || data
            totalData.value = data.count ?? daftarSuplier.value.length
            // Baru digeser setelah data benar-benar datang, biar Paginator
            // tidak menunjuk halaman yang gagal dimuat.
            halaman.value = ke
        } catch (err) {
            pesanError.value = bacaPesan(err, 'Gagal memuat data suplier.')
        } finally {
            sedangProses.value = false
        }
    }

    /**
     * Mengambil data ringkas khusus untuk Dropdown (digunakan di modul Accounting dll)
     * GET master/suplier/?ringkas=1&aktif=true
     *
     * `aktif` sengaja dikirim sebagai string 'true' — django-filter membaca
     * query string, jadi lebih eksplisit daripada mengandalkan serialisasi
     * boolean axios. Serializer ringkas membawa `termin_hari_default`, yang
     * dipakai form PO untuk menghitung jatuh tempo faktur — jangan dibuang
     * dari hasil di sisi pemanggil.
     */
    const ambilSuplierRingkas = async () => {
        try {
            const { data } = await api.get('master/suplier/', {
                params: { ringkas: 1, aktif: 'true' }
            })
            return data.results || data
        } catch (err) {
            console.error('Gagal memuat dropdown suplier:', err)
            return []
        }
    }

    /**
     * Menyimpan suplier (Tambah baru jika id kosong, atau Update jika id ada)
     * Hanya berhasil untuk role ADMIN atau SUPERVISOR — role lain dapat 403.
     * Sembunyikan tombol tambah/ubah di komponen untuk role tanpa izin,
     * jangan andalkan 403 sebagai satu-satunya penjaga.
     *
     * `pkp` tidak pernah ikut di payload — properti turunan npwp, read-only.
     */
    const simpanSuplier = async (payload, id = null) => {
        sedangProses.value = true
        pesanError.value = ''
        errorField.value = {}
        try {
            if (id) {
                await api.patch(`master/suplier/${id}/`, payload)
            } else {
                await api.post('master/suplier/', payload)
            }
            return { success: true }
        } catch (err) {
            const hasil = bacaError(err, 'Gagal menyimpan data suplier.')
            pesanError.value = hasil.pesanUmum
            errorField.value = hasil.errorField
            return { success: false }
        } finally {
            sedangProses.value = false
        }
    }

    /**
     * Pengganti DELETE. Endpoint DELETE suplier membalas 500 (backend melempar
     * ValidationError Django, bukan DRF) — JANGAN PERNAH dipanggil. Menonaktifkan
     * suplier cukup lewat PATCH { aktif: false }: backend buat_po() menolak
     * suplier nonaktif, sementara PO lama tetap jalan.
     */
    const ubahStatusAktif = async (id, aktif) => {
        sedangProses.value = true
        pesanError.value = ''
        try {
            await api.patch(`master/suplier/${id}/`, { aktif })
            return { success: true }
        } catch (err) {
            pesanError.value = bacaPesan(err, 'Gagal mengubah status suplier.')
            return { success: false }
        } finally {
            sedangProses.value = false
        }
    }

    return {
        // State
        daftarSuplier,
        sedangProses,
        pesanError,
        errorField,
        totalData,
        halaman,
        perHalaman,

        // Actions
        ambilSuplier,
        ambilSuplierRingkas,
        simpanSuplier,
        ubahStatusAktif
    }
}
