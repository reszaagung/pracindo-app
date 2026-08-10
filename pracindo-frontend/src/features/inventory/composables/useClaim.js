// src/features/inventory/composables/useClaim.js
// Kontrak diverifikasi dari inventory/views.py & serializers.py — lihat
// SPEK-BACKEND.md §3.x Inventory.
//
// posisi-klaim/ dan isi-pool/ BUKAN daftar berpaginasi — jangan unwrap
// .results, hasilnya undefined. Keduanya WAJIB diberi ?grup=, backend
// membalas 400 tanpanya.
//
// setor-ke-pool/, klaim-hasil/, dan opname/ menerima idem_key sebagai
// field body (bukan header). Kalau dikosongkan, backend membuat kunci
// acak sendiri per request — artinya retry TIDAK dianggap sama. Pemanggil
// (komponen form) wajib membuat idem_key SEKALI saat form dibuka dan
// memakainya ulang kalau submit gagal & dicoba lagi — composable ini
// sengaja tidak membuatkannya sendiri di dalam fungsi submit.

import { ref } from 'vue'
import api from '@/utils/api'
import { bacaError } from '@/utils/error'

export function useClaim() {
    const posisiKlaim = ref([])
    const isiPool = ref(null)
    const sedangProses = ref(false)
    const galat = ref('')

    /** @param {number|string} grup wajib diisi — backend 400 tanpanya */
    const muatPosisiKlaim = async (grup) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get('inventory/posisi-klaim/', { params: { grup } })
            posisiKlaim.value = data || []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat posisi klaim.')
        } finally {
            sedangProses.value = false
        }
    }

    /** @param {number|string} grup wajib diisi — backend 400 tanpanya */
    const muatIsiPool = async (grup) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get('inventory/isi-pool/', { params: { grup } })
            isiPool.value = data
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat isi pool.')
        } finally {
            sedangProses.value = false
        }
    }

    const kirimAksi = async (url, payload) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.post(url, payload)
            return { success: true, data }
        } catch (err) {
            galat.value = bacaError(err, 'Gagal menyimpan.')
            return { success: false, message: galat.value }
        } finally {
            sedangProses.value = false
        }
    }

    /** GUDANG/PRODUKSI saja — backend menolak role lain. Perlu idem_key dari pemanggil. */
    const setorKePool = (payload) => kirimAksi('inventory/setor-ke-pool/', payload)

    /** GUDANG/PRODUKSI saja — backend menolak role lain. Perlu idem_key dari pemanggil. */
    const klaimHasil = (payload) => kirimAksi('inventory/klaim-hasil/', payload)

    /** SUPERVISOR saja — backend menolak role lain. Perlu idem_key dari pemanggil. */
    const opname = (payload) => kirimAksi('inventory/opname/', payload)

    return {
        posisiKlaim, isiPool, sedangProses, galat,
        muatPosisiKlaim, muatIsiPool, setorKePool, klaimHasil, opname,
    }
}
