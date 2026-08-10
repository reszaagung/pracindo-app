    <template>
        <div class="flex flex-col w-full animate-fade-in relative">
            <!-- Header & Breadcrumb -->
            <div class="mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4 md:gap-0">
                <div>
                    <p class="text-xs text-slate-400 mb-1">
                        <router-link to="/" class="hover:text-slate-700 transition-colors">Dashboard</router-link> ›
                        <span class="text-slate-600">Piutang (AR)</span>
                    </p>
                    <div class="flex items-center gap-3">
                        <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Daftar Invoice Penagihan
                        </h2>
                        <span
                            class="bg-indigo-100 text-indigo-700 text-[10px] font-bold px-2.5 py-1 rounded-full tracking-wide border border-indigo-200">KEUANGAN</span>
                    </div>
                </div>

                <div class="flex items-center gap-2">
                    <button type="button" @click="fetchInvoices"
                        class="p-2.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-lg transition-colors">
                        <i class="pi pi-refresh" :class="{ 'pi-spin': isLoading }"></i>
                    </button>
                    <router-link to="/accounting/invoice/create"
                        class="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg transition-colors flex items-center gap-2 shadow-sm">
                        <i class="pi pi-plus"></i> Buat Invoice Baru
                    </router-link>
                </div>
            </div>

            <!-- Filter & Search Bar -->
            <div
                class="bg-white border border-slate-200 rounded-t-2xl p-4 flex flex-col md:flex-row gap-4 items-center justify-between shadow-sm relative z-10">
                <div class="w-full md:w-96 relative">
                    <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"></i>
                    <input v-model="pencarian" type="text" placeholder="Cari No. Invoice, Pelanggan, atau Ref SO..."
                        class="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all text-slate-700" />
                </div>

                <div class="flex gap-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
                    <button v-for="tab in tabs" :key="tab.value" @click="filterStatus = tab.value"
                        class="px-4 py-2 text-xs font-bold rounded-lg whitespace-nowrap transition-colors border"
                        :class="{ 'bg-slate-800 text-white border-slate-800': filterStatus === tab.value, 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50': filterStatus !== tab.value }">
                        {{ tab.label }}
                    </button>
                </div>
            </div>

            <!-- Tabel Data Invoice -->
            <div class="w-full bg-white border-x border-b border-slate-200 rounded-b-2xl shadow-sm overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm whitespace-nowrap">
                        <thead class="bg-slate-50 border-b border-slate-200 text-slate-500">
                            <tr>
                                <th class="py-4 px-6 font-semibold">No. Invoice</th>
                                <th class="py-4 px-6 font-semibold">Referensi SO</th>
                                <th class="py-4 px-6 font-semibold">Pelanggan</th>
                                <th class="py-4 px-6 font-semibold">Tanggal Terbit</th>
                                <th class="py-4 px-6 font-semibold">Jatuh Tempo</th>
                                <th class="py-4 px-6 font-semibold text-right">Total Tagihan</th>
                                <th class="py-4 px-6 font-semibold text-center">Status</th>
                                <th class="py-4 px-6 font-semibold text-center">Aksi</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-if="isLoading">
                                <td colspan="8" class="py-8 text-center text-slate-400">
                                    <i class="pi pi-spinner pi-spin text-2xl mb-2 text-indigo-500"></i>
                                    <p class="text-sm">Memuat data tagihan...</p>
                                </td>
                            </tr>
                            <tr v-else-if="filteredInvoice.length === 0">
                                <td colspan="8"
                                    class="py-12 text-center text-slate-400 flex flex-col items-center justify-center">
                                    <i class="pi pi-receipt text-4xl mb-3 text-slate-300"></i>
                                    <p class="text-sm font-medium">Tidak ada data invoice ditemukan.</p>
                                </td>
                            </tr>
                            <template v-else>
                                <tr v-for="inv in filteredInvoice" :key="inv.id"
                                    class="hover:bg-slate-50/80 transition-colors group">
                                    <td class="py-4 px-6">
                                        <span class="font-black text-slate-700 block">{{ inv.nomor_faktur }}</span>
                                    </td>
                                    <td class="py-4 px-6">
                                        <span
                                            class="font-semibold text-indigo-600 block cursor-pointer hover:underline">{{
                                                inv.referensi_so }}</span>
                                    </td>
                                    <td class="py-4 px-6 text-slate-700 font-medium">
                                        {{ inv.pelanggan }}
                                    </td>
                                    <td class="py-4 px-6 text-slate-600">{{ formatDate(inv.tanggal_faktur) }}</td>
                                    <td class="py-4 px-6">
                                        <span
                                            :class="{ 'text-red-600 font-bold': inv.ui_status === 'JATUH TEMPO', 'text-slate-600': inv.ui_status !== 'JATUH TEMPO' }">
                                            {{ formatDate(inv.tanggal_jatuh_tempo) }}
                                        </span>
                                    </td>
                                    <td class="py-4 px-6 text-right font-black text-slate-800">
                                        {{ formatRupiah(inv.total_tagihan) }}
                                    </td>
                                    <td class="py-4 px-6 text-center">
                                        <span
                                            class="px-2.5 py-1.5 text-[10px] font-bold rounded-md uppercase tracking-wider border"
                                            :class="badgeColor(inv.ui_status)">
                                            <i class="mr-1" :class="badgeIcon(inv.ui_status)"></i> {{ inv.ui_status }}
                                        </span>
                                    </td>
                                    <td class="py-4 px-6 text-center">
                                        <div
                                            class="flex items-center justify-center gap-2 opacity-100 md:opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button
                                                class="w-8 h-8 rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-indigo-600 flex items-center justify-center tooltip-trigger"
                                                title="Cetak PDF">
                                                <i class="pi pi-print text-xs"></i>
                                            </button>
                                            <button v-if="inv.status_asli !== 'LUNAS'" @click="tandaiLunas(inv)"
                                                class="w-8 h-8 rounded-lg bg-white border border-slate-200 text-emerald-600 hover:bg-emerald-50 hover:border-emerald-200 flex items-center justify-center"
                                                title="Catat Pembayaran">
                                                <i class="pi pi-wallet text-xs"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            </template>
                        </tbody>
                    </table>
                </div>

                <!-- Summary Bar (Total Piutang) -->
                <div
                    class="p-4 border-t border-slate-100 flex flex-col md:flex-row items-center justify-between text-sm bg-slate-50/50 gap-4">
                    <span class="text-slate-500">Menampilkan <b>{{ filteredInvoice.length }}</b> dokumen tagihan</span>
                    <div
                        class="flex gap-4 font-bold text-slate-700 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm">
                        <span>Total Outstanding: <span class="text-indigo-600 ml-1">{{
                            formatRupiah(totalOutstandingFiltered)
                                }}</span></span>
                    </div>
                </div>
            </div>
        </div>
    </template>

<script setup>
import { ref, computed, onMounted } from 'vue'
// PERBAIKAN: Gunakan path relatif yang benar dan panggil useInvoice
import { useInvoice } from '../composables/useInvoice'

// Ekstrak state dan fungsi asli dari backend
const { isLoading, daftarInvoice, fetchInvoices } = useInvoice()

const pencarian = ref('')
const filterStatus = ref('SEMUA')

const tabs = [
    { label: 'Semua', value: 'SEMUA' },
    { label: 'Belum Bayar', value: 'BELUM_BAYAR' },
    { label: 'Lunas', value: 'LUNAS' },
    { label: 'Jatuh Tempo', value: 'JATUH TEMPO' },
]

// Panggil API saat halaman Invoice dimuat
onMounted(() => {
    fetchInvoices()
})

const tandaiLunas = (inv) => {
    alert(`Fitur Catat Pembayaran untuk ${inv.nomor_faktur} akan membuka modal pembayaran.`)
}

// Fitur Filter & Search
const filteredInvoice = computed(() => {
    return daftarInvoice.value.filter(inv => {
        // Normalisasi status UI vs Tab Value
        const currentUiStatus = inv.ui_status === 'BELUM BAYAR' ? 'BELUM_BAYAR' : inv.ui_status
        const matchStatus = filterStatus.value === 'SEMUA' || currentUiStatus === filterStatus.value

        const keyword = pencarian.value.toLowerCase()

        // Safety check untuk mencegah error jika data null
        const matchSearch = (inv.nomor_faktur || '').toLowerCase().includes(keyword) ||
            (inv.referensi_so || '').toLowerCase().includes(keyword) ||
            (inv.pelanggan || '').toLowerCase().includes(keyword)

        return matchStatus && matchSearch
    })
})

// Menghitung Total Uang yang belum masuk (Sisa Piutang) KHUSUS untuk data yang difilter saat ini
const totalOutstandingFiltered = computed(() => {
    return filteredInvoice.value
        .filter(inv => inv.status_asli === 'BELUM_BAYAR' || inv.status_asli === 'SEBAGIAN')
        .reduce((sum, inv) => sum + inv.sisa_piutang, 0)
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
        case 'BELUM_BAYAR':
        case 'BELUM BAYAR': return 'bg-amber-50 text-amber-600 border-amber-200'
        case 'SEBAGIAN': return 'bg-blue-50 text-blue-600 border-blue-200'
        case 'LUNAS': return 'bg-emerald-50 text-emerald-600 border-emerald-200'
        case 'JATUH TEMPO': return 'bg-red-50 text-red-600 border-red-200'
        default: return 'bg-slate-100 text-slate-600 border-slate-200'
    }
}

const badgeIcon = (status) => {
    switch (status) {
        case 'BELUM_BAYAR':
        case 'BELUM BAYAR': return 'pi pi-clock'
        case 'SEBAGIAN': return 'pi pi-percentage'
        case 'LUNAS': return 'pi pi-check-circle'
        case 'JATUH TEMPO': return 'pi pi-exclamation-triangle'
        default: return 'pi pi-info-circle'
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