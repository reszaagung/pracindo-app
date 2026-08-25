import { ref } from 'vue'
import { apiProduksi } from '../api'

export function usePratinjau() {
  const hasilPratinjau = ref(null)
  const validationErrors = ref([])
  const loading = ref(false)
  const error = ref(null)

  const hitungPratinjau = async (data) => {
    loading.value = true
    error.value = null
    validationErrors.value = []
    hasilPratinjau.value = null

    try {
      const response = await apiProduksi.pratinjauBatch(data)

      if (response.data.valid) {
        hasilPratinjau.value = response.data
        return true
      } else {
        validationErrors.value = response.data.galat || []
        return false
      }
    } catch (err) {
      error.value = err.response?.data?.pesan || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const resetPratinjau = () => {
    hasilPratinjau.value = null
    validationErrors.value = []
    error.value = null
  }

  return {
    hasilPratinjau,
    validationErrors,
    loading,
    error,
    hitungPratinjau,
    resetPratinjau
  }
}
