import { computed, reactive, ref } from 'vue'
import { normalKg } from '@/utils/uang'
import { apiBatch } from '../api'
import { usePemeriksaanStore } from '@/stores/pemeriksaan'

let uid = 0
const barisKosong = () => ({
    _id: ++uid,
    sumber: 'RAW',
    raw: null,
    batch_sumber: null,
    qty_kg: ''
})

export function useInputProduksi() {
    const form = reactive({
        tangki: null,
        nama_hasil: '',
        tekor_kg: '0',
        catatan: '',
        baris: [barisKosong()],
    })

    const menyimpan = ref(false)
    const galatServer = ref(null)

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

    const bolehSimpan = computed(() =>
        !menyimpan.value &&
        !!form.tangki &&
        form.nama_hasil.trim().length > 0 &&
        adaIsi.value
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

    const galatBaris = computed(() => ({}))
    const valuasiBaris = computed(() => ({}))

    return {
        form, jenis, menyimpan, galatServer,
        galatBaris, valuasiBaris, bolehSimpan,
        tambahBaris, hapusBaris, simpanDanPosting,
    }
}
