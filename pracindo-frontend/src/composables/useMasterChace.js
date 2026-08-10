import { ref } from 'vue'
import api from '@/utils/api'


const cachedSuppliers = ref([])
const isSuppliersLoaded = ref(false)

export function useMasterCache() {
    const muatSuppliers = async () => {
        if (isSuppliersLoaded.value) {
            return cachedSuppliers.value
        }

        try {
            const { data } = await api.get('master/suplier/', { params: { ringkas: 1, aktif: true } })
            cachedSuppliers.value = data.results || data || []
            isSuppliersLoaded.value = true
            return cachedSuppliers.value
        } catch (error) {
            console.error("Gagal memuat suplier:", error)
            return []
        }
    }

    const forceRefreshSuppliers = async () => {
        isSuppliersLoaded.value = false
        return await muatSuppliers()
    }

    return {
        cachedSuppliers,
        isSuppliersLoaded,
        muatSuppliers,
        forceRefreshSuppliers
    }
}