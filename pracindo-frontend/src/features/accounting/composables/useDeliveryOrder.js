import { ref } from 'vue'
import api from '@/utils/api'

export function useDeliveryOrder() {
    const isLoading = ref(false)
    const sedangProses = ref(false)
    const daftarLog = ref([])
    const pesanError = ref('')

    const muatLogPacking = async (params = {}) => {
        isLoading.value = true
        try {

            await new Promise(resolve => setTimeout(resolve, 600))
            daftarLog.value = []

        } catch (error) {
            console.error("Gagal memuat log packing:", error)
            pesanError.value = "Gagal menarik data dari server."
        } finally {
            isLoading.value = false
        }
    }


    const simpanDO = async (payload) => {
        sedangProses.value = true
        pesanError.value = ''
        try {
            await new Promise(resolve => setTimeout(resolve, 1000))

            return { success: true }
        } catch (error) {
            pesanError.value = error.response?.data?.detail || "Gagal menerbitkan Surat Jalan."
            return { success: false, message: pesanError.value }
        } finally {
            sedangProses.value = false
        }
    }

    return {
        isLoading,
        sedangProses,
        daftarLog,
        pesanError,
        muatLogPacking,
        simpanDO
    }
}