import { ref } from 'vue'
import api from '@/utils/api'

export function useDashboard() {
    const isLoading = ref(false)
    const pesanError = ref('')

    // State untuk menyimpan data riil dari database
    const kpi = ref({
        prospek_aktif: 0,
        pertumbuhan_prospek: 0, // dalam persentase
        sales_order_bulan_ini: 0, // nominal rupiah
        so_disetujui: 0,
        antrean_pengiriman: 0,
        piutang_jatuh_tempo: 0, // nominal rupiah
        jumlah_invoice_tunggak: 0
    })

    const invoiceKritis = ref([])
    const aktivitasGudang = ref([])

    const muatDataDashboard = async () => {
        isLoading.value = true
        pesanError.value = ''
        try {
            // Endpoint untuk menarik semua rangkuman (Pastikan endpoint ini dibuat di FastAPI Anda)
            const res = await api.get('dashboard/master/')

            // Asumsi backend mengirim JSON dengan struktur: 
            // { kpi: {...}, invoice_kritis: [...], aktivitas_gudang: [...] }
            if (res.data) {
                kpi.value = res.data.kpi || kpi.value
                invoiceKritis.value = res.data.invoice_kritis || []
                aktivitasGudang.value = res.data.aktivitas_gudang || []
            }
        } catch (error) {
            console.error("Gagal memuat dashboard:", error)
            pesanError.value = error.response?.data?.detail || "Gagal terhubung ke server untuk memuat ringkasan data."
        } finally {
            isLoading.value = false
        }
    }

    return {
        isLoading,
        pesanError,
        kpi,
        invoiceKritis,
        aktivitasGudang,
        muatDataDashboard
    }
}