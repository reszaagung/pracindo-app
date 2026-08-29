/**
 * utils/cacheService.js
 * ======================
 * Disesuaikan dari versi lama. Perbaikan & penambahan:
 *
 * 1. clearAll() versi lama memakai localStorage.clear() — itu IKUT MENGHAPUS
 *    TOKEN, jadi membersihkan cache membuat user ter-logout. Sekarang hanya
 *    key ber-prefix cache yang dihapus (dan dibungkus try/catch juga).
 *
 * 2. BUG di versi sebelumnya: remove(key) memanggil localStorage.removeItem(key)
 *    TANPA prefix, padahal set()/get() selalu pakai PREFIX + key. Akibatnya
 *    remove() tidak pernah benar-benar menghapus apa pun — entry lama diam-
 *    diam tetap tersimpan sampai TTL habis atau clearAll(). Sudah diperbaiki.
 *
 * 3. Dibatasi untuk DATA MASTER saja (supplier, customer, produk, akun) —
 *    data yang jarang berubah. JANGAN cache stok, PO, sesi produksi, atau
 *    apa pun yang punya konsekuensi: user bisa mengambil keputusan
 *    berdasarkan angka basah 15 menit, dan di ERP itu berbahaya. Whitelist
 *    ini sekarang ditegakkan saat runtime di set() — key di luar CACHE_KEY
 *    ditolak (dengan warning di console saat dev), bukan sekadar aturan di
 *    komentar.
 *
 * 4. Layer memori (Map) di depan localStorage. localStorage.getItem() +
 *    JSON.parse() itu tidak gratis — kalau beberapa komponen di halaman
 *    yang sama-sama butuh, misalnya, daftar produk, versi lama akan
 *    parse ulang string JSON yang sama tiap kali. Sekarang baca pertama
 *    yang mengisi memori; baca berikutnya untuk key yang sama tinggal
 *    ambil dari Map. localStorage tetap sumber kebenaran yang bertahan
 *    lintas reload/tab.
 *
 * 5. Sinkron antar-tab lewat event 'storage'. Tanpa ini, tab yang sudah
 *    lama terbuka bisa terus menyajikan data lama dari memori meski tab
 *    lain sudah clearAll() (mis. logout) atau menimpa entry yang sama.
 *
 * 6. denganCache() sekarang men-dedup permintaan yang sedang berjalan.
 *    Kalau tiga komponen mount bersamaan dan sama-sama minta
 *    CACHE_KEY.PRODUK saat cache masih kosong, versi lama memicu tiga
 *    request paralel ke endpoint yang sama. Sekarang hanya permintaan
 *    pertama yang benar-benar jalan; sisanya menunggu promise yang sama.
 *
 * Kalau ragu, jangan cache. Query ke server itu murah; keputusan salah tidak.
 */

const PREFIX = 'pracindo_cache:'
const DEFAULT_TTL_MENIT = 15

/** Key yang BOLEH di-cache — daftar putih, bukan bebas, ditegakkan di set(). */
export const CACHE_KEY = {
  AKUN: 'akun',
  SUPLIER: 'suplier',
  CUSTOMER: 'customer',
  PRODUK: 'produk',
  BAHAN: 'bahan',
  TOKO_RETAIL: 'toko_retail',
  STAFF: 'staff',
}

/** @typedef {typeof CACHE_KEY[keyof typeof CACHE_KEY]} CacheKey */

const VALID_KEYS = new Set(Object.values(CACHE_KEY))
const isDev = Boolean(import.meta.env?.DEV)

/** Layer 1: cache in-memory. Key TANPA prefix -> { data, expiry }. */
const memori = new Map()

/** Dedup fetch yang sedang berjalan, dipakai denganCache(). Key TANPA prefix -> Promise. */
const sedangBerjalan = new Map()

function isBrowser() {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

function peringatanKeyTidakValid(key) {
  if (!isDev) return
  console.warn(
    `[CacheService] "${key}" bukan bagian dari CACHE_KEY. Hanya data master ` +
    `yang boleh di-cache (lihat komentar di atas file ini) — set() untuk ` +
    `key ini diabaikan, tidak disimpan.`
  )
}

/** Baca satu entry mentah dari localStorage. undefined kalau tidak ada / rusak. */
function bacaDariStorage(key) {
  try {
    const isi = localStorage.getItem(PREFIX + key)
    if (!isi) return undefined

    const item = JSON.parse(isi)
    if (!item || typeof item.expiry !== 'number') return undefined

    return item
  } catch {
    return undefined
  }
}

/**
 * Inti baca + cek kedaluwarsa, dipakai get() & has() supaya logikanya cuma
 * ada di satu tempat. Urutan: memori dulu (murah), baru localStorage
 * (sumber kebenaran kalau memori masih kosong, misalnya tab baru dibuka).
 */
function baca(key) {
  let item = memori.get(key)

  if (item === undefined) {
    item = bacaDariStorage(key)
    if (item !== undefined) memori.set(key, item)
  }

  if (item === undefined) return undefined

  if (Date.now() > item.expiry) {
    hapusInternal(key)
    return undefined
  }

  return item
}

function hapusInternal(key) {
  memori.delete(key)
  try {
    localStorage.removeItem(PREFIX + key)
  } catch {
    // no-op — lihat alasan try/catch di set()
  }
}

// Selaraskan memori tab ini kalau tab LAIN mengubah localStorage. Event
// 'storage' cuma nyala di tab lain, bukan di tab yang bikin perubahan —
// makanya set() / hapusInternal() di bawah update memori tab sendiri
// secara langsung, tidak menunggu event ini.
if (isBrowser()) {
  window.addEventListener('storage', event => {
    if (!event.key || !event.key.startsWith(PREFIX)) return
    const key = event.key.slice(PREFIX.length)

    if (event.newValue === null) {
      memori.delete(key)
      return
    }
    try {
      memori.set(key, JSON.parse(event.newValue))
    } catch {
      memori.delete(key)
    }
  })
}

export const CacheService = {
  /**
   * @param {CacheKey} key   pakai CACHE_KEY.*
   * @param {any} data
   * @param {number} ttlMenit  default 15
   */
  set(key, data, ttlMenit = DEFAULT_TTL_MENIT) {
    if (!VALID_KEYS.has(key)) {
      peringatanKeyTidakValid(key)
      return
    }

    const item = { data, expiry: Date.now() + ttlMenit * 60_000 }
    memori.set(key, item)

    try {
      localStorage.setItem(PREFIX + key, JSON.stringify(item))
    } catch {
      // Kuota penuh / mode privat — cache itu opsional, jangan sampai
      // menggagalkan alur utama. Data tetap ada di memori untuk sesi ini.
    }
  },

  /** @param {CacheKey} key @returns {any|null} null kalau kosong/kedaluwarsa. */
  get(key) {
    const item = baca(key)
    return item === undefined ? null : item.data
  },

  /** @param {CacheKey} key @returns {boolean} true kalau ada entry yang masih berlaku. */
  has(key) {
    return baca(key) !== undefined
  },

  /** @param {CacheKey} key */
  remove(key) {
    hapusInternal(key)
  },

  /** Hanya key cache — token & access card TIDAK ikut terhapus. */
  clearAll() {
    memori.clear()
    try {
      Object.keys(localStorage)
        .filter(k => k.startsWith(PREFIX))
        .forEach(k => localStorage.removeItem(k))
    } catch {
      // no-op
    }
  },

  /**
   * Ringkasan isi cache saat ini, untuk debug manual di console:
   * `console.table(CacheService.debug())`. Bukan untuk dipakai di alur
   * aplikasi normal.
   */
  debug() {
    if (!isBrowser()) return []
    const sekarang = Date.now()

    try {
      return Object.keys(localStorage)
        .filter(k => k.startsWith(PREFIX))
        .map(k => {
          const key = k.slice(PREFIX.length)
          const mentah = localStorage.getItem(k) || ''
          let expiry = null
          try {
            expiry = JSON.parse(mentah).expiry
          } catch {
            // data korup — tetap dilaporkan, expiry null menandakannya
          }
          return {
            key,
            expired: typeof expiry === 'number' ? sekarang > expiry : null,
            expiresInSec: typeof expiry === 'number' ? Math.round((expiry - sekarang) / 1000) : null,
            sizeKB: (mentah.length / 1024).toFixed(2),
            inMemory: memori.has(key),
          }
        })
    } catch {
      return []
    }
  },
}

/**
 * Helper: ambil dari cache, kalau kosong panggil fetcher lalu simpan.
 * Kalau ada beberapa pemanggil bersamaan untuk key yang sama saat cache
 * kosong, cuma satu fetcher yang benar-benar jalan (single-flight) —
 * sisanya menunggu hasil yang sama, jadi tidak ada request duplikat.
 *
 *   const akun = await denganCache(CACHE_KEY.AKUN, () =>
 *     api.get('akunting/akun/').then(r => r.data.results || r.data)
 *   )
 */
export const denganCache = async (key, fetcher, ttlMenit = DEFAULT_TTL_MENIT) => {
  const tersimpan = CacheService.get(key)
  if (tersimpan !== null) return tersimpan

  const sudahJalan = sedangBerjalan.get(key)
  if (sudahJalan) return sudahJalan

  const permintaan = (async () => {
    try {
      const segar = await fetcher()
      CacheService.set(key, segar, ttlMenit)
      return segar
    } finally {
      sedangBerjalan.delete(key)
    }
  })()

  sedangBerjalan.set(key, permintaan)
  return permintaan
}