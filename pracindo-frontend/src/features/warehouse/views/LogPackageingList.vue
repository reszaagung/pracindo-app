<!-- features/warehouse/views/LogPackageingList.vue -->
<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- Header & Breadcrumb -->
        <div class="mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4 md:gap-0">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <router-link to="/warehouse" class="hover:text-slate-700 transition-colors">Warehouse</router-link>
                    <span class="mx-1">/</span>
                    <span class="text-slate-600 font-semibold">Log Packing & Surat Jalan</span>
                </p>
                <div class="flex items-center gap-3">
                    <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Log Packing & Surat Jalan</h2>
                    <span class="bg-amber-100 text-amber-700 text-[10px] font-bold px-2.5 py-1 rounded-full tracking-wide border border-amber-200">GUDANG</span>
                </div>
            </div>
            <div class="flex items-center gap-2">
                <button type="button" @click="muatUlang"
                    class="p-2.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-lg transition-colors shadow-sm">
                    <i class="pi pi-refresh" :class="{ 'pi-spin': isLoading }"></i>
                </button>
                <router-link to="/warehouse/do/create"
                    class="px-4 py-2.5 bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold rounded-lg transition-colors flex items-center gap-2 shadow-sm transform hover:-translate-y-0.5">
                    <i class="pi pi-plus"></i> Input DO Baru
                </router-link>
            </div>
        </div>

        <!-- Filter & Search Bar -->
        <div class="bg-white border border-slate-200 rounded-t-2xl p-4 flex flex-col md:flex-row gap-4 items-center justify-between shadow-sm relative z-10">
            <div class="w-full md:w-96 relative">
                <i class="pi pi-search absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"></i>
                <input v-model="pencarian" type="text" placeholder="Cari No DO, Plat Nomor, atau Pengemudi..."
                    class="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all text-slate-700">
            </div>
            <div class="flex gap-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
                <input type="date" v-model="filterTanggal"
                    class="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-amber-500 text-slate-600">
            </div>
        </div>

        <!-- Notifikasi Error -->
        <div v-if="errorMsg" class="bg-red-50 text-red-600 border-x border-b border-red-200 p-4 text-sm font-medium flex items-center gap-2">
            <i class="pi pi-exclamation-circle"></i> {{ errorMsg }}
        </div>

        <!-- Tabel Log Packing -->
        <div class="w-full bg-white border-x border-b border-slate-200 rounded-b-2xl shadow-sm overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm whitespace-nowrap">
                    <thead class="bg-slate-50 border-b border-slate-200 text-slate-500">
                        <tr>
                            <th class="py-4 px-6 font-semibold w-[5%] text-center">No</th>
                            <th class="py-4 px-6 font-semibold w-[15%]">Tanggal</th>
                            <th class="py-4 px-6 font-semibold w-[20%]">Nomor DO</th>
                            <th class="py-4 px-6 font-semibold w-[25%]">Pengemudi / Plat</th>
                            <th class="py-4 px-6 font-semibold w-[20%] text-center">Item Dimuat</th>
                            <th class="py-4 px-6 font-semibold w-[15%] text-center">Aksi</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        <tr v-if="isLoading">
                            <td colspan="6" class="py-8 text-center text-slate-400">
                                <i class="pi pi-spinner pi-spin text-2xl mb-2 text-amber-500"></i>
                                <p class="text-sm">Memuat log pengiriman...</p>
                            </td>
                        </tr>
                        <tr v-else-if="filteredLog.length === 0">
                            <td colspan="6" class="py-12 text-center text-slate-400 flex flex-col items-center justify-center">
                                <i class="pi pi-box text-4xl mb-3 text-slate-300"></i>
                                <p class="text-sm font-medium">Tidak ada catatan pengiriman yang sesuai.</p>
                            </td>
                        </tr>

                        <!-- Baris Log Data Asli -->
                        <template v-else v-for="(log, index) in filteredLog" :key="log.id">
                            <tr class="hover:bg-slate-50/80 transition-colors group cursor-pointer" @click="toggleDetail(log.id)">
                                <td class="py-4 px-6 text-center text-slate-500">{{ index + 1 }}</td>
                                <td class="py-4 px-6 text-slate-700 font-medium">
                                    <div class="flex items-center gap-1.5">
                                        <i class="pi pi-calendar text-[10px] text-slate-400"></i>
                                        {{ formatDate(log.tanggal) }}
                                    </div>
                                </td>
                                <td class="py-4 px-6">
                                    <span class="font-bold text-slate-800">{{ log.nomor_do || '-' }}</span>
                                    <span class="block text-[10px] text-slate-400 mt-0.5 font-bold uppercase" :class="log.status === 'POSTED' ? 'text-emerald-500' : 'text-amber-500'">
                                        {{ log.status || 'DRAFT' }}
                                    </span>
                                </td>
                                <td class="py-4 px-6">
                                    <span class="font-semibold text-slate-700 block truncate max-w-[150px]">{{ log.pengemudi || 'Belum diisi' }}</span>
                                    <span class="text-xs text-slate-500 border border-slate-200 px-1.5 py-0.5 rounded uppercase mt-1 inline-block">
                                        {{ log.plat_nomor || '-' }}
                                    </span>
                                </td>
                                <td class="py-4 px-6 text-center">
                                    <span class="bg-amber-50 text-amber-600 px-3 py-1 rounded-full text-xs font-bold border border-amber-200">
                                        {{ log.item ? log.item.length : 0 }} Barang
                                    </span>
                                </td>
                                <td class="py-4 px-6 text-center">
                                    <button class="w-8 h-8 rounded-full bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-400 hover:text-amber-600 hover:border-amber-200 transition-colors mx-auto">
                                        <i class="pi text-xs" :class="expandedId === log.id ? 'pi-chevron-up' : 'pi-chevron-down'"></i>
                                    </button>
                                </td>
                            </tr>

                            <!-- Sub-tabel untuk Rincian Item (Expandable) -->
                            <tr v-if="expandedId === log.id" class="bg-slate-50 border-b-2 border-slate-200">
                                <td colspan="6" class="p-0">
                                    <div class="px-4 py-4 md:px-8 animate-fade-in border-l-4 border-amber-400">
                                        <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Detail Muatan Pengiriman</h4>

                                        <div v-if="!log.item || log.item.length === 0" class="text-xs text-slate-400 italic">Belum ada item muatan yang ditambahkan.</div>

                                        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                            <div v-for="(item, idx) in log.item" :key="idx" class="flex justify-between items-center bg-white p-3 border border-slate-200 rounded-xl shadow-sm">
                                                <div class="flex items-center gap-2">
                                                    <div class="w-6 h-6 rounded-md bg-slate-100 flex items-center justify-center text-xs text-slate-500 font-bold">{{ idx + 1 }}</div>
                                                    <span class="text-sm font-semibold text-slate-700">{{ item.produk_nama || 'Nama Produk' }}</span>
                                                </div>
                                                <div class="text-right">
                                                    <span class="text-sm font-black text-slate-800">{{ angka(item.qty) }}</span>
                                                    <span class="text-[10px] text-slate-500 ml-1">Kg/Pcs</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </td>
                            </tr>
                        </template>
                    </tbody>
                </table>
            </div>
            <div class="p-4 border-t border-slate-100 flex items-center justify-between text-sm text-slate-500 bg-slate-50/50">
                <span>Menampilkan <b>{{ filteredLog.length }}</b> catatan pengiriman</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useDeliveryOrder } from '../composables/useDeliveryOrder'
import { angka } from '@/utils/format' // Sesuaikan path formatter angka Anda

const { isLoading, errorMsg, daftarLog, muatData } = useDeliveryOrder()

const pencarian = ref('')
const filterTanggal = ref('')
const expandedId = ref(null)

onMounted(() => {
    muatData()
})

const muatUlang = () => {
    muatData()
}

const toggleDetail = (id) => {
    expandedId.value = expandedId.value === id ? null : id
}

// Logic Pencarian Data Asli dari Backend
const filteredLog = computed(() => {
    return daftarLog.value.filter(log => {
        const keyword = pencarian.value.toLowerCase()
        const matchSearch =
            (log.nomor_do || '').toLowerCase().includes(keyword) ||
            (log.pengemudi || '').toLowerCase().includes(keyword) ||
            (log.plat_nomor || '').toLowerCase().includes(keyword)

        const matchTanggal = filterTanggal.value === '' || log.tanggal === filterTanggal.value
        return matchSearch && matchTanggal
    })
})

const formatDate = (dateString) => {
    if (!dateString) return '-'
    const options = { day: '2-digit', month: 'short', year: 'numeric' }
    return new Date(dateString).toLocaleDateString('id-ID', options)
}
</script>

<style scoped>
.animate-fade-in { animation: fadeIn 0.3s ease-out forwards; }
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
::-webkit-scrollbar { height: 6px; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
</style>
