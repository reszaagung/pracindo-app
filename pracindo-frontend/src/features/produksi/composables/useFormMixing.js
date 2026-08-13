import { computed, reactive, ref, watch } from 'vue'
import api from '@/utils/api'
import { bacaError } from '@/utils/error'

/* ---------------------------------------------------------------
   Konfigurasi API
--------------------------------------------------------------- */
const API = {
    stok: 'inventory/stok/',
    tangki: 'inventory/tangki/',
    resep: 'produksi/resep/',
    sesi: 'produksi/sesi/',
}

/* ---------------------------------------------------------------
   Helper Format Angka & Tanggal
--------------------------------------------------------------- */
const angka = (v) => {
    const n = Number(String(v ?? '').replace(',', '.'))
    return Number.isFinite(n) ? n : 0
}
const qty3 = (n) => (Math.round(angka(n) * 1000) / 1000).toFixed(3)
const tampil = (n) => angka(n).toLocaleString('id-ID', {
    minimumFractionDigits: 3, maximumFractionDigits: 3,
})

function hariIni() {
    const d = new Date()
    const p = (x) => String(x).padStart(2, '0')
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

function kunciBaru() {
    const id = (crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`)
    return `adonan:${id}`
}

/* ---------------------------------------------------------------
   Composable Utama
--------------------------------------------------------------- */
export function useFormMixing(emit) {
    // State Utama
    const form = reactive({
        nomor_batch: '',
        tanggal: hariIni(),
        resep_id: '',
        mode_tangki: 'ada',
        tangki_hasil_id: '',
        tangki_baru: { kode: '', nama: '', kapasitas_kg: '' },
        target_hasil: '',
        catatan: '',
    })

    const barisKosong = () => ({ stok_id: '', qty: '', otomatis: false })
    const bahan = ref([barisKosong(), barisKosong(), barisKosong()])

    const opsi = reactive({ resep: [], stokPool: [], tangki: [] })
    const memuat = reactive({ awal: false, resep: false, kirim: false })
    const galatServer = ref(null)
    const sudahDicoba = ref(false)
    const idemKey = ref(kunciBaru())

    // --- Fungsi Inisialisasi ---
    async function muatDataAwal() {
        memuat.awal = true
        galatServer.value = null
        try {
            const { data } = await api.get(API.resep, { params: { aktif: 'true' } })
            opsi.resep = data.results || data || []
        } catch (err) {
            galatServer.value = { message: bacaError(err, 'Gagal memuat daftar resep.') }
        } finally {
            memuat.awal = false
        }
    }

    // --- Watcher ---
    watch(() => form.resep_id, async (id) => {
        opsi.stokPool = []
        opsi.tangki = []
        bahan.value = [barisKosong(), barisKosong(), barisKosong()]
        form.tangki_hasil_id = ''
        galatServer.value = null

        if (!id) return

        memuat.resep = true
        try {
            const resepTerpilih = opsi.resep.find(r => String(r.id) === String(id))
            const grupId = resepTerpilih?.grup_bahan_id

            if (grupId) {
                const [stokRes, tangkiRes] = await Promise.all([
                    api.get(API.stok, { params: { lapis: 'POOL', grup: grupId } }),
                    api.get(API.tangki, { params: { grup_bahan: grupId, aktif: 'true' } }),
                ])

                const stokData = stokRes.data.results || stokRes.data || []
                const tangkiData = tangkiRes.data.results || tangkiRes.data || []

                opsi.stokPool = stokData.filter((s) => angka(s.qty) > 0)
                opsi.tangki = tangkiData.filter((t) => t.aktif && String(t.grup_bahan) === String(grupId))
            }
        } catch (err) {
            galatServer.value = { message: bacaError(err, 'Gagal memuat data Pool & Tangki terkait.') }
        } finally {
            memuat.resep = false
        }
    })

    // --- Computed Properties (Turunan & Kalkulasi) ---
    const resepTerpilih = computed(() => opsi.resep.find((r) => String(r.id) === String(form.resep_id)))
    const grupBahanId = computed(() => resepTerpilih.value?.grup_bahan_id)
    const stokById = (id) => opsi.stokPool.find((s) => String(s.id) === String(id))

    function opsiUntukBaris(i) {
        const terpakai = bahan.value
            .map((b, j) => (j === i ? null : b.stok_id))
            .filter(Boolean)
            .map(String)
        return opsi.stokPool.filter((s) => !terpakai.includes(String(s.id)))
    }

    const barisTerisi = computed(() => bahan.value.filter((b) => b.stok_id && angka(b.qty) > 0))
    const totalBahan = computed(() => barisTerisi.value.reduce((t, b) => t + angka(b.qty), 0))
    const targetHasil = computed(() => angka(form.target_hasil))
    const susut = computed(() => totalBahan.value - targetHasil.value)
    const rendemen = computed(() => totalBahan.value > 0 ? (targetHasil.value / totalBahan.value) * 100 : null)
    const tangkiTerpilih = computed(() => opsi.tangki.find((t) => String(t.id) === String(form.tangki_hasil_id)))


    const galat = computed(() => {
        const g = {}
        if (!form.tanggal) g.tanggal = 'Tanggal wajib diisi.'
        if (!form.resep_id) g.resep_id = 'Pilih resep adonan.'

        if (form.mode_tangki === 'ada') {
            if (!form.tangki_hasil_id) {
                g.tangki_hasil_id = 'Pilih tangki perantara/tujuan.'
            } else {
                const t = tangkiTerpilih.value
                if (t && targetHasil.value > angka(t.ruang_kosong_kg)) {
                    g.tangki_hasil_id = `Sisa ruang tangki ${t.kode} tinggal ${tampil(t.ruang_kosong_kg)} kg.`
                }
            }
        } else {
            const tb = form.tangki_baru
            if (!tb.kode.trim()) g.tangki_baru_kode = 'Kode tangki wajib diisi.'
            if (!tb.nama.trim()) g.tangki_baru_nama = 'Nama tangki wajib diisi.'
            if (angka(tb.kapasitas_kg) <= 0) g.tangki_baru_kapasitas = 'Kapasitas harus > 0.'
        }

        if (targetHasil.value <= 0) g.target_hasil = 'Target hasil (kg) wajib diisi.'
        return g
    })

    const peringatan = computed(() => {
        const p = []
        if (rendemen.value !== null && rendemen.value > 100) {
            p.push('Target hasil melebihi total bahan input manual.')
        }
        return p
    })

    const bisaKirim = computed(() => Object.keys(galat.value).length === 0 && !memuat.kirim)

    function tambahBaris() { bahan.value.push(barisKosong()) }
    function hapusBaris(i) { if (bahan.value.length > 1) bahan.value.splice(i, 1) }

    function reset() {
        form.nomor_batch = ''
        form.resep_id = ''
        form.tangki_hasil_id = ''
        form.mode_tangki = 'ada'
        form.tangki_baru = { kode: '', nama: '', kapasitas_kg: '' }
        form.target_hasil = ''
        form.catatan = ''
        bahan.value = [barisKosong(), barisKosong(), barisKosong()]
        idemKey.value = kunciBaru()
        sudahDicoba.value = false
    }

    async function kirim() {
        sudahDicoba.value = true
        galatServer.value = null
        if (!bisaKirim.value) return

        memuat.kirim = true
        try {
            const daftarPengiriman = barisTerisi.value.map((b, index) => {
                const s = stokById(b.stok_id)
                const idProduk = s.produk_id || (s.produk && s.produk.id)
                const payload = {
                    entitas_id: Number(form.entitas_asal_id),
                    grup_bahan_id: Number(grupBahanId.value),
                    produk_id: Number(idProduk),
                    qty: (Math.round(angka(b.qty) * 1000) / 1000).toFixed(3),
                    tanggal: form.tanggal
                }

                if (form.catatan && form.catatan.trim()) {
                    payload.referensi = form.catatan.trim()
                }
                if (idemKey.value) {
                    payload.idem_key = `${idemKey.value}-${index}`
                }

                if (s.tangki || s.tangki_id) {
                    payload.tangki_raw_id = Number(s.tangki || s.tangki_id)
                }

                return api.post('inventory/setor-ke-pool/', payload)
            })

  
            await Promise.all(daftarPengiriman)
            emit('tersimpan', { sukses: true })
            reset()
        } catch (err) {
            galatServer.value = { message: bacaError(err, 'Gagal mengeksekusi transfer ke Pool.') }
        } finally {
            memuat.kirim = false
        }
    }

    const tampilkan = (kunci) => sudahDicoba.value && galat.value[kunci]
    const galatBaris = (i) => (sudahDicoba.value ? galat.value.baris?.[i] : null)

    return {
        form, bahan, opsi, memuat, galatServer, galat, peringatan, bisaKirim, totalBahan,
        targetHasil, susut, rendemen, muatDataAwal, stokById, opsiUntukBaris, tambahBaris,
        hapusBaris, kirim, reset, tampil, tampilkan, galatBaris
    }
}