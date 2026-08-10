import { ref, computed } from 'vue'
import api from '@/utils/api'

export function useSupplier() {
    const dataSuplier = ref([])
    const isLoading = ref(false)
    const error = ref(null)
    const searchQuery = ref('')

    const fetchSupplier = async () => {
        isLoading.value = true
        error.value = null
        try {
            const response = await api.get('suplier/')
            dataSuplier.value = response.data.results || response.data || []
        } catch (err) {
            console.error("Gagal memuat data master suplier:", err)
            error.value = "Gagal memuat data dari database."
        } finally {
            isLoading.value = false
        }
    }

    const addSuplier = async (payload) => {
        isLoading.value = true
        try {
            const response = await api.post('supplier/', payload)
            await fetchSupplier()
            return { success: true, data: response.data }
        } catch (err) {
            console.error("Gagal menambah supplier:", err)
            return {
                success: false,
                message: err.response?.data?.message || err.response?.data?.detail || "Gagal menyimpan data ke server."
            }
        } finally {
            isLoading.value = false
        }
    }

    const deleteSuplier = async (id_supplier) => {
        isLoading.value = true
        try {
            await api.delete(`supplier/${id_supplier}/`)
            await fetchSupplier()
            return { success: true }
        } catch (err) {
            console.error("Gagal menghapus suplier:", err)
            return {
                success: false,
                message: err.response?.data?.message || err.response?.data?.detail || "Gagal menghapus data dari server."
            }
        } finally {
            isLoading.value = false
        }
    }

    const filteredSuplier = computed(() => {
        if (!searchQuery.value) return dataSuplier.value

        const lowerCaseQuery = searchQuery.value.toLowerCase()
        return dataSuplier.value.filter(sup => {
            const nama = (sup.nama_perusahaan || sup.nama_suplier || '').toLowerCase()
            const pic = (sup.pic_name || sup.pic || '').toLowerCase()
            return nama.includes(lowerCaseQuery) || pic.includes(lowerCaseQuery)
        })
    })

    return {
        dataSuplier,
        filteredSuplier,
        searchQuery,
        isLoading,
        error,
        fetchSupplier,
        addSuplier,
        deleteSuplier
    }
}