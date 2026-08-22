<script setup>
import { ref, onMounted, computed } from 'vue'
import { usePenerimaan } from '../composables/usePenerimaan'
import { useRetail } from '../composables/useRetail' // Mengambil katalog produk
import dayjs from 'dayjs'

const { doList, fetchDO, prosesPenerimaan, isLoading } = usePenerimaan()
const { posProducts, fetchPosProducts } = useRetail()

const isModalOpen = ref(false)
const selectedDO = ref(null)

// Format input persis 8 baris item untuk entri data secara langsung
const formItems = ref(Array.from({ length: 8 }, () => ({
    produk_id: '',
    qty_diterima: ''
})))

onMounted(() => {
    fetchDO()
    fetchPosProducts()
})

const doMenunggu = computed(() => doList.value.filter(d => d.status === 'MENUNGGU').length)
const formatTanggal = (date) => date ? dayjs(date).format('DD MMM YYYY, HH:mm') : '-'

const openModal = (suratJalan) => {
    selectedDO.value = suratJalan
    // Reset form ke 8 baris kosong setiap kali modal dibuka
    formItems.value = Array.from({ length: 8 }, () => ({
        produk_id: '',
        qty_diterima: ''
    }))
    isModalOpen.value = true
}

const closeModal = () => {
    isModalOpen.value = false
    selectedDO.value = null
}

const submitPenerimaan = async () => {
    const res = await prosesPenerimaan(selectedDO.value.id, formItems.value)
    if (res.status === 'sukses') {
        alert('Data penerimaan berhasil dicatat ke sistem!')
        closeModal()
        fetchDO()
    } else {
        alert(`Gagal: ${res.pesan}`)
    }
}
</script>

<template>
    <div class="p-6 max-w-7xl mx-auto space-y-6">
        <header class="flex justify-between items-center border-b border-slate-200 pb-4">
            <div>
                <h1 class="text-2xl font-bold text-slate-800">Penerimaan Stok Factory</h1>
                <p class="text-sm text-slate-500 mt-1">Delivery Order & Logistik Cabang</p>
            </div>
            <span v-if="doMenunggu > 0" class="bg-red-500 text-white px-4 py-1.5 rounded-full text-sm font-semibold shadow animate-pulse">
                {{ doMenunggu }} Menunggu Pengecekan
            </span>
        </header>

        <div class="bg-white rounded-[20px] shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 overflow-hidden">
            <table class="min-w-full divide-y divide-slate-200">
                <thead class="bg-slate-50">
                    <tr>
                        <th class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase">No. Dokumen</th>
                        <th class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase">Asal Pengiriman</th>
                        <th class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase">Waktu Kirim</th>
                        <th class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase">Status</th>
                        <th class="px-6 py-4 text-center text-xs font-bold text-slate-500 uppercase">Aksi</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                    <tr v-if="doList.length === 0" class="bg-white">
                        <td colspan="5" class="px-6 py-8 text-center text-slate-400">Belum ada riwayat dokumen Delivery Order.</td>
                    </tr>
                    <tr v-for="dokumen in doList" :key="dokumen.id" class="hover:bg-slate-50 transition-colors">
                        <td class="px-6 py-4 whitespace-nowrap font-bold text-slate-800">{{ dokumen.nomor_do }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600">{{ dokumen.asal_pengiriman }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600">{{ formatTanggal(dokumen.tanggal_kirim) }}</td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <span :class="dokumen.status === 'SELESAI' ? 'bg-emerald-100 text-emerald-700' : 'bg-orange-100 text-orange-700'"
                                  class="px-3 py-1 text-xs font-bold rounded-md">
                                {{ dokumen.status }}
                            </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-center">
                            <button v-if="dokumen.status === 'MENUNGGU'" @click="openModal(dokumen)"
                                    class="bg-blue-600 text-white px-4 py-2 rounded-lg text-xs font-bold hover:bg-blue-700 transition-colors shadow-sm">
                                INPUT BARANG MASUK
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Modal Pengecekan & Input 8 Item -->
        <div v-if="isModalOpen" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div class="bg-white rounded-2xl shadow-xl w-full max-w-4xl flex flex-col h-[85vh]">
                <div class="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50 shrink-0">
                    <div>
                        <h3 class="font-bold text-lg text-slate-800">Form Entri Barang DO: {{ selectedDO?.nomor_do }}</h3>
                        <p class="text-xs text-slate-500 mt-0.5">Asal: {{ selectedDO?.asal_pengiriman }}</p>
                    </div>
                    <button @click="closeModal" class="text-slate-400 hover:text-red-500 transition-colors"><i class="pi pi-times"></i></button>
                </div>

                <div class="p-6 overflow-y-auto flex-1 custom-scrollbar bg-slate-50/50">
                    <div class="grid grid-cols-12 gap-4 mb-3 px-2">
                        <div class="col-span-1 text-xs font-bold text-slate-500 text-center">No</div>
                        <div class="col-span-8 text-xs font-bold text-slate-500">Nama Produk / Barang</div>
                        <div class="col-span-3 text-xs font-bold text-slate-500 text-right">Qty Masuk</div>
                    </div>

                    <div class="space-y-3">
                        <div v-for="(item, index) in formItems" :key="index" class="grid grid-cols-12 gap-4 items-center bg-white p-2 rounded-lg border border-slate-200">
                            <div class="col-span-1 text-center font-semibold text-slate-400 text-sm">{{ index + 1 }}</div>
                            <div class="col-span-8">
                                <select v-model="item.produk_id" class="w-full border-none outline-none text-sm text-slate-700 bg-transparent cursor-pointer">
                                    <option value="" disabled>-- Pilih produk yang diterima --</option>
                                    <option v-for="p in posProducts" :key="p.id" :value="p.id">
                                        {{ p.nama }}
                                    </option>
                                </select>
                            </div>
                            <div class="col-span-3">
                                <input v-model.number="item.qty_diterima" type="number" min="0" placeholder="0"
                                       class="w-full text-right border-none outline-none text-sm font-bold text-slate-800 bg-transparent">
                            </div>
                        </div>
                    </div>
                </div>

                <div class="p-5 border-t border-slate-100 flex justify-end gap-3 shrink-0 bg-white">
                    <button @click="closeModal" class="px-6 py-2.5 rounded-xl text-sm font-bold text-slate-600 hover:bg-slate-100 transition-colors">Batal</button>
                    <button @click="submitPenerimaan" :disabled="isLoading"
                            class="px-8 py-2.5 rounded-xl text-sm font-bold bg-slate-900 text-white hover:bg-slate-800 transition-colors shadow-md flex items-center">
                        <i v-if="isLoading" class="pi pi-spinner pi-spin mr-2"></i>
                        Simpan Data
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>
