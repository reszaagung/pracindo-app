import { computed, reactive, ref, watch } from 'vue'
import { PRATINJAU_DEBOUNCE_MS } from '@/config/api'
import { normalKg } from '@/utils/uang'
import { apiBatch, apiPratinjau } from '../api'
import { usePemeriksaanStore } from '@/stores/pemeriksaan'

let uid = 0
const barisKosong = () => ({
    _id: ++uid,
    sumber: 'RAW',        // 'RAW' | 'WIP'
    raw: null,            // id RawMaterial
    batch_sumber: null,   // id Batch
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
            if (!q) continue
            if (b.sumber === 'RAW' && b.raw) input_raw.push({ raw: b.raw, qty_kg: q })
            if (b.sumber === 'WIP' && b.batch_sumber) input_wip.push({ batch_sumber: b.batch_sumber, qty_kg: q })
        }

        return {
            tangki: form.tangki,
            nama_hasil: form.nama_hasil,
            tekor_kg: normalKg(form.tekor_kg) || '0.000',
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
            return
        }

        const ini = ++seq
        memuat.value = true

        try {
            const hasil = await apiPratinjau(payload())
            if (ini === seq) pratinjau.value = hasil
        } catch (e) {
            if (ini === seq) {
                pratinjau.value = { valid: false, galat: [{ pesan: 'Gagal memuat pratinjau: Cek koneksi' }] }
            }
        } finally {
            if (ini === seq) memuat.value = false
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

    const bolehSimpan = computed(() =>
        !menyimpan.value &&
        !memuat.value &&
        pratinjau.value?.valid === true &&
        !!form.tangki &&
        form.nama_hasil.trim().length > 0
    )

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
        if (!bolehSimpan.value) return null

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
