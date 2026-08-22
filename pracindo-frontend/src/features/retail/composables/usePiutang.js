import { ref } from 'vue'
import { http } from '@/utils/http'

export function usePiutang() {
    const piutangList = ref([])
    const isLoading = ref(false)

    const fetchPiutang = async () => {
        isLoading.value = true
        try {
            const response = await http.get('v1/retail/piutang/')
            piutangList.value = response.data.results || response.data || []
        } catch (error) {
            console.error("Gagal mengambil data piutang:", error)
            piutangList.value = []
        } finally {
            isLoading.value = false
        }
    }

    const prosesBayar = async (id, payload) => {
        isLoading.value = true
        try {
            const response = await http.post(`v1/retail/piutang/${id}/bayar/`, payload)
            return response.data
        } catch (error) {
            console.error("Gagal memproses pembayaran piutang:", error)
            return {
                status: 'gagal',
                pesan: error.response?.data?.pesan || 'Terjadi kesalahan sistem.'
            }
        } finally {
            isLoading.value = false
        }
    }

    return {
        piutangList,
        isLoading,
        fetchPiutang,
        prosesBayar
    }
}
