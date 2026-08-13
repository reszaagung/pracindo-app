import { ref, computed } from 'vue'
import api from '@/utils/api'

export function useSalesOrder() {
    const listEntitas = ref([])
    const listPelanggan = ref([])
    const listProduk = ref([])

    const daftarSO = ref([])
    const isLoading = ref(false)

    const sedangProses = ref(false)
    const pesanError = ref('')
    const periodeDitutup = ref(false)

    const muatDataMaster = async () => {
        try {
            const [resEntitas, resPelanggan, resProduk] = await Promise.all([
                api.get('master/entitas/'),
                api.get('master/pelanggan/'),
                api.get('master/produk/')
            ])

            listEntitas.value = resEntitas.data.results || resEntitas.data
            listPelanggan.value = resPelanggan.data.results || resPelanggan.data
            listProduk.value = resProduk.data.results || resProduk.data
        } catch (error) {
            console.error("Gagal memuat master data SO:", error)
            pesanError.value = "Gagal memuat data master dari server."
        }
    }

    const fetchSO = async () => {
        isLoading.value = true
        pesanError.value = ''
        try {
            const response = await api.get('sales-order/')

            let rawData = Array.isArray(response.data) ? response.data
                : (response.data?.results || response.data?.data || [response.data])

            daftarSO.value = rawData.map(so => ({
                id: so.id,
                nomor_so: so.no_so,
                tanggal: so.tanggal,
                entitas: so.entitas ? { kode: so.entitas.kode } : { kode: 'UMUM' },
                pelanggan: so.pelanggan ? { nama: so.pelanggan.nama, kota: so.pelanggan.kota || '-' } : { nama: '-', kota: '-' },
                grand_total: parseFloat(so.subtotal) + parseFloat(so.ppn_nominal || 0),
                status: so.status
            }))
        } catch (error) {
            console.error("Gagal mengambil data Sales Order:", error)
            pesanError.value = "Gagal memuat daftar Sales Order."
        } finally {
            isLoading.value = false
        }
    }

    const simpanSO = async (payload) => {
        sedangProses.value = true
        pesanError.value = ''
        try {
            const res = await api.post('akunting/sales-order/', payload)
            await fetchSO()
            return { success: true, data: res.data }
        } catch (error) {
            pesanError.value = error.response?.data?.detail || "Gagal menyimpan Sales Order."
            return { success: false }
        } finally {
            sedangProses.value = false
        }
    }

    return {
        listEntitas, listPelanggan, listProduk, daftarSO,
        isLoading, sedangProses, pesanError, periodeDitutup,
        muatDataMaster, fetchSO, simpanSO
    }
}