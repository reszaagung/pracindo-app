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
            // PERBAIKAN: Menjamin pembacaan angka desimal yang aman
            // baik menggunakan titik maupun koma dari input operator
            let qStr = normalKg(b.qty_kg) || '0'
            qStr = qStr.toString().replace(',', '.')
            const q = parseFloat(qStr)

            if (isNaN(q) || q <= 0) continue

            if (b.sumber === 'RAW' && b.raw) {
                input_raw.push({ raw: Number(b.raw), qty_kg: Number(q).toFixed(3) })
            }
            if (b.sumber === 'WIP' && b.batch_sumber) {
                input_wip.push({ batch_sumber: Number(b.batch_sumber), qty_kg: Number(q).toFixed(3) })
            }
        }

        let tekorStr = normalKg(form.tekor_kg) || '0'
        tekorStr = tekorStr.toString().replace(',', '.')
        let tekor = parseFloat(tekorStr)
        if (isNaN(tekor) || tekor < 0) tekor = 0

        return {
            tangki: form.tangki,
            nama_hasil: form.nama_hasil,
            tekor_kg: Number(tekor).toFixed(3),
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
            galatServer.value = null
            memuat.value = false
            return
        }

        const ini = ++seq
        memuat.value = true
        galatServer.value = null // Bersihkan pesan error sebelumnya saat memuat ulang

        try {
            const hasil = await apiPratinjau(payload())

            if (ini === seq) {
                const data = hasil.data !== undefined ? hasil.data : hasil
                pratinjau.value = data

                // PERBAIKAN FATAL: Mencegah error kalkulasi tertelan diam-diam.
                // Jika backend menolak pratinjau, paksa UI memunculkan alasannya!
                if (data && data.valid === false && data.galat && data.galat.length > 0) {
                    const pesanError = data.galat.map(g => g.pesan).join(' | ')
                    galatServer.value = {
                        pesan: pesanError,
                        konflikSaldo: true // Memicu UI menguning/memerah agar operator sadar
                    }
                }
            }
        } catch (e) {
            if (ini === seq) {
                pratinjau.value = { valid: false, galat: [{ pesan: 'Gagal memuat pratinjau: Cek koneksi' }] }
                galatServer.value = { pesan: 'Gagal terhubung ke server untuk kalkulasi.', konflikSaldo: false }
            }
        } finally {
            // PERBAIKAN: Hanya matikan status memuat jika ini adalah antrean hitung terakhir.
            // Sebelumnya, antrean yang selesai lebih cepat mematikan indikator loading lebih awal.
            if (ini === seq) {
                memuat.value = false
            }
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

    const bolehSimpan = computed(() => {
        const val = pratinjau.value

        const kondisi = {
            tidakSedangMenyimpan: !menyimpan.value,
            tidakSedangMemuat: !memuat.value,
            pratinjauValid: val?.valid === true,
            tangkiTerpilih: !!form.tangki,
            namaHasilTerisi: Boolean(form.nama_hasil && form.nama_hasil.trim().length > 0)
        }

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
