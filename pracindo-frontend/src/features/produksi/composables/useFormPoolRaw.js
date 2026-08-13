/* ===============================================================
   useFormPoolRaw.js — setor RAW ke POOL

   PERBAIKAN UTAMA
   1. produk_id  : field serializernya `produk`, bukan `produk_id`.
                   Rantai `s.produk_id || (s.produk && s.produk.id)` selalu
                   jatuh ke undefined -> NaN -> JSON null -> 400
                   {"produk_id":["This field may not be null."]}
   2. entitas    : dibaca dari `kepemilikan`, bukan ditebak dari
                   grup_bahan. Versi lama mengirim id GrupBahan sebagai
                   entitas_id -- hak setoran tercatat atas nama yang salah.
   3. grup       : DITURUNKAN dari baris stok, bukan dipilih. setor_ke_pool()
                   memakai satu grup_bahan_id untuk sisi RAW dan sisi POOL,
                   jadi "pool tujuan" bukan pilihan bebas.
   4. tangki_raw : ikut dikirim. Tanpa itu backend mencari baris stok RAK,
                   bukan baris tangki yang dipilih operator.
   5. batas qty  : terhadap hak entitas, bukan total baris. Menyetor
                   melebihi hak sendiri menembus hak pemilik lain.
   6. pengiriman : berurutan, bukan Promise.all. Kegagalan di tengah tidak
                   lagi menyisakan setoran separuh tanpa laporan.
   7. idem_key   : terikat produk, bukan indeks baris.

   Butuh backend: GET /stok/?rinci=1 (lihat TAMBAHAN-kepemilikan-di-daftar.py)
   =============================================================== */
import { computed, reactive, ref, watch } from 'vue'
import api from '@/utils/api'
import { bacaError } from '@/utils/error'

const buatIdemKey = () =>
    `setor:${crypto?.randomUUID?.() || Date.now() + '-' + Math.random()}`
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
        referensi: '',   // serializer punya `referensi`, bukan `catatan`
    })

    const barisKosong = () => ({ stok_id: '', qty: '' })
    const bahan = ref([barisKosong(), barisKosong()])

    // Dibuat SEKALI, dipakai ulang di setiap percobaan, baru diganti setelah
    // seluruh baris berhasil. Kalau diganti tiap retry, percobaan kedua
    // menulis ulang setoran yang sudah masuk.
    const idemKey = ref(buatIdemKey())

    const opsi = reactive({ stokGudang: [] })
    const memuat = reactive({ awal: false, kirim: false })
    const galatServer = ref(null)
    const sudahDicoba = ref(false)
    const hasilParsial = ref([])   // laporan per baris kalau ada yang gagal

    /* ---------------- pemuatan ---------------- */

    async function muatDataAwal() {
        memuat.awal = true
        galatServer.value = null
        try {
            const { data } = await api.get('inventory/stok/', {
                // rinci=1 menyertakan `kepemilikan`. Tanpa itu tidak ada cara
                // tahu siapa pemilik baris RAW selain memanggil /stok/{id}/
                // satu per satu.
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

    /* ---------------- turunan ---------------- */

    const adaRincianKepemilikan = computed(
        () => opsi.stokGudang.some((s) => Array.isArray(s.kepemilikan))
    )

    // Daftar entitas yang BENAR-BENAR memiliki RAW, dari SaldoEntitas.
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

    // Berapa yang dimiliki entitas terpilih pada satu baris stok.
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

    // Grup DITURUNKAN, tidak dipilih. setor_ke_pool() memakai satu
    // grup_bahan_id untuk RAW dan POOL sekaligus.
    const grupTerpakai = computed(() => {
        const set = new Set(
            barisTerisi.value.map((b) => stokById(b.stok_id)?.grup_bahan)
                .filter((g) => g !== undefined && g !== null))
        return [...set]
    })
    const grupBahanId = computed(
        () => (grupTerpakai.value.length === 1 ? grupTerpakai.value[0] : null))

    /* ---------------- validasi ---------------- */

    const galat = computed(() => {
        const g = {}

        if (!adaRincianKepemilikan.value && opsi.stokGudang.length) {
            g.kepemilikan =
                'Daftar stok tidak memuat rincian kepemilikan. Backend belum ' +
                'mendukung ?rinci=1 — tanpa itu pemilik bahan tidak bisa ' +
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
            // Batas adalah HAK entitas, bukan isi baris. Menyetor melebihi
            // hak sendiri menembus hak pemilik lain di baris yang sama --
            // dan _geser_pemilik() akan menolaknya (patch P2).
            if (angka(b.qty) > hak) {
                g[`baris_${i}`] =
                    `Hak ${s?.produk_kode ?? 'bahan ini'} hanya ${qty3(hak)}.`
            }
        })
        return g
    })

    const bisaKirim = computed(
        () => Object.keys(galat.value).length === 0 && !memuat.kirim)

    /* ---------------- aksi ---------------- */

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
            // BERURUTAN, bukan Promise.all. Tiap baris transaksi terpisah di
            // backend; kalau baris ketiga gagal, dua baris sebelumnya SUDAH
            // masuk buku besar. Operator harus tahu persis yang mana.
            for (const b of barisTerisi.value) {
                const s = stokById(b.stok_id)
                const produkId = Number(s.produk)   // BUKAN s.produk_id

                await api.post('inventory/setor-ke-pool/', {
                    produk_id: produkId,
                    grup_bahan_id: Number(grupBahanId.value),
                    entitas_id: Number(form.entitas_asal_id),
                    qty: qty3(b.qty),
                    tanggal: form.tanggal,
                    referensi: form.referensi.trim(),
                    // Terikat produk, bukan indeks. Kunci berbasis indeks
                    // menunjuk bahan berbeda begitu satu baris dihapus, dan
                    // setoran nyata dilewati diam-diam sebagai "duplikat".
                    idem_key: `${idemKey.value}:${produkId}`,
                    // Tanpa ini backend mencari baris stok RAK, bukan tangki
                    // yang dipilih operator.
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
                    `mengulang dari awal — perbaiki baris yang gagal saja, ` +
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