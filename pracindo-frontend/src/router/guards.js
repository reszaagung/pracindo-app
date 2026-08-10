/**
 * router/guards.js
 * =================
 * Proteksi rute berdasarkan Data-Driven UI dari backend.
 */

import { useAuth } from '@/composables/useAuth'
import { rutePertamaSiap } from '@/config/modules'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'


NProgress.configure({
  showSpinner: false,
  speed: 400,
  minimum: 0.15
})

export const useGuards = (router) => {
  router.beforeEach((to, from) => {
    if (to.path !== from.path) {
      NProgress.start()
    }

    const auth = useAuth()

    if (to.meta?.publik) {
      if (auth.masuk.value && (to.name === 'login' || to.name === 'register')) {
        return rutePertamaSiap(auth.modul.value) ?? { name: 'dashboard' }
      }
      return true
    }

    if (!auth.masuk.value) {
      return { name: 'login', query: { next: to.fullPath } }
    }

    if (to.meta?.modul && !auth.bisaAkses(to.meta.modul)) {
      return { name: 'akses-ditolak', query: { modul: to.meta.modul } }
    }

    return true
  })

  router.afterEach(() => {
    NProgress.done()
  })
}