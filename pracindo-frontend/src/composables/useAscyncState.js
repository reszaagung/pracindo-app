/**
 * composables/useAsyncState.js
 * ==============================
 * Menangani loading/error/data untuk satu operasi async, dirancang khusus
 * supaya UI tidak "berkedip":
 *
 * 1. DELAY SEBELUM MENAMPILKAN LOADING (default 200ms) — kalau data
 *    datang lebih cepat dari ini (mis. cache hit dari CacheService),
 *    status loading TIDAK PERNAH ditampilkan sama sekali.
 *
 * 2. MINIMUM DURASI TAMPIL (default 400ms) — KALAU loading terlanjur
 *    ditampilkan (request-nya memang lebih lambat dari delay di atas),
 *    ditahan tampil minimal segini lama. Tanpa ini, loading bisa
 *    "flash lalu hilang" kalau response datang tepat setelah delay
 *    terlewati — sama-sama kelihatan sebagai kedipan, cuma di ujung lain.
 *
 * 3. RACE-CONDITION GUARD — kalau run() dipanggil lagi sebelum panggilan
 *    sebelumnya selesai (mis. user ganti filter dengan cepat), respons
 *    yang datang belakangan dari request yang SUDAH USANG tidak akan
 *    menimpa data yang lebih baru.
 *
 * 4. shallowRef untuk `data`/`error` — response API biasanya diganti utuh
 *    (bukan di-mutate field-nya satu per satu), jadi tidak perlu Vue
 *    membungkus tiap properti nested jadi reactive proxy. Untuk list
 *    besar (mis. daftar produk/bahan) ini beda cukup terasa di performa.
 */
import { shallowRef, ref } from 'vue'

export function useAsyncState(options = {}) {
  const {
    delayMs = 200,
    minDurationMs = 400,
  } = options

  const data = shallowRef(null)
  const error = shallowRef(null)
  const loading = ref(false)

  let requestId = 0

  async function run(fetcher) {
    const idSaatIni = ++requestId
    error.value = null

    let sudahSelesai = false
    let waktuTampil = null

    const delayTimer = setTimeout(() => {
      if (!sudahSelesai && idSaatIni === requestId) {
        loading.value = true
        waktuTampil = Date.now()
      }
    }, delayMs)

    try {
      const hasil = await fetcher()
      if (idSaatIni !== requestId) return hasil // sudah usang (kalah cepat), diabaikan
      data.value = hasil
      return hasil
    } catch (err) {
      if (idSaatIni !== requestId) throw err
      error.value = err
      throw err
    } finally {
      sudahSelesai = true
      clearTimeout(delayTimer)

      if (idSaatIni === requestId) {
        if (waktuTampil) {
          const sisaWaktu = minDurationMs - (Date.now() - waktuTampil)
          if (sisaWaktu > 0) await new Promise(r => setTimeout(r, sisaWaktu))
        }
        loading.value = false
      }
    }
  }

  return { data, error, loading, run }
}