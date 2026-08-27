import { useRoute } from 'vue-router'

/**
 * Konfigurasi menu sidebar untuk modul Produksi.
 * `ikon` memakai nama kelas PrimeIcons lengkap (mis. 'pi-history'),
 * karena di ProduksiLayout.vue dipakai sebagai :class="['pi', menu.ikon]".
 */
const MENU_PRODUKSI = [
  {
    id: 'batch-buat',
    label: 'Input Baru',
    ikon: 'pi-plus-circle',
    rute: '/produksi/batch/buat',
    activate: true
  },
  {
    id: 'tangki-list',
    label: 'Monitor Tangki',
    ikon: 'pi-database',
    rute: '/produksi/tangki',
    activate: true
  }
]

export function useNavProduksi() {
  const route = useRoute()

  const aktif = (rute) => {
    if (!rute) return false
    if (route.path === rute) return true

    // 'Riwayat Batch' tetap tersorot saat membuka detail/ubah batch
    // (/produksi/batch/12, /produksi/batch/12/edit), tapi tidak boleh
    // ikut menyorot saat sedang di 'Input Baru' (/produksi/batch/buat).
    if (rute === '/produksi/batch') {
      return route.path.startsWith('/produksi/batch/') && route.path !== '/produksi/batch/buat'
    }

    return false
  }

  return {
    menuProduksi: MENU_PRODUKSI,
    aktif
  }
}
