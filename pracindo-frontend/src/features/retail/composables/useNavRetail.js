import { useRoute, useRouter } from 'vue-router'
import { useLayout } from '@/composables/useLayout'

export function useNavRetailLayout() {
    const route = useRoute()
    const router = useRouter()

    // Ambil fungsi tutup menu mobile dari useLayout utama
    const { tutupDiMobile } = useLayout()

    const menuRetail = [
        {
            id: 'pos',
            label: 'Mesin Kasir (POS)',
            rute: '/retail/pos',
            ikon: 'pi-desktop',
            activate: true
        },
        {
            id: 'piutang',
            label: 'Buku Piutang',
            rute: '/retail/piutang',
            ikon: 'pi-credit-card',
            activate: true
        },
        {
            id: 'penerimaan',
            label: 'Penerimaan Stok',
            rute: '/retail/penerimaan',
            ikon: 'pi-box',
            activate: true
        }
    ]

    const aktif = (path) => route.path.startsWith(path)

    const kembali = () => router.push('/')

    const klikMenu = (menu) => {
        if (!menu.activate) return
        router.push(menu.rute)
        tutupDiMobile()
    }

    return {
        menuRetail,
        aktif,
        kembali,
        klikMenu
    }
}
