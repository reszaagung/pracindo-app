import { ref } from 'vue'
import { http } from '@/utils/http'

export function useAkuntansi() {
    const akunList = ref([])
    const riwayatJurnal = ref([])
    const isLoading = ref(false)

    const fetchAkun = async () => {
        isLoading.value = true
        try {
            const response = await http.get('v1/retail/akuntansi/akun/')
            akunList.value = response.data.results || response.data || []
        } catch (error) {
            console.error("Gagal mengambil data akun:", error)
            akunList.value = []
        } finally {
            isLoading.value = false
        }
    }

    // FUNGSI BARU: Mengambil riwayat jurnal
    const fetchRiwayatJurnal = async () => {
        isLoading.value = true
        try {
            const response = await http.get('v1/retail/akuntansi/jurnal/')
            riwayatJurnal.value = response.data.results || response.data || []
        } catch (error) {
            console.error("Gagal mengambil riwayat jurnal:", error)
            riwayatJurnal.value = []
        } finally {
            isLoading.value = false
        }
    }

    const buatJurnal = async (payload) => {
        isLoading.value = true
        try {
            const response = await http.post('v1/retail/akuntansi/jurnal/', payload)
            return response.data
        } catch (error) {
            console.error("Gagal membuat jurnal:", error)
            return {
                status: 'gagal',
                pesan: error.response?.data?.pesan || 'Terjadi kesalahan sistem.'
            }
        } finally {
            isLoading.value = false
        }
    }

    return {
        akunList,
        riwayatJurnal,
        isLoading,
        fetchAkun,
        fetchRiwayatJurnal,
        buatJurnal
    }
}
