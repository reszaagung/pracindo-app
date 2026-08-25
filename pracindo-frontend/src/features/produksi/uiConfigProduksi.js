// ============================================================
// Konstanta & helper bersama untuk modul Produksi
// (dipakai BatchList.vue, BatchDetail.vue, dan komponen lain
// di bawah folder produksi supaya tidak duplikat)
// ============================================================

// ---- Kolom tabel Riwayat Batch ----
export const BATCH_TABLE_COLUMNS = [
  { key: 'batch', label: 'Batch', align: 'left' },
  { key: 'waktu', label: 'Tanggal', align: 'left' },
  { key: 'jenis', label: 'Jenis', align: 'left' },
  { key: 'tangki_tujuan_nama', label: 'Tangki Tujuan', align: 'left' },
  { key: 'nama_hasil', label: 'Nama Hasil', align: 'left' },
  { key: 'qty_hasil', label: 'Yield (Kg)', align: 'right' },
  { key: 'harga_per_kg', label: 'Harga Rata', align: 'right' },
  { key: 'status', label: 'Status', align: 'center' },
  { key: 'aksi', label: '', align: 'center' }
]

// ---- Opsi filter (dropdown) ----
export const JENIS_BATCH_OPTIONS = [
  { value: '', label: 'Semua Jenis' },
  { value: 'MIXING', label: 'Mixing' },
  { value: 'BLENDING', label: 'Blending' }
]

export const STATUS_BATCH_OPTIONS = [
  { value: '', label: 'Semua Status' },
  { value: 'DRAFT', label: 'Draft' },
  { value: 'POSTED', label: 'Posted' },
  { value: 'VOID', label: 'Void' }
]

// ---- Label tampilan ----
export const JENIS_BATCH_LABELS = {
  MIXING: 'Mixing',
  BLENDING: 'Blending'
}

export const STATUS_BATCH_LABELS = {
  DRAFT: 'Draft',
  POSTED: 'Posted',
  VOID: 'Void'
}

// ---- Warna badge status (samakan dengan BatchDetail.vue) ----
export function getStatusBadgeClass(status) {
  switch (status) {
    case 'POSTED':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200'
    case 'VOID':
      return 'bg-red-50 text-red-700 border-red-200'
    case 'DRAFT':
    default:
      return 'bg-amber-50 text-amber-700 border-amber-200'
  }
}

// ---- Formatter bersama (opsional — belum dipakai komponen existing,
// tinggal ganti import kalau nanti mau hapus duplikasi formatKg/
// formatRupiah/formatTanggal lokal di BatchList/BatchDetail/InputProduksi) ----
export function formatKg(v) {
  return Number(v || 0).toLocaleString('id-ID', { minimumFractionDigits: 3, maximumFractionDigits: 3 })
}

export function formatRupiah(v) {
  return `Rp ${Number(v || 0).toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export function formatTanggal(v) {
  if (!v) return '-'
  const d = new Date(v)
  if (isNaN(d)) return v
  return (
    d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) +
    ' ' +
    d.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
  )
}
