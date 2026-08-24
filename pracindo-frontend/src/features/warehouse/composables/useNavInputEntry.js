// src/features/warehouse/composables/useNavInputEntry.js
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
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
            id: 'packing',
            label: 'Input Packing',
            ikon: 'pi-box',
            rute: '/warehouse/input/packing',
            activate: true
        },
        {
            id: 'log-packaging',
            label: 'Riwayat Packing',
            ikon: 'pi-history',
            rute: '/warehouse/input/packaging/log',
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

    const setNavInfo = (judulBaru, breadcrumbBaru = '') => {
        judulHeader.value = judulBaru
        breadcrumb.value = breadcrumbBaru
    }
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
