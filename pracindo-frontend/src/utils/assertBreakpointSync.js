/**
 * assertBreakpointSync.js
 * ========================
 * Pengaman DEV-ONLY: mendeteksi kalau TITIK_PUTUS (constants/layout.js,
 * dipakai composables/useLayout.js) diam-diam berbeda dari breakpoint
 * `lg:` yang sungguhan dipakai Tailwind.
 *
 * KENAPA BUKAN IMPOR LANGSUNG
 * Project ini tidak punya tailwind.config.js -- berarti breakpoint
 * ditentukan lewat default bawaan Tailwind, atau lewat @theme di CSS
 * utama (Tailwind v4, CSS-first). CSS tidak bisa mengimpor konstanta
 * JS, jadi kesesuaiannya diverifikasi di runtime saat browser sudah
 * merender CSS yang sebenarnya -- bukan ditebak saat build.
 *
 * CARA KERJA
 * 1. Coba baca custom property --breakpoint-lg dari :root (Tailwind v4
 *    menulisnya kalau variant `lg:` dipakai di suatu tempat pada bundle).
 * 2. Kalau tidak ditemukan, anggap tidak ada override -> pakai default
 *    bawaan Tailwind (1024px, sama di v3 maupun v4) sebagai acuan.
 */

import { TITIK_PUTUS } from '@/constants/layout'

const DEFAULT_TAILWIND_LG_PX = 1024 // default bawaan Tailwind untuk `lg:`, v3 maupun v4

export function assertBreakpointSync() {
  if (!import.meta.env.DEV) return // jangan bebani production

  const rootStyle = getComputedStyle(document.documentElement)
  const raw = rootStyle.getPropertyValue('--breakpoint-lg').trim()

  let breakpointCssPx = null
  if (raw) {
    const rootFontSizePx = parseFloat(rootStyle.fontSize) || 16
    breakpointCssPx = raw.endsWith('rem')
      ? parseFloat(raw) * rootFontSizePx
      : parseFloat(raw)
  }

  const acuan = breakpointCssPx ?? DEFAULT_TAILWIND_LG_PX
  const sumber = breakpointCssPx
    ? `--breakpoint-lg dari CSS (${raw})`
    : 'default bawaan Tailwind (tidak ada override terdeteksi)'

  if (Math.abs(acuan - TITIK_PUTUS) > 0.5) {
    console.warn(
      `[useLayout] TITIK_PUTUS (${TITIK_PUTUS}px) di constants/layout.js ` +
      `berbeda dari breakpoint 'lg' Tailwind (${acuan}px, sumber: ${sumber}). ` +
      `Sidebar auto-toggle dan class 'lg:' akan aktif di lebar layar yang ` +
      `BERBEDA. Samakan salah satunya.`
    )
  }
}
