// src/features/kurir/composables/useCourier.js
import { ref } from 'vue'
import api from '@/utils/api'

export function useCourier() {
    const isLoading = ref(false)
    const isUploading = ref(false)

    // State Data
    const daftarTugas = ref([])
    const detailPengiriman = ref(null)

    // 1. Memuat daftar tugas kurir yang sedang login
    const fetchTugasSaya = async () => {
        isLoading.value = true
        try {
            const response = await api.get('logistik/pengiriman/tugas-saya/')
            daftarTugas.value = response.data.results || response.data
        } catch (error) {
            console.error("Gagal memuat daftar tugas:", error)
            throw error
        } finally {
            isLoading.value = false
        }
    }

    // 2. Mencatat keberangkatan pengiriman
    const berangkatkanPengiriman = async (id) => {
        try {
            await api.post(`logistik/pengiriman/${id}/berangkatkan/`)
            return true
        } catch (error) {
            console.error("Gagal memberangkatkan:", error)
            throw error
        }
    }

    // 3. Memuat detail perjalanan dan titik perhentian
    const fetchDetailPengiriman = async (id) => {
        isLoading.value = true
        try {
            const response = await api.get(`logistik/pengiriman/${id}/`)
            detailPengiriman.value = response.data
        } catch (error) {
            console.error("Gagal memuat detail pengiriman:", error)
            throw error
        } finally {
            isLoading.value = false
        }
    }

    // 4. Menandai bahwa kurir sudah tiba di satu titik perhentian
    const tandaiPerhentianSampai = async (pengirimanId, perhentianId) => {
        try {
            await api.post(`logistik/pengiriman/${pengirimanId}/perhentian/${perhentianId}/sampai/`)
            return true
        } catch (error) {
            console.error("Gagal menandai sampai:", error)
            throw error
        }
    }

    // 5. Mengunggah foto Bukti Terima (POD) dengan pengamanan Idempotency-Key (Mode Offline)
    const unggahBuktiTerima = async (pengirimanId, perhentianId, formData) => {
        isUploading.value = true

        // Membuat string unik untuk mencegah duplikasi unggahan jika sinyal jelek
        const idemKey = 'idem-' + Date.now() + '-' + Math.random().toString(36).substring(2)

        try {
            await api.post(
                `logistik/pengiriman/${pengirimanId}/perhentian/${perhentianId}/bukti/`,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                        'Idempotency-Key': idemKey
                    }
                }
            )
            return true
        } catch (error) {
            console.error("Gagal mengunggah POD:", error)
            throw error
        } finally {
            isUploading.value = false
        }
    }

    return {
        isLoading,
        isUploading,
        daftarTugas,
        detailPengiriman,
        fetchTugasSaya,
        berangkatkanPengiriman,
        fetchDetailPengiriman,
        tandaiPerhentianSampai,
        unggahBuktiTerima
    }
}