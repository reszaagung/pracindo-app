// src/features/produksi/composables/useInputProduksi.js
import { computed, reactive, ref, watch } from 'vue'
import { PRATINJAU_DEBOUNCE_MS } from '@/config/api'
import { normalKg } from '@/utils/uang'
import { apiBatch, apiPratinjau } from '../api'
import { usePemeriksaanStore } from '@/stores/pemeriksaan'

let uid = 0
const barisKosong = () => ({
    _id: ++uid,
    sumber: 'RAW',
    raw: null,
    batch_sumber: null,
    qty_kg: '',
})

export function useInputProduksi() {
    const form = reactive({
        tangki: null,
        nama_hasil: '',
        tekor_kg: '0',
        catatan: '',
        baris: [barisKosong()],
    })

    const pratinjau = ref(null)
    const memuat = ref(false)
    const menyimpan = ref(false)
    const galatServer = ref(null)

    let seq = 0
    let timer = null

    const jenis = computed(() =>
        form.baris.some((b) => b.sumber === 'WIP' && b.batch_sumber) ? 'BLENDING' : 'MIXING',
    )

    function payload() {
        const input_raw = []
        const input_wip = []

        for (const b of form.baris) {
            const q = normalKg(b.qty_kg)
            if (!q || Number(q) <= 0) continue

            if (b.sumber === 'RAW' && b.raw) {
                input_raw.push({ raw: Number(b.raw), qty_kg: Number(q).toFixed(3) })
            }
            if (b.sumber === 'WIP' && b.batch_sumber) {
                input_wip.push({ batch_sumber: Number(b.batch_sumber), qty_kg: Number(q).toFixed(3) })
            }
        }

        return {
            tangki: form.tangki,
            nama_hasil: form.nama_hasil,
            tekor_kg: Number(normalKg(form.tekor_kg) || 0).toFixed(3),
            catatan: form.catatan,
            input_raw,
            input_wip,
        }
    }

    const adaIsi = computed(() => {
        const p = payload()
        return p.input_raw.length > 0 || p.input_wip.length > 0
    })

    async function hitung() {
        if (!adaIsi.value) {
            pratinjau.value = null
            memuat.value = false
            return
        }

        const ini = ++seq
        memuat.value = true
        console.log(`[DEBUG hitung] Request #${ini} dikirim dengan payload:`, payload())

        try {
            const hasil = await apiPratinjau(payload())
            console.log(`[DEBUG hitung] Request #${ini} menerima respons mentah:`, hasil)

            if (ini === seq) {
                // PERHATIAN: Jika apiPratinjau menggunakan axios, struktur aslinya
                // mungkin berada di dalam 'hasil.data'. Cek log konsol Anda nanti!
                pratinjau.value = hasil.data !== undefined ? hasil.data : hasil
            }
        } catch (e) {
            console.error(`[DEBUG hitung] Request #${ini} gagal:`, e)
            if (ini === seq) {
                pratinjau.value = { valid: false, galat: [{ pesan: 'Gagal memuat pratinjau: Cek koneksi' }] }
            }
        } finally {
            memuat.value = false
            console.log(`[DEBUG hitung] Request #${ini} selesai. Status memuat: false`)
        }
    }

    watch(
        () => JSON.stringify(payload()),
        () => {
            clearTimeout(timer)
            timer = setTimeout(hitung, PRATINJAU_DEBOUNCE_MS || 300)
        },
        { immediate: true },
    )

    const galatBaris = computed(() => {
        const peta = {}
        for (const g of pratinjau.value?.galat || []) {
            const m = /^input_(raw|wip)\[(\d+)\]$/.exec(g.field || '')
            if (!m) continue

            const kunci = m[1] === 'raw' ? 'raw' : 'batch_sumber'
            const baris = form.baris.find((b) => String(b[kunci]) === m[2])
            if (baris) peta[baris._id] = g.pesan
        }
        return peta
    })

    const galatUmum = computed(() =>
        (pratinjau.value?.galat || []).filter((g) => !g.field).map((g) => g.pesan),
    )

    const valuasiBaris = computed(() => {
        const peta = {}
        for (const b of pratinjau.value?.baris || []) {
            peta[`${b.sumber}:${b.id_sumber}`] = b
        }
        return peta
    })

    // --- EVALUASI KONDISI TOMBOL SIMPAN DENGAN DEBUGGER ---
    const bolehSimpan = computed(() => {
        const val = pratinjau.value

        const kondisi = {
            tidakSedangMenyimpan: !menyimpan.value,
            tidakSedangMemuat: !memuat.value,
            pratinjauValid: val?.valid === true,   // <--- Titik rawan sering bernilai false/undefined
            tangkiTerpilih: !!form.tangki,
            namaHasilTerisi: Boolean(form.nama_hasil && form.nama_hasil.trim().length > 0)
        }

        console.log('[DEBUG bolehSimpan Evaluasi]:', kondisi, {
            'Nilai pratinjau.value': val,
            'Nilai form.tangki': form.tangki,
            'Nilai form.nama_hasil': form.nama_hasil
        })

        return Object.values(kondisi).every(Boolean)
    })

    function tambahBaris() { form.baris.push(barisKosong()) }
    function hapusBaris(id) {
        if (form.baris.length <= 1) return
        form.baris = form.baris.filter((b) => b._id !== id)
    }

    function reset() {
        form.nama_hasil = ''
        form.tekor_kg = '0'
        form.catatan = ''
        form.baris = [barisKosong()]
        pratinjau.value = null
        galatServer.value = null
    }

    async function simpanDanPosting() {
        if (!bolehSimpan.value) {
            console.warn('[DEBUG Simpan] Ditolak karena bolehSimpan bernilai false!')
            return null
        }

        menyimpan.value = true
        galatServer.value = null
        let draft = null

        try {
            draft = await apiBatch.buat(payload())
            const posted = await apiBatch.posting(draft.id)

            usePemeriksaanStore().periksa()

            reset()
            return posted
        } catch (e) {
            galatServer.value = e
            if (draft) e.draftId = draft.id
            throw e
        } finally {
            menyimpan.value = false
        }
    }

    return {
        form, jenis, pratinjau, memuat, menyimpan, galatServer,
        galatBaris, galatUmum, valuasiBaris, adaIsi, bolehSimpan,
        tambahBaris, hapusBaris, reset, hitung, simpanDanPosting,
    }
}
