import { ref } from 'vue'
import { apiDistribusi } from '../api'

export function useArmada() {
    const daftarArmada = ref([])
    const sedangMemuat = ref(false)

    const muatArmada = async () => {
        sedangMemuat.value = true
        try {
            const data = await apiDistribusi.getArmada()
            daftarArmada.value = data.results || data || []
        } catch (err) {
            console.error(err)
        } finally {
            sedangMemuat.value = false
        }
    }

    return {
        daftarArmada,
        sedangMemuat,
        muatArmada
    }
}
