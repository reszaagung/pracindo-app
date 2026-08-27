// Dipakai composable (JS) DAN jadi referensi angka yang harus dipakai
// KONSISTEN di semua @container CSS manual di seluruh app. Ubah di sini,
// lalu cari-ganti manual di CSS -- @container belum bisa baca CSS
// custom property di dalam kondisinya, jadi tidak bisa disambungkan
// otomatis ke sini.
export const CONTAINER_BREAKPOINTS = {
  xs: 0,
  sm: 400,
  md: 560,   // dipakai modal PO kemarin
  lg: 720,
  xl: 960,
}
