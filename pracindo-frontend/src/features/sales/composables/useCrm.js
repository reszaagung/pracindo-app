// src/features/sales/composables/useCrm.js
import { ref } from 'vue'
import api from '@/utils/api'

export function useCrm() {
    const isLoading = ref(false)
    const leads = ref([])
    const prospects = ref([])
    const won = ref([])

    const fetchCrmData = async () => {
        isLoading.value = true
        try {
            // Gunakan API nyata saat backend sudah siap:
            // const response = await api.get('crm/leads/')
            // const allData = response.data.results || response.data

            // MOCKUP SEMENTARA (Agar bisa dites perpindahan kolomnya)
            const allData = [
                { id: 1, nama: 'Budi Santoso', perusahaan: 'CV. Bangun Abadi', telepon: '0812-3456-7890', estimasi_nilai: 15000000, status: 'LEADS', tanggal: 'Hari ini' },
                { id: 2, nama: 'Anita Wijaya', perusahaan: 'Toko Besi Makmur', telepon: '0857-1122-3344', estimasi_nilai: 8500000, status: 'LEADS', tanggal: 'Kemarin' },
                { id: 3, nama: 'Hendra Gunawan', perusahaan: 'PT. Konstruksi Jaya', telepon: '0811-9988-7766', estimasi_nilai: 45000000, status: 'PROSPECT', tanggal: '3 hari lalu' },
                { id: 4, nama: 'Diana Putri', perusahaan: 'Sentral Logistik', telepon: '0878-5555-4444', estimasi_nilai: 125000000, status: 'WON', tanggal: '1 Mgg lalu' },
            ]

            // Pisahkan data ke masing-masing kolom berdasarkan status
            leads.value = allData.filter(item => item.status === 'LEADS')
            prospects.value = allData.filter(item => item.status === 'PROSPECT')
            won.value = allData.filter(item => item.status === 'WON')

        } catch (error) {
            console.error("Gagal memuat data CRM:", error)
        } finally {
            isLoading.value = false
        }
    }

    const updateLeadStatus = async (id, newStatus) => {
        try {
            // API Call ke backend FastAPI untuk update status di database
            // await api.patch(`crm/leads/${id}/status/`, { status: newStatus })

            // Logika Frontend: Pindahkan kartu secara reaktif
            let itemToMove = null

            const findAndRemove = (array) => {
                const index = array.findIndex(item => item.id === id)
                if (index !== -1) {
                    itemToMove = array[index]
                    array.splice(index, 1)
                }
            }

            findAndRemove(leads.value)
            if (!itemToMove) findAndRemove(prospects.value)
            if (!itemToMove) findAndRemove(won.value)

            if (itemToMove) {
                itemToMove.status = newStatus
                if (newStatus === 'LEADS') leads.value.push(itemToMove)
                if (newStatus === 'PROSPECT') prospects.value.push(itemToMove)
                if (newStatus === 'WON') won.value.push(itemToMove)
            }

            return { success: true }
        } catch (error) {
            console.error("Gagal mengubah status:", error)
            return { success: false, message: "Gagal memindahkan prospek." }
        }
    }

    return {
        isLoading,
        leads,
        prospects,
        won,
        fetchCrmData,
        updateLeadStatus
    }
}