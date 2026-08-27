// src/features/warehouse/composables/useReceiptIndex.js
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNavInputEntry } from './useNavInputEntry'

export function useReceiptIndex() {
    const route = useRoute()
    const router = useRouter()
    const { setNavInfo, resetNav } = useNavInputEntry()

    // Membaca tab aktif dari URL, default ke 'bahan_baku' jika kosong
    const tabAktif = ref(route.query.tab === 'kemasan' ? 'kemasan' : 'bahan_baku')

    const ubahTab = (tabBaru) => {
        tabAktif.value = tabBaru
        router.replace({ query: { ...route.query, tab: tabBaru } })
    }

    onMounted(() => {
        setNavInfo('Penerimaan Barang', 'Warehouse > Penerimaan > Index')
    })
    onUnmounted(() => {
        resetNav()
    })

    return {
        tabAktif,
        ubahTab
    }
}
