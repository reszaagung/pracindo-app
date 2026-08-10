import { ref, computed, onMounted } from 'vue'
import api from '@/utils/api'

export function useInvoice() {
    const isLoading = ref(false)
    const sedangProses = ref(false)
    const pesanError = ref('')
    const daftarInvoice = ref([])
    const previewNomorInvoice = ref('INV/Otomatis')

    const daftarRekening = ref([
        { id: 1, nama_bank: 'BCA', nomor: '1234567890', atas_nama: 'PT. Pracindo Utama' },
        { id: 2, nama_bank: 'Mandiri', nomor: '0987654321', atas_nama: 'PT. Pracindo Utama' }
    ])


    const fetchInvoices = async () => {
        isLoading.value = true
        try {
            // Hit endpoint Faktur Penjualan
            const response = await api.get('akunting/faktur-jual/')
            let rawData = Array.isArray(response.data) ? response.data
                : (response.data?.results || response.data?.data || [response.data])

            const today = new Date().toISOString().split('T')[0]

            daftarInvoice.value = rawData.map(faktur => {
                let uiStatus = faktur.status
                if ((faktur.status === 'BELUM_BAYAR' || faktur.status === 'SEBAGIAN') && faktur.tanggal_jatuh_tempo < today) {
                    uiStatus = 'JATUH TEMPO'
                }

                return {
                    id: faktur.id,
                    nomor_faktur: faktur.nomor_faktur,
                    referensi_so: faktur.delivery_order_nomor || '-',
                    pelanggan: faktur.pelanggan_nama || '-',
                    tanggal_faktur: faktur.tanggal_faktur,
                    tanggal_jatuh_tempo: faktur.tanggal_jatuh_tempo,
                    total_tagihan: parseFloat(faktur.total_tagihan),
                    sisa_piutang: parseFloat(faktur.sisa_piutang),
                    status_asli: faktur.status,
                    ui_status: uiStatus
                }
            })
        } catch (error) {
            console.error("Gagal mengambil data Faktur Penjualan:", error)
            pesanError.value = "Gagal memuat daftar invoice."
        } finally {
            isLoading.value = false
        }
    }

    const totalOutstanding = computed(() => {
        return daftarInvoice.value.reduce((total, inv) => {
            if (inv.status_asli === 'BELUM_BAYAR' || inv.status_asli === 'SEBAGIAN') {
                return total + inv.sisa_piutang
            }
            return total
        }, 0)
    })


    const simpanInvoice = async (deliveryOrderId, payload) => {
        sedangProses.value = true
        pesanError.value = ''
        try {

            const res = await api.post(`akunting/faktur-jual/dari-do/${deliveryOrderId}/`, payload)

            await fetchInvoices()

            return { success: true, data: res.data }
        } catch (error) {
            pesanError.value = error.response?.data?.detail || "Gagal menerbitkan Faktur Tagihan."
            return { success: false }
        } finally {
            sedangProses.value = false
        }
    }

    onMounted(() => {
        fetchInvoices()
    })

    return {
        isLoading,
        sedangProses,
        pesanError,
        daftarInvoice,
        totalOutstanding,
        previewNomorInvoice,
        daftarRekening,
        fetchInvoices,
        simpanInvoice
    }
}