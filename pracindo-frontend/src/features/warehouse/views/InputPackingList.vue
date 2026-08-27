<!-- src/features/warehouse/views/InputPackingList.vue -->
<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <transition name="fade" mode="out-in">
            <!-- STATE 1: FORM INPUT PACKING (LAZY VIEW) -->
            <div v-if="modeForm" key="form" class="w-full">
                <div class="mb-4 flex items-center gap-3">
                    <button @click="tutupForm"
                        class="w-9 h-9 bg-white border border-slate-200 rounded-xl flex items-center justify-center hover:bg-slate-50 transition-colors shadow-sm">
                        <i class="pi pi-arrow-left text-slate-600 text-sm"></i>
                    </button>
                    <div>
                        <h2 class="text-xl font-bold text-slate-800 tracking-tight">Klaim Packing Baru</h2>
                        <p class="text-xs text-slate-500">Tarik WIP dari Produksi menjadi Finished Goods</p>
                    </div>
                </div>

                <!-- Render Form Packing yang baru saja kita buat -->
                <InputPackingForm @tutup="tutupForm" />
            </div>

            <!-- STATE 2: TAMPILAN DAFTAR RIWAYAT PACKING -->
            <div v-else key="list" class="w-full">
                <!-- Header -->
                <div class="mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                    <div>
                        <p class="text-xs text-slate-400 mb-1">
                            <span class="hover:text-slate-700 transition-colors">Warehouse</span> /
                            <span class="hover:text-slate-700 transition-colors font-semibold">Packing Barang Jadi</span>
                        </p>
                        <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Riwayat Packing</h2>
                    </div>
                    <button @click="modeForm = true"
                        class="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl transition-colors shadow-md flex items-center gap-2 transform hover:-translate-y-0.5">
                        <i class="pi pi-plus text-[10px]"></i> Input Packing Baru
                    </button>
                </div>

                <!-- Area Filter & Tabel -->
                <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full min-h-[400px]">

                    <div class="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4 mb-6 pb-4 border-b border-slate-100">
                        <div>
                            <h3 class="text-sm font-bold text-slate-800">Daftar Dokumen Packing</h3>
                            <p class="text-xs text-slate-500">Menampilkan riwayat klaim barang jadi</p>
                        </div>
                    </div>

                    <!-- Loading State -->
                    <div v-if="memuat" class="flex flex-col items-center justify-center py-12 text-center">
                        <i class="pi pi-spin pi-spinner text-slate-300 text-2xl mb-3"></i>
                        <p class="text-xs text-slate-500">Memuat riwayat packing...</p>
                    </div>

                    <!-- Empty State -->
                    <div v-else-if="daftarPacking.length === 0" class="flex flex-col items-center justify-center py-12 text-center">
                        <div class="w-12 h-12 bg-slate-50 rounded-full flex items-center justify-center mb-3 border border-slate-100">
                            <i class="pi pi-box text-slate-300 text-xl"></i>
                        </div>
                        <h4 class="text-sm font-bold text-slate-800 mb-1">Belum ada data packing</h4>
                        <p class="text-xs text-slate-500">Klik "Input Packing Baru" untuk memulai klaim WIP pertama Anda.</p>
                    </div>

                    <!-- Tampilan Tabel -->
                    <div v-else class="overflow-x-auto custom-scrollbar">
                        <table class="w-full text-left text-sm whitespace-nowrap">
                            <thead class="text-slate-500 bg-slate-50/50">
                                <tr>
                                    <th class="py-3 px-4 font-semibold rounded-tl-xl">Nomor & Tanggal</th>
                                    <th class="py-3 px-4 font-semibold">Batch Sumber</th>
                                    <th class="py-3 px-4 font-semibold">Kemasan</th>
                                    <th class="py-3 px-4 font-semibold text-right">Qty (Kg)</th>
                                    <th class="py-3 px-4 font-semibold text-right">Nilai HPP</th>
                                    <th class="py-3 px-4 font-semibold text-center rounded-tr-xl">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="p in daftarPacking" :key="p.id" class="border-b border-slate-100 hover:bg-slate-50/50 transition-colors">
                                    <td class="py-3 px-4">
                                        <div class="font-bold text-slate-800">{{ p.nomor }}</div>
                                        <div class="text-[11px] font-medium text-slate-400 mt-0.5">
                                            <i class="pi pi-calendar text-[10px] mr-1"></i>{{ tanggal(p.tanggal) }}
                                        </div>
                                    </td>
                                    <td class="py-3 px-4 text-slate-700 font-medium">
                                        {{ p.batch_nomor }}
                                        <span class="block text-[10px] text-slate-400">{{ p.batch_hasil }}</span>
                                    </td>
                                    <td class="py-3 px-4 text-slate-600">
                                        {{ p.kemasan_nama }}
                                        <span class="block text-[10px] text-slate-400">{{ p.total_unit }} Unit</span>
                                    </td>
                                    <td class="py-3 px-4 text-right font-bold text-blue-600">{{ angka(p.qty_kg, 3) }}</td>
                                    <td class="py-3 px-4 text-right font-medium text-slate-600">Rp {{ angka(p.nilai_hpp) }}</td>
                                    <td class="py-3 px-4 text-center">
                                        <span :class="badgeColor(p.status)" class="px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wide uppercase border inline-block">
                                            {{ p.status }}
                                        </span>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </transition>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/utils/api'
import { tanggal, angka } from '@/utils/format'
import { useNavInputEntry } from '../composables/useNavInputEntry'
import InputPackingForm from './InputPackingForm.vue'

const { setNavInfo, resetNav } = useNavInputEntry()

const modeForm = ref(false)
const memuat = ref(false)
const daftarPacking = ref([])

// Muat daftar riwayat packing dari backend
const muatRiwayat = async () => {
    memuat.value = true
    try {
        const res = await api.get('inventory/packing/')
        daftarPacking.value = res.data?.results || res.data || []
    } catch (e) {
        console.error("Gagal memuat riwayat packing", e)
    } finally {
        memuat.value = false
    }
}

// Handler saat form ditutup
const tutupForm = () => {
    modeForm.value = false
    muatRiwayat() // Refresh list otomatis agar data baru muncul
}

// Styling badge dinamis
const badgeColor = (status) => {
    const st = String(status).toUpperCase()
    if (st === 'POSTED') return 'bg-emerald-50 text-emerald-600 border-emerald-200'
    if (st === 'DRAFT') return 'bg-amber-50 text-amber-600 border-amber-200'
    if (st === 'VOID') return 'bg-rose-50 text-rose-600 border-rose-200'
    return 'bg-slate-50 text-slate-500 border-slate-200'
}

onMounted(() => {
    setNavInfo('Packing Barang Jadi', 'Warehouse > Input Entry > Packing')
    muatRiwayat()
})
</script>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.3s ease-out forwards;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.fade-enter-active, .fade-leave-active {
    transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
    opacity: 0; transform: translateY(-10px);
}

.custom-scrollbar::-webkit-scrollbar { height: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>
