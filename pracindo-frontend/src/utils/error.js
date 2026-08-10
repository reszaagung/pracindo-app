/**
 * utils/error.js
 * ===============
 * Backend TIDAK PERNAH mengirim field `message`. Composable lama membaca
 * `err.response?.data?.message` — selalu undefined, jadi semua pesan spesifik
 * yang ditulis backend tidak pernah sampai ke user. Yang muncul cuma teks
 * fallback generik.
 *
 * Bentuk error yang benar-benar dikirim backend:
 *
 *   { "detail": "Stok fisik 'Gula' tidak cukup: diminta 31, tersedia 30." }
 *       dari services (ValueError) — pesan paling berguna, biasanya
 *       menjelaskan angka dan apa yang harus dilakukan
 *
 *   { "akun": ["Wajib diisi untuk role selain Supervisor."] }
 *       dari serializer DRF — per field
 *
 *   { "non_field_errors": ["Username/email atau password salah."] }
 *       dari validate() serializer
 */

const LABEL_FIELD = {
  non_field_errors: '',
  detail: '',
  akun: 'Entitas',
  suplier: 'Suplier',
  daftar_item: 'Item',
  nama_item: 'Nama barang',
  quantity: 'Kuantitas',
  total_unit: 'Jumlah unit',
  harga_satuan: 'Harga satuan',
  qty_unit: 'Jumlah unit',
  berat_per_unit: 'Berat per unit',
  staff_ids: 'Staf yang ditag',
  tanggal: 'Tanggal',
  deadline: 'Tenggat',
}

/**
 * @param {Error} err    
 * @param {string} fallback  
 * @returns {string}
 */
export const bacaError = (err, fallback = 'Terjadi kesalahan.') => {
  if (!err?.response) {
    return 'Tidak bisa menghubungi server. Cek koneksi.'
  }

  const { status, data } = err.response

  if (status === 403) return 'Kamu tidak punya akses untuk tindakan ini.'
  if (status === 404) return 'Data tidak ditemukan.'
  if (status >= 500) return 'Server bermasalah. Coba lagi sebentar lagi.'

  if (!data) return fallback
  if (typeof data === 'string') return data

  // Pesan dari service layer — paling spesifik, dahulukan.
  if (data.detail) return data.detail

  if (typeof data === 'object') {
    const pesan = []
    for (const [field, isi] of Object.entries(data)) {
      const teks = Array.isArray(isi) ? isi.join(' ') : String(isi)
      const label = LABEL_FIELD[field] ?? field
      pesan.push(label ? `${label}: ${teks}` : teks)
    }
    if (pesan.length) return pesan.join('\n')
  }

  return fallback
}

/**
 * Untuk form: petakan error DRF ke field, supaya pesan muncul di bawah
 * input yang salah, bukan menumpuk di atas.
 * @returns {Object} { namaField: 'pesan' }
 */
export const errorPerField = (err) => {
  const data = err?.response?.data
  if (!data || typeof data !== 'object' || data.detail) return {}

  const hasil = {}
  for (const [field, isi] of Object.entries(data)) {
    if (field === 'non_field_errors') continue
    hasil[field] = Array.isArray(isi) ? isi.join(' ') : String(isi)
  }
  return hasil
}