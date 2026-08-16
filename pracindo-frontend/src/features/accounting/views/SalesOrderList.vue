<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- Header & Breadcrumb -->
        <div class="mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4 md:gap-0">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <router-link to="/" class="hover:text-slate-700 transition-colors">Dashboard</router-link> ›
                    <span class="text-slate-600">Daftar Sales Order</span>
                </p>
                <div class="flex items-center gap-3">
                    <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Data Sales Order (SO)</h2>
                    <span
                        class="bg-blue-50 text-blue-600 text-[10px] font-bold px-2.5 py-1 rounded-full tracking-wide border border-blue-200">AKUNTANSI</span>
                </div>
            </div>

            <div class="flex items-center gap-2">
                <button type="button" @click="fetchSO"
                    class="p-2.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-lg transition-colors">
                    <i class="pi pi-refresh" :class="{ 'pi-spin': isLoading }"></i>
                </button>
                <button type="button" @click="tampilModalSO = true"
                    class="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg transition-colors flex items-center gap-2 shadow-sm">
                    <i class="pi pi-plus"></i> Buat SO Baru
                </button>
            </div>
        </div>

        <!-- Filter & Search Bar -->
        <div
            class="bg-white border border-slate-200 rounded-t-2xl p-4 flex flex-col md:flex-row gap-4 items-center justify-between shadow-sm relative z-10">
            <div class="w-full md:w-96 relative">
                <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"></i>
                <input v-model="pencarian" type="text" placeholder="Cari No. SO atau Pelanggan..."
                    class="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-slate-700" />
            </div>

            <div class="flex gap-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
                <button v-for="tab in tabs" :key="tab.value" @click="filterStatus = tab.value"
                    class="px-4 py-2 text-xs font-bold rounded-lg whitespace-nowrap transition-colors border"
                    :class="{ 'bg-slate-800 text-white border-slate-800': filterStatus === tab.value, 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50': filterStatus !== tab.value }">
                    {{ tab.label }}
                </button>
            </div>
        </div>

        <!-- Tabel Data Sales Order -->
        <div class="w-full bg-white border-x border-b border-slate-200 rounded-b-2xl shadow-sm overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm whitespace-nowrap">
                    <thead class="bg-slate-50 border-b border-slate-200 text-slate-500">
                        <tr>
                            <th class="py-4 px-6 font-semibold">No. Dokumen</th>
                            <th class="py-4 px-6 font-semibold">Tanggal</th>
                            <th class="py-4 px-6 font-semibold">Pelanggan</th>
                            <th class="py-4 px-6 font-semibold text-right">Total Tagihan</th>
                            <th class="py-4 px-6 font-semibold text-center">Status</th>
                            <th class="py-4 px-6 font-semibold text-center">Aksi</th>
                        </tr>
                    </thead>

                    <tbody class="divide-y divide-slate-100">
                        <tr v-if="isLoading">
                            <td colspan="6" class="py-8 text-center text-slate-400">
                                <i class="pi pi-spinner pi-spin text-2xl mb-2 text-blue-500"></i>
                                <p class="text-sm">Memuat data Sales Order...</p>
                            </td>
                        </tr>

                        <tr v-else-if="filteredSO.length === 0">
                            <td colspan="6"
                                class="py-12 text-center text-slate-400 flex flex-col items-center justify-center">
                                <i class="pi pi-folder-open text-4xl mb-3 text-slate-300"></i>
                                <p class="text-sm font-medium">Tidak ada data Sales Order ditemukan.</p>
                            </td>
                        </tr>

                        <template v-else>
                            <tr v-for="so in filteredSO" :key="so.id"
                                class="hover:bg-slate-50/80 transition-colors group">
                                <td class="py-4 px-6">
                                    <span class="font-bold text-slate-700 block">{{ so.nomor_so }}</span>
                                    <span class="text-[10px] text-slate-400 font-medium">{{ so.entitas?.kode || 'UMUM'
                                        }}</span>
                                </td>
                                <td class="py-4 px-6 text-slate-600">{{ formatDate(so.tanggal) }}</td>
                                <td class="py-4 px-6">
                                    <span class="font-semibold text-slate-700 block">{{ so.pelanggan?.nama || '-'
                                        }}</span>
                                    <span class="text-xs text-slate-500"><i class="pi pi-map-marker text-[10px]"></i> {{
                                        so.pelanggan?.kota || '-' }}</span>
                                </td>
                                <td class="py-4 px-6 text-right font-bold text-slate-800">
                                    {{ formatRupiah(so.grand_total) }}
                                </td>
                                <td class="py-4 px-6 text-center">
                                    <span
                                        class="px-2.5 py-1 text-[10px] font-bold rounded-md uppercase tracking-wider border"
                                        :class="badgeColor(so.status)">
                                        {{ so.status }}
                                    </span>
                                </td>
                                <td class="py-4 px-6 text-center">
                                    <div
                                        class="flex items-center justify-center gap-2 opacity-100 md:opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button
                                            class="w-8 h-8 rounded-lg bg-white border border-slate-200 text-blue-600 hover:bg-blue-50 hover:border-blue-200 flex items-center justify-center tooltip-trigger"
                                            title="Lihat Detail">
                                            <i class="pi pi-eye text-xs"></i>
                                        </button>
                                        <button v-if="so.status === 'DRAFT'"
                                            class="w-8 h-8 rounded-lg bg-white border border-slate-200 text-emerald-600 hover:bg-emerald-50 hover:border-emerald-200 flex items-center justify-center"
                                            title="Setujui SO">
                                            <i class="pi pi-check text-xs"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        </template>
                    </tbody>
                </table>
            </div>

            <!-- Footer Info -->
            <div
                class="p-4 border-t border-slate-100 flex items-center justify-between text-sm text-slate-500 bg-slate-50/50">
                <span>Menampilkan <b>{{ filteredSO.length }}</b> dari <b>{{ daftarSO.length }}</b> dokumen</span>
            </div>
        </div>

        <Dialog v-model:visible="tampilModalSO" modal header="Buat Sales Order Baru"
            :style="{ width: '90vw', maxWidth: '1100px' }">
            <LazyFormSO v-if="tampilModalSO" @close="tampilModalSO = false" @saved="soBerhasilDisimpan" />
        </Dialog>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, defineAsyncComponent } from 'vue'
import Dialog from 'primevue/dialog'
import { useSalesOrder } from '@/features/accounting/composables/useSalesOrder'

const LazyFormSO = defineAsyncComponent(() =>
    import('@/features/accounting/views/SalesOrderCreate.vue')
)

const tampilModalSO = ref(false)

const soBerhasilDisimpan = () => {
    tampilModalSO.value = false
    fetchSO()
}
const { isLoading, daftarSO, fetchSO } = useSalesOrder()

const pencarian = ref('')
const filterStatus = ref('SEMUA')

const tabs = [
    { label: 'Semua Data', value: 'SEMUA' },
    { label: 'Draft', value: 'DRAFT' },
    { label: 'Disetujui', value: 'DISETUJUI' },
    { label: 'Selesai', value: 'SELESAI' },
]

onMounted(() => {
    fetchSO()
})

const filteredSO = computed(() => {
    return daftarSO.value.filter(so => {
        const matchStatus = filterStatus.value === 'SEMUA' || so.status === filterStatus.value
        const keyword = pencarian.value.toLowerCase()

        const safeNomorSo = String(so.nomor_so || '').toLowerCase()
        const safePelangganNama = String(so.pelanggan?.nama || '').toLowerCase()

        const matchSearch = safeNomorSo.includes(keyword) || safePelangganNama.includes(keyword)

        return matchStatus && matchSearch
    })
})

// Utilities Formatting
const formatRupiah = (angka) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(angka || 0)
}

const formatDate = (dateString) => {
    if (!dateString) return '-'
    const options = { day: '2-digit', month: 'short', year: 'numeric' }
    return new Date(dateString).toLocaleDateString('id-ID', options)
}

const badgeColor = (status) => {
    switch (status) {
        case 'DRAFT': return 'bg-slate-100 text-slate-600 border-slate-200'
        case 'DISETUJUI': return 'bg-blue-50 text-blue-600 border-blue-200'
        case 'SELESAI': return 'bg-emerald-50 text-emerald-600 border-emerald-200'
        case 'BATAL': return 'bg-red-50 text-red-600 border-red-200'
        default: return 'bg-slate-100 text-slate-600 border-slate-200'
    }
}
</script>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.3s ease-out forwards;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

::-webkit-scrollbar {
    height: 6px;
}

::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 10px;
}
</style>