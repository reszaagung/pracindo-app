import { ref } from 'vue'
import { warehouseApi } from '../api' 

export function usePacking() {
  const packings = ref([])
  const isLoading = ref(false)
  const error = ref(null)

  const fetchPackings = async (params = {}) => {
    isLoading.value = true
    error.value = null
    try {
      const { data } = await warehouseApi.getRiwayatPacking(params)
      packings.value = data.results || data
    } catch (err) {
      error.value = err.response?.data?.pesan || err.message
    } finally {
      isLoading.value = false
    }
  }

  const createPacking = async (payload) => {
    isLoading.value = true
    error.value = null
    try {
      const { data } = await warehouseApi.simpanPacking(payload)
      return data
    } catch (err) {
      error.value = err.response?.data?.pesan || err.response?.data?.detail || err.message
      throw error.value
    } finally {
      isLoading.value = false
    }
  }

  const voidPacking = async (id, alasan) => {
    try {
      const { data } = await warehouseApi.voidPacking(id, { alasan })
      return data
    } catch (err) {
      throw err.response?.data?.pesan || err.message
    }
  }

  return {
    packings,
    isLoading,
    error,
    fetchPackings,
    createPacking,
    voidPacking
  }
}