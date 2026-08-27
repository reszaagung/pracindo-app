import { ref } from 'vue'
import api from '@/utils/api'

export function useFormPurchasePackageing() {
    const listEntitas = ref([])
    const listSupplier = ref([])
    const sedangProses = ref(false)
    const pesanError = ref('')
    const previewNomor = ref('')
    const periodeDitutup = ref(false)

    const muatDataMaster = async () => {
        try {
            const [resEntitas, resSupplier] = await Promise.all([
                api.get('master/entitas/'),
                api.get('master/suplier/')
            ])
            listEntitas.value = resEntitas.data?.results || resEntitas.data || []
            listSupplier.value = resSupplier.data?.results || resSupplier.data || []
        } catch (error) {
            console.error('Gagal memuat data master:', error)
            pesanError.value = 'Gagal memuat data master. Pastikan koneksi dan API berjalan.'
        }
    }

    const muatPreviewNomor = async (entitasId, tanggal) => {
        if (!entitasId || !tanggal) return
        try {
            // Arahkan ke endpoint khusus kemasan agar format penomorannya tidak tertukar
            const res = await api.get('accounting/po-kemasan/preview-nomor/', {
                params: { entitas_id: entitasId, tanggal, jenis: 'KEMASAN' }
            })
            previewNomor.value = res.data?.nomor || 'Draft PO (Kemasan)'
        } catch (error) {
            previewNomor.value = 'Gagal memuat nomor'
        }
    }

    const cekStatusPeriode = async (entitasId, tanggal) => {
        try {
            const res = await api.get('accounting/periode/status/', {
                params: { entitas_id: entitasId, tanggal }
            })
            periodeDitutup.value = res.data?.is_closed || false
            if (periodeDitutup.value) {
                pesanError.value = 'Buku periode untuk tanggal tersebut telah ditutup.'
            }
        } catch (error) {
            periodeDitutup.value = false
        }
    }

    const simpanPO = async (payload, isDraft = true) => {
        sedangProses.value = true
        try {
            // KUNCI: Endpoint sekarang menembak ke jalur yang sudah diisolasi di backend
            const endpoint = 'accounting/po-kemasan/'
            const response = await api.post(endpoint, payload)
            return { success: true, data: response.data }
        } catch (error) {
            return {
                success: false,
                message: error.response?.data?.message || error.message || 'Terjadi kesalahan sistem'
            }
        } finally {
            sedangProses.value = false
        }
    }

    return {
        listEntitas,
        listSupplier,
        sedangProses,
        pesanError,
        previewNomor,
        periodeDitutup,
        muatDataMaster,
        muatPreviewNomor,
        cekStatusPeriode,
        simpanPO
    }
}
