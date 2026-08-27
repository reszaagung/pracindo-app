/**
 * composables/useLayout.js
 * =========================
 * State sidebar & deteksi mobile, dibagi ke seluruh komponen (module-level
 * ref, bukan dibuat ulang tiap useLayout() dipanggil).
 *
 * TITIK_PUTUS diimpor dari constants/layout.js (bukan didefinisikan di
 * sini) supaya tailwind.config.js bisa mengimpor angka yang SAMA persis
 * untuk breakpoint CSS -- lihat contoh sinkronisasinya di bawah file ini.
 */

import { ref } from 'vue'
import { TITIK_PUTUS } from '@/constants/layout'

export { TITIK_PUTUS }

const sidebarAktif = ref(false)
const isMobile = ref(false)

const perbarui = () => {
  const mobileSebelumnya = isMobile.value
  isMobile.value = window.innerWidth < TITIK_PUTUS

  // Sengaja menimpa pilihan manual user saat melewati breakpoint --
  // ini keputusan UX default (buka otomatis di desktop, tutup otomatis
  // di mobile), bukan bug. Kalau nanti perlu menghormati pilihan manual
  // user lintas-breakpoint, tambahkan flag `dipilihManual` terpisah di
  // sini -- jangan diam-diam diubah tanpa keputusan eksplisit.
  if (mobileSebelumnya && !isMobile.value) {
    sidebarAktif.value = true
  }
  if (!mobileSebelumnya && isMobile.value) {
    sidebarAktif.value = false
  }
}

if (typeof window !== 'undefined') {
  isMobile.value = window.innerWidth < TITIK_PUTUS
  sidebarAktif.value = !isMobile.value

  let timer = null
  const onResize = () => {
    clearTimeout(timer)
    timer = setTimeout(perbarui, 120)
  }
  window.addEventListener('resize', onResize)

  if (import.meta.hot) {
    import.meta.hot.dispose(() => {
      clearTimeout(timer)
      window.removeEventListener('resize', onResize)
    })
  }
}

export function useLayout() {
  const toggleSidebar = () => {
    sidebarAktif.value = !sidebarAktif.value
  }

  const tutupDiMobile = () => {
    if (isMobile.value) sidebarAktif.value = false
  }

  return {
    sidebarAktif,
    isMobile,
    toggleSidebar,
    tutupDiMobile,
    isSidebarActive: sidebarAktif,
    closeSidebarOnMobile: tutupDiMobile,
  }
}
