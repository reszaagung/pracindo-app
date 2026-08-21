import { ref } from 'vue'
import { http } from '@/utils/http' // <-- Menggunakan http bawaan sistem Anda

export function useRetail() {
    const posProducts = ref([])
    const isLoading = ref(false)
    const sesiAktif = ref(null)

    // 1. Mengambil Katalog Produk
    const fetchPosProducts = async () => {
        isLoading.value = true
        try {
            const response = await http.get('v1/retail/pos/katalog/')

            if (response.data && response.data.results) {
                posProducts.value = response.data.results
            } else if (response.data) {
                posProducts.value = response.data
            } else {
                posProducts.value = []
            }
        } catch (error) {
            console.error("Gagal mengambil data produk:", error)
            posProducts.value = []
        } finally {
            isLoading.value = false
        }
    }

    // 2. Checkout
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

    // 3. Status Shift Kasir
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

    return {
        posProducts,
        isLoading,
        sesiAktif,
        fetchPosProducts,
        checkoutCart,
        fetchSesiKasir
    }
}
