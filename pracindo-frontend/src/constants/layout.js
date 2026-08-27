/**
 * constants/layout.js
 * ====================
 * Konstanta MURNI, tanpa dependensi Vue atau `window`.
 *
 * Kenapa dipisah dari useLayout.js: composable itu memanggil `ref()` dan
 * menyentuh `window` di level modul, jadi tidak aman diimpor oleh file
 * yang jalan di Node (tailwind.config.js, vite.config.js, dll). File ini
 * aman diimpor di MANA SAJA -- browser maupun build-time Node -- sehingga
 * satu angka ini benar-benar jadi satu-satunya sumber kebenaran untuk
 * breakpoint sidebar, baik di JS maupun di konfigurasi Tailwind.
 */

export const TITIK_PUTUS = 1024
