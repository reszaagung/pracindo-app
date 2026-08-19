import { computed, reactive, ref, watch } from 'vue'
import api from '@/utils/api'
import { bacaError } from '@/utils/error'

const buatIdemKey = () => `setor:${crypto?.randomUUID?.() || Date.now() + '-' + Math.random()}`
const hariIni = () => new Date().toISOString().split('T')[0]

const angka = (v) => {
    const n = Number(String(v ?? '').replace(',', '.'))
    return Number.isFinite(n) ? n : 0
}

const qty3 = (n) => (Math.round(angka(n) * 1000) / 1000).toFixed(3)

export function useFormPoolRaw(emit) {
    const form = reactive({
        entitas_asal_id: '',
        tanggal: hariIni(),
        referensi: '',
    })

    const barisKosong = () => ({ stok_id: '', qty: '' })
    const bahan = ref([barisKosong(), barisKosong()])
    const idemKey = ref(buatIdemKey())
    const opsi = reactive({ stokGudang: [] })
    const memuat = reactive({ awal: false, kirim: false })
    const galatServer = ref(null)
    const sudahDicoba = ref(false)
    const hasilParsial = ref([])

    async function muatDataAwal() {
        memuat.awal = true
        galatServer.value = null
        try {
            const { data } = await api.get('inventory/stok/', {
                params: { lapis: 'RAW', ada_isi: '1', rinci: '1' },
            })
            opsi.stokGudang = data.results || data || []
        } catch (err) {
            galatServer.value = {
                message: bacaError(err, 'Gagal memuat stok Bahan Mentah (RAW).'),
            }
        } finally {
            memuat.awal = false
        }
    }

    const adaRincianKepemilikan = computed(
        () => opsi.stokGudang.some((s) => Array.isArray(s.kepemilikan))
    )

    const opsiEntitasAsal = computed(() => {
        const map = new Map()
        for (const s of opsi.stokGudang) {
            for (const k of s.kepemilikan ?? []) {
                if (angka(k.qty) > 0 && !map.has(k.entitas)) {
                    map.set(k.entitas, { id: k.entitas, kode: k.entitas_kode })
                }
            }
        }
        return [...map.values()].sort((a, b) => a.kode.localeCompare(b.kode))
    })

    const stokById = (id) => opsi.stokGudang.find((s) => String(s.id) === String(id))

    function hakEntitas(stok) {
        if (!stok || !form.entitas_asal_id) return 0
        const k = (stok.kepemilikan ?? []).find(
            (x) => String(x.entitas) === String(form.entitas_asal_id))
        return angka(k?.qty)
    }

    function opsiUntukBaris(i) {
        if (!form.entitas_asal_id) return []
        const terpakai = bahan.value
            .map((b, j) => (j === i ? null : b.stok_id))
            .filter(Boolean)
            .map(String)
        return opsi.stokGudang.filter(
            (s) => hakEntitas(s) > 0 && !terpakai.includes(String(s.id)))
    }

    const barisTerisi = computed(
        () => bahan.value.filter((b) => b.stok_id && angka(b.qty) > 0))

    const totalBahan = computed(
        () => barisTerisi.value.reduce((t, b) => t + angka(b.qty), 0))

    const grupTerpakai = computed(() => {
        const set = new Set(
            barisTerisi.value.map((b) => stokById(b.stok_id)?.grup_bahan)
                .filter((g) => g !== undefined && g !== null))
        return [...set]
    })

    const grupBahanId = computed(
        () => (grupTerpakai.value.length === 1 ? grupTerpakai.value[0] : null))

    const galat = computed(() => {
        const g = {}
        if (!adaRincianKepemilikan.value && opsi.stokGudang.length) {
            g.kepemilikan =
                'Daftar stok tidak memuat rincian kepemilikan. Backend belum ' +
                'mendukung ?rinci=1 tanpa itu pemilik bahan tidak bisa ' +
                'ditentukan dan setoran akan tercatat atas nama yang salah.'
        }
        if (!form.entitas_asal_id) g.entitas_asal_id = 'Pilih entitas pemilik bahan.'
        if (!form.tanggal) g.tanggal = 'Tanggal wajib diisi.'
        if (!barisTerisi.value.length) g.baris = 'Isi minimal satu bahan.'
        if (grupTerpakai.value.length > 1) {
            g.baris = 'Semua bahan harus berasal dari grup yang sama. ' +
                'Setoran lintas grup dipisah jadi dua transaksi.'
        }

        bahan.value.forEach((b, i) => {
            if (!b.stok_id || angka(b.qty) <= 0) return
            const s = stokById(b.stok_id)
            const hak = hakEntitas(s)
            if (angka(b.qty) > hak) {
                g[`baris_${i}`] = `Hak ${s?.produk_kode ?? 'bahan ini'} hanya ${qty3(hak)}.`
            }
        })
        return g
    })

    const bisaKirim = computed(
        () => Object.keys(galat.value).length === 0 && !memuat.kirim)

    function tambahBaris() { bahan.value.push(barisKosong()) }
    function hapusBaris(i) { if (bahan.value.length > 1) bahan.value.splice(i, 1) }

    watch(() => form.entitas_asal_id, () => {
        bahan.value = [barisKosong(), barisKosong()]
    })

    function reset() {
        form.referensi = ''
        form.entitas_asal_id = ''
        bahan.value = [barisKosong(), barisKosong()]
        sudahDicoba.value = false
        hasilParsial.value = []
        idemKey.value = buatIdemKey()
    }

    async function kirim() {
        sudahDicoba.value = true
        galatServer.value = null
        hasilParsial.value = []
        if (!bisaKirim.value) return

        memuat.kirim = true
        const berhasil = []
        try {
            for (const b of barisTerisi.value) {
                const s = stokById(b.stok_id)
                const produkId = Number(s.produk)
                await api.post('inventory/setor-ke-pool/', {
                    produk_id: produkId,
                    grup_bahan_id: Number(grupBahanId.value),
                    entitas_id: Number(form.entitas_asal_id),
                    qty: qty3(b.qty),
                    tanggal: form.tanggal,
                    referensi: form.referensi.trim(),
                    idem_key: `${idemKey.value}:${produkId}`,
                    tangki_raw_id: s.tangki ?? null,
                    tangki_pool_id: null,
                })
                berhasil.push({ produk: s.produk_kode, qty: qty3(b.qty) })
            }
            emit('tersimpan', { sukses: true, baris: berhasil })
            reset()
        } catch (err) {
            hasilParsial.value = berhasil
            const dasar = bacaError(err, 'Gagal mengeksekusi transfer ke Pool.')
            galatServer.value = {
                message: berhasil.length
                    ? `${dasar}\n\n${berhasil.length} baris SUDAH tersimpan ` +
                    `(${berhasil.map((x) => x.produk).join(', ')}). Jangan ` +
                    `mengulang dari awal perbaiki baris yang gagal saja, ` +
                    `kunci idempotency akan melewati yang sudah masuk.`
                    : dasar,
            }
        } finally {
            memuat.kirim = false
        }
    }

    const tampilkan = (kunci) => sudahDicoba.value && galat.value[kunci]
    const galatBaris = (i) => (sudahDicoba.value ? galat.value[`baris_${i}`] : null)

    return {
        form, bahan, opsi, memuat, galatServer, galat, bisaKirim, totalBahan,
        opsiEntitasAsal, grupBahanId, hakEntitas, hasilParsial,
        adaRincianKepemilikan,
        muatDataAwal, stokById, opsiUntukBaris, tambahBaris, hapusBaris,
        kirim, reset, tampilkan, galatBaris,
    }
}
