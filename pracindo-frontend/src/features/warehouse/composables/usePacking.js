// src/features/warehouse/composables/usePacking.js
import { ref } from 'vue'
import { warehouseApi } from '../api' 
import { apiProduksi } from '@/features/produksi/api'
import { bacaError } from '@/utils/error'
import { angka } from '@/utils/format' // Wajib di-import untuk format teks di belakang layar

export function usePacking() {
    const daftarEntitas = ref([])
    const daftarKemasan = ref([])
    const daftarBatch = ref([])

    const sedangProses = ref(false)
    const galat = ref('')

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
            const [resEntitas, resKemasan, resBatch] = await Promise.all([
                warehouseApi.getEntitasAktif(),
                warehouseApi.getKemasanAktif(),
                apiProduksi.getBatches({ status: 'POSTED' }) 
            ])

            daftarEntitas.value = resEntitas.data?.results || resEntitas.data || []
            daftarKemasan.value = resKemasan.data?.results || resKemasan.data || []
            
            // 1. AMBIL DATA MENTAH DARI BACKEND
            const rawBatch = resBatch.data?.results || resBatch.data || []

            // 2. FILTERING DEWA: Buang semua batch yang sisanya 0
            const batchAdaIsi = rawBatch.filter(b => {
                const qty = b.yield_kg ?? b.yield ?? b.sisa_qty ?? 0
                return Number(qty) > 0 // Hanya loloskan jika lebih dari 0
            })

            // 3. MAPPING UI: Format teks sekali saja agar browser tidak lag
            daftarBatch.value = batchAdaIsi.map(b => {
                const qty = b.yield_kg ?? b.yield ?? b.sisa_qty ?? 0
                const harga = b.harga_rata ?? 0
                return {
                    ...b,
                    label_dropdown: `${b.batch || b.nomor} - ${b.nama_hasil} (Sisa: ${angka(qty, 3)} Kg | Rp ${angka(harga)})`
                }
            })

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
            const { data } = await warehouseApi.getPratinjauPacking(batchId, qtyKg)
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
            const resDraft = await warehouseApi.simpanDraftPacking(payload)
            const draftId = resDraft.data.id

            const resPost = await warehouseApi.postingPacking(draftId)
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