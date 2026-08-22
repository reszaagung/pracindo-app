import { ref } from 'vue'
import { http } from '@/utils/http'

export function usePenerimaan() {
    const doList = ref([])
    const isLoading = ref(false)

    const fetchDO = async () => {
        isLoading.value = true
        try {
            const response = await http.get('v1/retail/penerimaan/')
            doList.value = response.data.results || response.data || []
        } catch (error) {
            console.error("Gagal mengambil data DO:", error)
        } finally {
            isLoading.value = false
        }
    }

    const prosesPenerimaan = async (id, items) => {
        isLoading.value = true
        try {
            const response = await http.post(`v1/retail/penerimaan/${id}/proses/`, { items })
            return response.data
        } catch (error) {
            console.error("Gagal proses DO:", error)
            return { status: 'gagal', pesan: error.response?.data?.pesan || 'Terjadi kesalahan sistem.' }
        } finally {
            isLoading.value = false
        }
    }

    return {
        doList,
        isLoading,
        fetchDO,
        prosesPenerimaan
    }
}
