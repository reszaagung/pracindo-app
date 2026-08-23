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
            const response = await http.get('v1/retail/pelanggan/')
            pelangganList.value = response.data.results || response.data || []
        } catch (error) {
            console.error("Gagal mengambil pelanggan:", error)
        }
    }

    const fetchSales = async () => {
        try {
            const response = await http.get('v1/retail/sales/')
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

    // PERBAIKAN: Namanya disamakan jadi fetchSesi agar cocok dengan KeuanganView.vue
    const fetchSesi = async () => {
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

    const tutupShift = async () => {
        isLoading.value = true
        try {
            const response = await http.post('v1/retail/sesi/')
            sesiAktif.value = null // Reset state setelah tutup shift
            return response.data
        } catch (error) {
            console.error("Gagal menutup shift:", error)
            throw error
        } finally {
            isLoading.value = false
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
        fetchSesi,
        fetchRiwayat,
        tutupShift
    }
}
