// src/features/warehouse/composables/usePacking.js
import { ref } from 'vue'
import api from '@/utils/api'
import { bacaError } from '@/utils/error'

export function usePacking() {
    const daftarEntitas = ref([])
    const daftarKemasan = ref([])
    const daftarBatch = ref([])

    const sedangProses = ref(false)
    const galat = ref('')

    // Menyimpan hasil kalkulasi COGS dari Backend
    const pratinjau = ref({
        valid: false,
        qty_kg: 0,
        harga_rata: 0,
        nilai_hpp: 0,
        sisa_qty_batch: 0,
        pesan: ''
    })

    const muatMasterData = async () => {
        sedangProses.value = true
        galat.value = ''
        try {
            // Memanggil endpoint API Backend secara bersamaan
            const [resEntitas, resKemasan, resBatch] = await Promise.all([
                api.get('inventory/entitas/', { params: { aktif: true } }),
                api.get('inventory/kemasan/', { params: { aktif: true } }),
                api.get('produksi/batch/tersedia/')
            ])

            daftarEntitas.value = resEntitas.data?.results || resEntitas.data || []
            daftarKemasan.value = resKemasan.data?.results || resKemasan.data || []
            daftarBatch.value = resBatch.data?.results || resBatch.data || []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat data referensi packing.')
        } finally {
            sedangProses.value = false
        }
    }

    const cekPratinjau = async (batchId, qtyKg) => {
        if (!batchId || qtyKg <= 0) {
            pratinjau.value.valid = false
            return
        }
        try {
            // Endpoint kalkulator HPP tanpa mengubah database
            const { data } = await api.get('inventory/packing/pratinjau/', {
                params: { batch: batchId, qty: qtyKg }
            })
            pratinjau.value = data
        } catch (err) {
            pratinjau.value = {
                valid: false,
                qty_kg: 0,
                harga_rata: 0,
                nilai_hpp: 0,
                sisa_qty_batch: 0,
                pesan: bacaError(err, 'Kalkulasi HPP gagal.')
            }
        }
    }

    const simpanPacking = async (payload) => {
        sedangProses.value = true
        galat.value = ''
        try {
            // FASE 1: Buat Dokumen (DRAFT)
            const resDraft = await api.post('inventory/packing/', payload)
            const draftId = resDraft.data.id

            // FASE 2: Posting & Absorpsi COGS (POSTED)
            const resPost = await api.post(`inventory/packing/${draftId}/post/`)
            return { success: true, data: resPost.data }
        } catch (err) {
            galat.value = bacaError(err, 'Gagal mengeksekusi klaim dan absorpsi COGS.')
            return { success: false, message: galat.value }
        } finally {
            sedangProses.value = false
        }
    }

    return {
        daftarEntitas, daftarKemasan, daftarBatch, pratinjau, sedangProses, galat,
        muatMasterData, cekPratinjau, simpanPacking
    }
}
