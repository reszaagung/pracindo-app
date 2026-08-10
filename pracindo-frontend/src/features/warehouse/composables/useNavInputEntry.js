// src/features/warehouse/composables/useNavInputEntry.js
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

// Letakkan state di luar fungsi agar bersifat global (shared state) antar komponen
const judulHeader = ref('Input Entry')
const breadcrumb = ref('')

export function useNavInputEntry() {
    const route = useRoute()
    const menus = [
        {
            id: 'goods-receipt',
            label: 'Penerimaan',
            ikon: 'pi-box',
            rute: '/warehouse/input/receipt',
            activate: true
        },
        {
            id: 'discrepancy',
            label: 'Selisih / Retur',
            ikon: 'pi-exclamation-triangle',
            rute: '/warehouse/input/discrepancy',
            activate: true
        },
        {
            id: 'quality-control',
            label: 'Inspeksi QC',
            ikon: 'pi-check-square',
            rute: '/warehouse/input/qc',
            activate: false
        }
    ]

    const aktif = (path) => {
        return computed(() => route.path.startsWith(path)).value
    }

    // Fungsi untuk mengubah teks header dari dalam komponen form/detail
    const setNavInfo = (judulBaru, breadcrumbBaru = '') => {
        judulHeader.value = judulBaru
        breadcrumb.value = breadcrumbBaru
    }

    // Fungsi untuk mengembalikan judul ke semula saat keluar dari form
    const resetNav = () => {
        judulHeader.value = 'Input Entry'
        breadcrumb.value = ''
    }

    return {
        menus,
        aktif,
        judulHeader,
        breadcrumb,
        setNavInfo,
        resetNav
    }
}