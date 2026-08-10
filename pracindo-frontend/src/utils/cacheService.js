/**
 * utils/cacheService.js
 * ======================
 * Disesuaikan dari versi lama. Dua perbaikan penting:
 *
 * 1. clearAll() versi lama memakai localStorage.clear() — itu IKUT MENGHAPUS
 *    TOKEN, jadi membersihkan cache membuat user ter-logout. Sekarang hanya
 *    key ber-prefix cache yang dihapus.
 *
 * 2. Dibatasi untuk DATA MASTER saja (supplier, customer, produk, akun) —
 *    data yang jarang berubah. JANGAN cache stok, PO, sesi produksi, atau
 *    apa pun yang punya konsekuensi: user bisa mengambil keputusan
 *    berdasarkan angka basah 15 menit, dan di ERP itu berbahaya.
 *
 * Kalau ragu, jangan cache. Query ke server itu murah; keputusan salah tidak.
 */

const PREFIX = 'pracindo_cache:'

/** Key yang BOLEH di-cache — daftar putih, bukan bebas. */
export const CACHE_KEY = {
  AKUN: 'akun',
  SUPLIER: 'suplier',
  CUSTOMER: 'customer',
  PRODUK: 'produk',
  BAHAN: 'bahan',
  TOKO_RETAIL: 'toko_retail',
  STAFF: 'staff',
}

export const CacheService = {
  /**
   * @param {string} key   pakai CACHE_KEY.*
   * @param {any} data
   * @param {number} ttlMenit  default 15
   */
  set(key, data, ttlMenit = 15) {
    try {
      localStorage.setItem(PREFIX + key, JSON.stringify({
        data,
        expiry: Date.now() + ttlMenit * 60_000,
      }))
    } catch {
      // Kuota penuh / mode privat — cache itu opsional, jangan sampai
      // menggagalkan alur utama.
    }
  },

  get(key) {
    try {
      const isi = localStorage.getItem(PREFIX + key)
      if (!isi) return null

      const item = JSON.parse(isi)
      if (Date.now() > item.expiry) {
        localStorage.removeItem(PREFIX + key)
        return null
      }
      return item.data
    } catch {
      return null
    }
  },

  remove(key) {
    localStorage.removeItem(PREFIX + key)
  },

  /** Hanya key cache — token & access card TIDAK ikut terhapus. */
  clearAll() {
    Object.keys(localStorage)
      .filter(k => k.startsWith(PREFIX))
      .forEach(k => localStorage.removeItem(k))
  },
}

/**
 * Helper: ambil dari cache, kalau kosong panggil fetcher lalu simpan.
 *
 *   const akun = await denganCache(CACHE_KEY.AKUN, () =>
 *     api.get('akunting/akun/').then(r => r.data.results || r.data)
 *   )
 */
export const denganCache = async (key, fetcher, ttlMenit = 15) => {
  const tersimpan = CacheService.get(key)
  if (tersimpan) return tersimpan

  const segar = await fetcher()
  CacheService.set(key, segar, ttlMenit)
  return segar
}