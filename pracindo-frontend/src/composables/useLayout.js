/**
 * composables/useLayout.js
 * =========================
 * Versi lama sudah bagus — `ref` di luar fungsi (state dibagi semua
 * komponen), listener resize benar. Tiga penyesuaian kecil:
 *
 * 1. removeEventListener saat modul di-dispose (HMR): tanpa ini, setiap
 *    hot-reload menambah listener baru yang tidak pernah dilepas.
 * 2. Debounce resize — resize event menembak puluhan kali per detik.
 * 3. Titik putus dijadikan konstanta yang diekspor, supaya CSS media query
 *    dan JS tidak berbeda diam-diam.
 */

import { ref } from 'vue'

export const TITIK_PUTUS = 1024

const sidebarAktif = ref(false)
const isMobile = ref(false)

const perbarui = () => {
  const mobileSebelumnya = isMobile.value
  isMobile.value = window.innerWidth < TITIK_PUTUS

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