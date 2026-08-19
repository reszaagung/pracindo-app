import { computed } from 'vue'
import { useRoute } from 'vue-router'

export function useNavProduksi() {
    const route = useRoute()

    const produksi = computed(() => [
        {
            id: 'batch',
            label: 'Riwayat Batch',
            rute: '/produksi/batch',
            ikon: 'pi-list',
            activate: true
        },
        {
            id: 'tangki',
            label: 'Monitor Tangki',
            rute: '/produksi/tangki',
            ikon: 'pi-database',
            activate: true
        }
    ])

    const aktif = (path) => route.path.startsWith(path)

    return { produksi, aktif }
}
