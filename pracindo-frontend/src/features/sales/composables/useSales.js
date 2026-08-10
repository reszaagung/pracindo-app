// src/features/sales/composables/useSales.js
import { ref } from 'vue'
import api from '@/utils/api'

export function useSales() {
    const isLoading = ref(false)
    const isCreating = ref(false)
    const salesOrders = ref([])
    const statistik = ref({
        total_omset: 0,
        pesanan_aktif: 0,
        pesanan_selesai: 0
    })

    const fetchSalesOrders = async () => {
        isLoading.value = true
        try {
            // Memanggil API backend FastAPI
            const response = await api.get('sales-order/')
            salesOrders.value = response.data.results || response.data

            // Kalkulasi statistik sederhana dari data yang ditarik
            let omset = 0
            let aktif = 0
            let selesai = 0

            salesOrders.value.forEach(so => {
                if (so.status === 'SELESAI') {
                    selesai++
                } else {
                    aktif++
                    omset += Number(so.nilai || 0)
                }
            })

            statistik.value = { total_omset: omset, pesanan_aktif: aktif, pesanan_selesai: selesai }
        } catch (error) {
            console.error("Gagal memuat data Sales Order:", error)
        } finally {
            isLoading.value = false
        }
    }

    const createSalesOrder = async (payload) => {
        isCreating.value = true
        try {
            // Mengirim data SO baru ke backend
            await api.post('sales-order/', payload)
            await fetchSalesOrders() // Refresh data setelah berhasil
            return { success: true }
        } catch (error) {
            console.error("Gagal membuat SO:", error)
            const detailError = error.response?.data?.detail || JSON.stringify(error.response?.data) || "Gagal menyimpan pesanan baru."
            return { success: false, message: detailError }
        } finally {
            isCreating.value = false
        }
    }

    return {
        isLoading,
        isCreating,
        salesOrders,
        statistik,
        fetchSalesOrders,
        createSalesOrder
    }
}