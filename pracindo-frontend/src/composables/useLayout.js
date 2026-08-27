/**
 * composables/useLayout.js
 * =========================
 * State sidebar & deteksi mobile, dibagi ke seluruh komponen (module-level
 * ref, bukan dibuat ulang tiap useLayout() dipanggil).
 *
 * TITIK_PUTUS diimpor dari constants/layout.js (bukan didefinisikan di
 * sini) supaya SATU angka ini jadi satu-satunya sumber kebenaran untuk
 * breakpoint mobile di seluruh app. Project ini tidak memakai Tailwind,
 * jadi tidak ada config build terpisah yang perlu disinkronkan -- yang
 * perlu dijaga adalah jangan ada @media di CSS manapun yang mendefinisikan
 * ulang angka breakpoint sendiri (lihat ModulLayout.vue, yang dulu punya
 * @media (max-width: 900px) terpisah dari TITIK_PUTUS = 1024, sehingga
 * ada rentang 900-1024px di mana JS dan CSS saling bertentangan). Kalau
 * sebuah tampilan perlu berubah di breakpoint ini, kondisikan lewat class
 * binding dari isMobile di bawah, bukan lewat @media baru.
 */

import { ref } from 'vue'
import { TITIK_PUTUS } from '@/constants/layout'

export { TITIK_PUTUS }

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
