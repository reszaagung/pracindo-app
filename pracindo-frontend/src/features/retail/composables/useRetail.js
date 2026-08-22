import { ref } from 'vue'
import { http } from '@/utils/http'

export function useRetail() {
    const posProducts = ref([])
    const pelangganList = ref([])
    const salesList = ref([])
    const riwayat = ref([])
    const isLoading = ref(false)
    const sesiAktif = ref(null)

    const fetchPosProducts = async () => {
        isLoading.value = true
        try {
            const response = await http.get('v1/retail/pos/katalog/')
            posProducts.value = response.data.results || response.data || []
        } catch (error) {
            console.error("Gagal mengambil data produk:", error)
            posProducts.value = []
        } finally {
            isLoading.value = false
        }
    }

    const fetchPelanggan = async () => {
        try {
            const response = await http.get('v1/retail/pelanggan/') // Pastikan endpoint ini ada di backend
            pelangganList.value = response.data.results || response.data || []
        } catch (error) {
            console.error("Gagal mengambil pelanggan:", error)
        }
    }

    const fetchSales = async () => {
        try {
            const response = await http.get('v1/retail/sales/') // Pastikan endpoint ini ada di backend
            salesList.value = response.data.results || response.data || []
        } catch (error) {
            console.error("Gagal mengambil sales:", error)
        }
    }

    const checkoutCart = async (payload) => {
        isLoading.value = true
        try {
            const response = await http.post('v1/retail/pos/checkout/', payload)
            return response.data
        } catch (error) {
            console.error("Gagal memproses pembayaran:", error)
            return {
                status: 'gagal',
                pesan: error.response?.data?.pesan || 'Terjadi kesalahan sistem.'
            }
        } finally {
            isLoading.value = false
        }
    }

    const fetchSesiKasir = async () => {
        try {
            const response = await http.get('v1/retail/sesi/')
            if (response.data.status !== 'TIDAK_ADA_SHIFT') {
                sesiAktif.value = response.data
            } else {
                sesiAktif.value = null
            }
        } catch (error) {
            console.error("Gagal memuat sesi:", error)
        }
    }

    const fetchRiwayat = async () => {
        try {
            const response = await http.get('v1/retail/riwayat/')
            riwayat.value = response.data.results || response.data || []
        } catch (error) {
            console.error("Gagal memuat riwayat:", error)
        }
    }

    return {
        posProducts,
        pelangganList,
        salesList,
        riwayat,
        isLoading,
        sesiAktif,
        fetchPosProducts,
        fetchPelanggan,
        fetchSales,
        checkoutCart,
        fetchSesiKasir,
        fetchRiwayat
    }
}
