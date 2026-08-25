import { ref } from 'vue'
import { apiProduksi } from '../api'

export function useBatch() {
  const batches = ref([])
  const currentBatch = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const batchSaldo = ref(null)
  const batchKomposisi = ref(null)

  const fetchBatches = async (params = {}) => {
    loading.value = true
    error.value = null
    try {
      const response = await apiProduksi.getBatches(params)
      batches.value = response.data.results || response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.pesan || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchBatch = async (id) => {
    loading.value = true
    error.value = null
    try {
      const response = await apiProduksi.getBatch(id)
      currentBatch.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.pesan || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const createBatch = async (data) => {
    loading.value = true
    error.value = null
    try {
      const response = await apiProduksi.createBatch(data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.pesan || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const postingBatch = async (id) => {
    loading.value = true
    error.value = null
    try {
      const response = await apiProduksi.postingBatch(id)
      currentBatch.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.pesan || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const voidBatch = async (id, alasan) => {
    loading.value = true
    error.value = null
    try {
      const response = await apiProduksi.voidBatch(id, { alasan })
      currentBatch.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.pesan || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchBatchSaldo = async (id) => {
    try {
      const response = await apiProduksi.getBatchSaldo(id)
      batchSaldo.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.pesan || err.message
      throw err
    }
  }

  const fetchBatchKomposisi = async (id) => {
    try {
      const response = await apiProduksi.getBatchKomposisi(id)
      batchKomposisi.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.pesan || err.message
      throw err
    }
  }

  return {
    batches,
    currentBatch,
    loading,
    error,
    batchSaldo,
    batchKomposisi,
    fetchBatches,
    fetchBatch,
    createBatch,
    postingBatch,
    voidBatch,
    fetchBatchSaldo,
    fetchBatchKomposisi
  }
}
