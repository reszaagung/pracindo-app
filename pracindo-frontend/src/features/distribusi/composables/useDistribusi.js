import { ref } from 'vue'
import { apiDistribusi } from '../api'

export function useDistribusi() {
    const daftarJadwal = ref([])
    const barangTersedia = ref([])
    const sedangMemuat = ref(false)
    const galat = ref('')

    const muatJadwal = async (params = {}) => {
        sedangMemuat.value = true
        galat.value = ''
        try {
            const data = await apiDistribusi.getSemuaPengiriman(params)
            daftarJadwal.value = data.results || data || []
        } catch (err) {
            galat.value = err.response?.data?.detail || 'Gagal memuat jadwal pengiriman.'
            console.error(err)
        } finally {
            sedangMemuat.value = false
        }
    }

    const muatBarangTersedia = async (entitasId = '') => {
        try {
            const data = await apiDistribusi.getDistribusiTersedia(entitasId)
            barangTersedia.value = data || []
        } catch (err) {
            console.error(err)
        }
    }

    return {
        daftarJadwal,
        barangTersedia,
        sedangMemuat,
        galat,
        muatJadwal,
        muatBarangTersedia
    }
}
