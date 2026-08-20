import { ref } from 'vue'
import { apiKurir } from '../api'


export function useCourier() {
    const daftarPengiriman = ref([])
    const sedangMemuat = ref(false)

    const muatTugas = async () => {
        sedangMemuat.value = true
        try {
            const data = await apiKurir.getTugasSaya()
            daftarPengiriman.value = data || []
        } catch (error) {
            console.error(error)
        } finally {
            sedangMemuat.value = false
        }
    }

    const berangkatkan = async (pengirimanId) => {
        try {
            await apiKurir.berangkatkanTugas(pengirimanId)
            await muatTugas()
            return { success: true }
        } catch (error) {
            return { success: false, error }
        }
    }

    const tandaiSampai = async (pengirimanId, perhentianId) => {
        try {
            await apiKurir.tandaiSampai(pengirimanId, perhentianId)
            await muatTugas()
            return { success: true }
        } catch (error) {
            return { success: false, error }
        }
    }

    const unggahBukti = async (pengirimanId, perhentianId, file, namaPenerima) => {
        try {
            const formData = new FormData()
            formData.append('foto', file)
            formData.append('catatan', `Penerima: ${namaPenerima}`)

            const idemKey = `bukti-${perhentianId}-${Date.now()}`
            await apiKurir.unggahBukti(pengirimanId, perhentianId, formData, idemKey)

            await muatTugas()
            return { success: true }
        } catch (error) {
            return { success: false, error }
        }
    }

    return {
        daftarPengiriman,
        sedangMemuat,
        muatTugas,
        berangkatkan,
        tandaiSampai,
        unggahBukti
    }
}
