import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/utils/api'

// ==========================================
// KONFIGURASI INDEXED-DB
// ==========================================
const DB_NAME = 'PracindoCourierDB'
const DB_VERSION = 1
const STORE_NAME = 'sync_queue'

// Helper untuk membuka koneksi IndexedDB
const openDB = () => {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION)
        request.onupgradeneeded = (e) => {
            const db = e.target.result
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                db.createObjectStore(STORE_NAME, { keyPath: 'id' })
            }
        }
        request.onsuccess = () => resolve(request.result)
        request.onerror = () => reject(request.error)
    })
}

export function useCourierSync() {
    const isOnline = ref(navigator.onLine)
    const isSyncing = ref(false)
    const antreanKosong = ref(true)

    // ==========================================
    // LOGIKA INDEXED-DB
    // ==========================================
    const simpanKeAntrean = async (tugas) => {
        const db = await openDB()
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readwrite')
            const store = tx.objectStore(STORE_NAME)
            store.add(tugas)
            tx.oncomplete = () => {
                antreanKosong.value = false
                resolve()
            }
            tx.onerror = () => reject(tx.error)
        })
    }

    const ambilSemuaAntrean = async () => {
        const db = await openDB()
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readonly')
            const store = tx.objectStore(STORE_NAME)
            const request = store.getAll()
            request.onsuccess = () => resolve(request.result)
            request.onerror = () => reject(request.error)
        })
    }

    const hapusDariAntrean = async (id) => {
        const db = await openDB()
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readwrite')
            const store = tx.objectStore(STORE_NAME)
            store.delete(id)
            tx.oncomplete = async () => {
                // Cek apakah masih ada sisa antrean
                const sisa = await ambilSemuaAntrean()
                antreanKosong.value = sisa.length === 0
                resolve()
            }
            tx.onerror = () => reject(tx.error)
        })
    }

    // ==========================================
    // FUNGSI SINKRONISASI
    // ==========================================
    const jalankanSinkronisasi = async () => {
        if (!isOnline.value || isSyncing.value) return

        const antrean = await ambilSemuaAntrean()
        if (antrean.length === 0) {
            antreanKosong.value = true
            return
        }

        isSyncing.value = true

        for (const tugas of antrean) {
            try {
                // Siapkan FormData untuk foto
                const formData = new FormData()
                if (tugas.payload.foto) formData.append('foto', tugas.payload.foto)
                if (tugas.payload.catatan) formData.append('catatan', tugas.payload.catatan)
                if (tugas.payload.alasan) formData.append('alasan', tugas.payload.alasan)
                if (tugas.payload.lat) formData.append('lat', tugas.payload.lat)
                if (tugas.payload.lng) formData.append('lng', tugas.payload.lng)

                // Kirim ke Backend dengan Header Idempotency-Key
                await api.post(tugas.url, formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                        'Idempotency-Key': tugas.idem_key // Mencegah duplikasi data di backend
                    }
                })

                // Jika berhasil diterima server, hapus dari IndexedDB (Lokal)
                await hapusDariAntrean(tugas.id)
            } catch (error) {
                console.error(`Gagal sinkronisasi tugas ${tugas.id}:`, error)
                // Jika error 400 (Bad Request), berarti data ditolak permanen, hapus agar tidak menyumbat antrean
                if (error.response && error.response.status === 400) {
                    await hapusDariAntrean(tugas.id)
                }
                // Jika error 5xx atau timeout, biarkan di antrean untuk dicoba lagi nanti
            }
        }

        isSyncing.value = false
    }

    // ==========================================
    // AKSI LAPANGAN KURIR
    // ==========================================

    // Fungsi ini yang akan dipanggil oleh tombol UI
    const kirimBuktiTerima = async (pengirimanId, perhentianId, fotoBlob, catatan = '') => {
        // Buat Idempotency-Key unik (UUID)
        const idemKey = crypto.randomUUID()
        const tugas = {
            id: `bukti_${Date.now()}`,
            jenis: 'BUKTI',
            url: `logistik/pengiriman/${pengirimanId}/perhentian/${perhentianId}/bukti/`,
            idem_key: idemKey,
            payload: { foto: fotoBlob, catatan }
        }

        // 1. Simpan selalu ke antrean lokal dulu (Offline First)
        await simpanKeAntrean(tugas)
        // 2. Langsung coba kirim jika sedang online
        jalankanSinkronisasi()
    }

    const kirimRetur = async (pengirimanId, perhentianId, alasan, fotoBlob = null) => {
        const idemKey = crypto.randomUUID()
        const tugas = {
            id: `retur_${Date.now()}`,
            jenis: 'RETUR',
            url: `logistik/pengiriman/${pengirimanId}/perhentian/${perhentianId}/retur/`,
            idem_key: idemKey,
            payload: { foto: fotoBlob, alasan }
        }

        await simpanKeAntrean(tugas)
        jalankanSinkronisasi()
    }

    // ==========================================
    // LISTENER KONEKSI
    // ==========================================
    const updateStatusKoneksi = () => {
        isOnline.value = navigator.onLine
        if (isOnline.value) {
            jalankanSinkronisasi() // Otomatis jalan saat sinyal kembali
        }
    }

    onMounted(() => {
        window.addEventListener('online', updateStatusKoneksi)
        window.addEventListener('offline', updateStatusKoneksi)

        // Cek antrean saat pertama kali aplikasi dibuka
        ambilSemuaAntrean().then(data => {
            antreanKosong.value = data.length === 0
            if (!antreanKosong.value && isOnline.value) jalankanSinkronisasi()
        })
    })

    onUnmounted(() => {
        window.removeEventListener('online', updateStatusKoneksi)
        window.removeEventListener('offline', updateStatusKoneksi)
    })

    return {
        isOnline,
        isSyncing,
        antreanKosong,
        kirimBuktiTerima,
        kirimRetur,
        jalankanSinkronisasi
    }
}