import { reactive, ref, computed, watch } from 'vue'

const API = {
    kemasan: '/api/inventory/kemasan/',
    tangki: '/api/inventory/tangki/',
    entitas: '/api/core/entitas/', // Sesuaikan dengan endpoint Entitas kamu
    rencana: '/api/inventory/klaim-kemasan/rencana/',
    klaim: '/api/inventory/klaim-kemasan/',
}

async function apiGet(url, params = {}) {
    const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== null && v !== ''))
    const r = await fetch(`${url}?${q}`, { credentials: 'include' })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    const d = await r.json()
    return Array.isArray(d) ? d : (d.results ?? [])
}

async function apiPost(url, body) {
    const r = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    })
    if (!r.ok) {
        const err = await r.json().catch(() => ({}))
        throw new Error(err.detail || 'Gagal memproses pengepakan')
    }
    return r.json()
}

export function usePackaging(emit) {
    const form = reactive({
        tanggal: new Date().toISOString().split('T')[0],
        referensi: '',
        entitas_id: '',
        grup_bahan_id: '', // Diambil dari Entitas
        kemasan_id: '',
        tangki_pool_id: '',
        jumlah: '', // Pcs
        qty_curah_aktual: '' // Opsional (jika ada susut selang)
    })

    const opsi = reactive({ kemasan: [], tangki: [], entitas: [] })
    const memuat = reactive({ awal: false, rencana: false, kirim: false })
    const pratinjau = ref(null) // Menyimpan hasil dari rencana_kemasan
    const galat = ref(null)

    // --- Muat Data Awal ---
    async function muatDataAwal() {
        memuat.awal = true
        try {
            const [resKemasan, resTangki, resEntitas] = await Promise.all([
                apiGet(API.kemasan, { aktif: 'true' }),
                apiGet(API.tangki, { lapis: 'POOL' }),
                apiGet(API.entitas)
            ])
            opsi.kemasan = resKemasan
            opsi.tangki = resTangki
            opsi.entitas = resEntitas
        } catch (e) {
            galat.value = 'Gagal memuat data master.'
        } finally {
            memuat.awal = false
        }
    }

    // Set otomatis grup_bahan_id jika entitas dipilih
    watch(() => form.entitas_id, (id) => {
        const ent = opsi.entitas.find(e => String(e.id) === String(id))
        form.grup_bahan_id = ent?.grup_bahan_id || ''
        form.tangki_pool_id = '' // Reset tangki karena grup bisa berbeda
    })

    const tangkiSesuaiGrup = computed(() => {
        if (!form.grup_bahan_id) return []
        return opsi.tangki.filter(t => String(t.grup_bahan) === String(form.grup_bahan_id))
    })

    // --- Simulasi Rencana Kemasan ---
    let timerRencana = null
    const cekRencana = () => {
        if (!form.kemasan_id || !form.grup_bahan_id || !form.jumlah) {
            pratinjau.value = null
            return
        }
        if (timerRencana) clearTimeout(timerRencana)
        timerRencana = setTimeout(async () => {
            memuat.rencana = true
            try {
                // Sesuai dengan fungsi rencana_kemasan() di backend
                const data = await apiGet(API.rencana, {
                    kemasan_id: form.kemasan_id,
                    grup_bahan_id: form.grup_bahan_id,
                    jumlah: form.jumlah,
                    tangki_pool_id: form.tangki_pool_id || ''
                })
                // Anggap API mengembalikan array 1 item atau langsung object
                pratinjau.value = Array.isArray(data) ? data[0] : data
                galat.value = null
            } catch (e) {
                pratinjau.value = null
            } finally {
                memuat.rencana = false
            }
        }, 500) // Debounce 500ms
    }

    // Pantau perubahan form untuk menjalankan Kalkulator Pratinjau
    watch([() => form.kemasan_id, () => form.jumlah, () => form.tangki_pool_id], cekRencana)

    // --- Eksekusi ---
    const bisaKirim = computed(() => {
        return form.entitas_id && form.kemasan_id && Number(form.jumlah) > 0 && 
               pratinjau.value?.cukup && !memuat.kirim
    })

    async function kirim() {
        if (!bisaKirim.value) return
        galat.value = null
        memuat.kirim = true
        try {
            // Sesuai parameter fungsi klaim_kemasan()
            const payload = {
                kemasan_id: Number(form.kemasan_id),
                grup_bahan_id: Number(form.grup_bahan_id),
                entitas_id: Number(form.entitas_id),
                jumlah: Number(form.jumlah),
                tanggal: form.tanggal,
                referensi: form.referensi.trim() || `PACK-${Date.now()}`,
                idem_key: `pack:${Date.now()}`,
                tangki_pool_id: form.tangki_pool_id ? Number(form.tangki_pool_id) : null,
                qty_curah_aktual: form.qty_curah_aktual ? Number(form.qty_curah_aktual) : null
            }

            const res = await apiPost(API.klaim, payload)
            emit('tersimpan', res)
            
            // Reset form
            form.jumlah = ''
            form.qty_curah_aktual = ''
            pratinjau.value = null
        } catch (e) {
            galat.value = e.message
        } finally {
            memuat.kirim = false
        }
    }

    return {
        form, opsi, memuat, pratinjau, galat, bisaKirim, tangkiSesuaiGrup,
        muatDataAwal, kirim
    }
}