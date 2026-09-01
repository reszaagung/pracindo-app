
import { ref } from 'vue'
import { warehouseApi } from '../api'
import { apiProduksi } from '@/features/produksi/api'
import { bacaError } from '@/utils/error'
import { angka } from '@/utils/format'

export function usePacking() {
    const daftarEntitas = ref([])
    const daftarKemasan = ref([])
    const daftarBatch = ref([])
    const daftarProduk = ref([])

    const sedangProses = ref(false)
    const galat = ref('')

    const pratinjau = ref({
        valid: false,
        qty_kg: 0,
        harga_per_kg: 0,
        nilai_tagihan: 0,
        sisa_qty_batch: 0,
        menghabiskan: false,
        peringatan: [],
        pesan: ''
    })

    /**
     * Mengambil ID dari berbagai bentuk value:
     *
     * 15
     * "15"
     * { id: 15 }
     * { pk: 15 }
     * { produk_id: 15 }
     * { kode: 15 }
     */
    const ambilId = (value) => {
        if (value === null || value === undefined || value === '') {
            return null
        }

        if (typeof value === 'object') {
            const id =
                value.id ??
                value.pk ??
                value.produk_id ??
                value.entitas_id ??
                value.batch_id ??
                value.kemasan_id ??
                value.kode

            if (id === null || id === undefined || id === '') {
                return null
            }

            const numericId = Number(id)
            return Number.isFinite(numericId) ? numericId : id
        }

        const numericValue = Number(value)

        return Number.isFinite(numericValue)
            ? numericValue
            : value
    }

    const muatMasterData = async () => {
        sedangProses.value = true
        galat.value = ''

        try {
            const [
                resEntitas,
                resKemasan,
                resBatch,
                resProduk
            ] = await Promise.all([
                warehouseApi.getEntitasAktif(),
                warehouseApi.getKemasanAktif(),
                apiProduksi.getBatches({ status: 'POSTED' }),
                warehouseApi.getMasterProduk({
                    kategori: 'FINISHED_GOODS'
                })
            ])

            const ekstrakData = (res) => {
                if (!res) return []

                if (Array.isArray(res)) {
                    return res
                }

                if (Array.isArray(res.data?.results)) {
                    return res.data.results
                }

                if (Array.isArray(res.results)) {
                    return res.results
                }

                if (Array.isArray(res.data)) {
                    return res.data
                }

                return []
            }

            // =========================
            // ENTITAS
            // =========================
            daftarEntitas.value = ekstrakData(resEntitas)

            // =========================
            // KEMASAN
            // =========================
            const rawKemasan = ekstrakData(resKemasan)

            daftarKemasan.value = rawKemasan.map((k) => {
                const qtyUnit = Number(k.qty_unit) || 0
                const totalNilai = Number(k.nilai) || 0

                const unitCost =
                    k.harga_satuan ??
                    (
                        qtyUnit > 0
                            ? totalNilai / qtyUnit
                            : 0
                    )

                return {
                    ...k,
                    harga_satuan_calculated: Number(unitCost) || 0,

                    label_dropdown:
                        `${k.produk_nama || 'Kemasan'} ` +
                        `(Stok: ${angka(qtyUnit, 0)} Unit | ` +
                        `@Rp ${angka(unitCost)})`
                }
            })

            // =========================
            // PRODUK
            // =========================
            const rawProduk = ekstrakData(resProduk)

            daftarProduk.value = rawProduk.map((p) => ({
                ...p,

                label_display:
                    p.nama_item ||
                    p.nama ||
                    p.nama_produk ||
                    `Produk #${p.kode_item}`
            }))

            // =========================
            // BATCH
            // =========================
            const rawBatch = ekstrakData(resBatch)

            const batchAdaIsi = rawBatch.filter(
                (b) => Number(b.qty_hasil ?? 0) > 0
            )

            daftarBatch.value = batchAdaIsi.map((b) => {
                const qty = Number(b.qty_hasil ?? 0)
                const kodeTangki = b.tangki_kode ?? 'TANGKI'
                const namaHasil = b.nama_hasil ?? 'WIP'
                const noBatch = b.nomor
                    ? ` | Batch: ${b.nomor}`
                    : ''

                return {
                    ...b,

                    label_dropdown:
                        `[${kodeTangki}] ${namaHasil} ` +
                        `(Sisa: ${angka(qty, 3)} Kg${noBatch})`
                }
            })

        } catch (err) {
            galat.value = bacaError(
                err,
                'Gagal memuat data Master & WIP Produksi.'
            )
        } finally {
            sedangProses.value = false
        }
    }

    // =========================
    // PREVIEW PACKING
    // =========================
    const cekPratinjau = async (batchValue, qtyValue) => {
        const batchId = ambilId(batchValue)
        const qtyKg = Number(qtyValue) || 0

        if (!batchId || qtyKg <= 0) {
            pratinjau.value = {
                valid: false,
                qty_kg: 0,
                harga_per_kg: 0,
                nilai_tagihan: 0,
                sisa_qty_batch: 0,
                menghabiskan: false,
                peringatan: [],
                pesan: ''
            }

            return
        }

        try {
            const { data } =
                await warehouseApi.getPratinjauPacking(
                    batchId,
                    qtyKg
                )

            pratinjau.value = {
                valid: Boolean(data?.valid),
                qty_kg: Number(data?.qty_kg) || 0,
                harga_per_kg: Number(data?.harga_per_kg) || 0,
                nilai_tagihan: Number(data?.nilai_tagihan) || 0,
                sisa_qty_batch: Number(data?.sisa_qty_batch) || 0,
                menghabiskan: Boolean(data?.menghabiskan),
                peringatan: data?.peringatan || [],
                pesan: data?.pesan || ''
            }

        } catch (err) {
            pratinjau.value = {
                valid: false,
                qty_kg: 0,
                harga_per_kg: 0,
                nilai_tagihan: 0,
                sisa_qty_batch: 0,
                menghabiskan: false,
                peringatan: [],
                pesan: bacaError(
                    err,
                    'Kalkulasi HPP gagal.'
                )
            }
        }
    }

    // =========================
    // SIMPAN + POSTING
    // =========================
    const simpanPacking = async (payload) => {
        sedangProses.value = true
        galat.value = ''

        try {
            const normalizedPayload = {
                entitas: ambilId(payload?.entitas),
                batch: ambilId(payload?.batch),
                produk: ambilId(payload?.produk),
                kemasan: ambilId(payload?.kemasan),
                total_unit: Number(payload?.total_unit) || 0,
                qty_kg: Number(payload?.qty_kg) || 0
            }

            // Validasi sebelum POST
            if (!normalizedPayload.entitas) {
                throw new Error('Entitas belum dipilih.')
            }

            if (!normalizedPayload.batch) {
                throw new Error('Batch belum dipilih.')
            }

            if (!normalizedPayload.produk) {
                throw new Error('Produk belum dipilih.')
            }

            if (!normalizedPayload.kemasan) {
                throw new Error('Kemasan belum dipilih.')
            }

            if (normalizedPayload.total_unit <= 0) {
                throw new Error('Total unit harus lebih dari 0.')
            }

            if (normalizedPayload.qty_kg <= 0) {
                throw new Error('Qty kg harus lebih dari 0.')
            }

            console.log(
                '[PACKING] Payload Draft:',
                normalizedPayload
            )

            // 1. Buat DRAFT
            const resDraft =
                await warehouseApi.simpanDraftPacking(
                    normalizedPayload
                )

            const draftId = resDraft?.data?.id

            if (!draftId) {
                throw new Error(
                    'Draft Packing berhasil dibuat tetapi ID tidak ditemukan.'
                )
            }

            console.log(
                '[PACKING] Draft berhasil dibuat:',
                draftId
            )

            // 2. Posting
            const resPost =
                await warehouseApi.postingPacking(
                    draftId
                )

            console.log(
                '[PACKING] Posting berhasil:',
                resPost?.data
            )

            return {
                success: true,
                data: resPost?.data,
                draft: resDraft?.data
            }

        } catch (err) {
            console.error(
                '[PACKING] Gagal:',
                err
            )

            galat.value = bacaError(
                err,
                'Gagal mengeksekusi Packing.'
            )

            return {
                success: false,
                message: galat.value
            }

        } finally {
            sedangProses.value = false
        }
    }

    return {
        daftarEntitas,
        daftarKemasan,
        daftarBatch,
        daftarProduk,

        pratinjau,
        sedangProses,
        galat,

        muatMasterData,
        cekPratinjau,
        simpanPacking,

        // Bisa digunakan component apabila diperlukan
        ambilId
    }
}

