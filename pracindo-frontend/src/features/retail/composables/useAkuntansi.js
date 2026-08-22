import { ref } from 'vue'
import { http } from '@/utils/http'

export function useAkuntansi() {
    const akunList = ref([])
    const isLoading = ref(false)

    // Ambil daftar Akun Buku Besar
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
        isLoading,
        fetchAkun,
        buatJurnal
    }
}
