<template>
    <div class="flex flex-col w-full animate-fade-in relative gap-6">

        <!-- Header & Greeting -->
        <div class="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 md:gap-0 mb-2">
            <div>
                <p class="text-xs text-slate-400 mb-1">PracindoERP › Master Dashboard</p>
                <h2 class="text-2xl md:text-3xl font-bold text-slate-800 tracking-tight">Selamat pagi, Resza! 👋</h2>
                <p class="text-sm text-slate-500 mt-1">Berikut adalah ringkasan performa operasional dan finansial hari
                    ini.</p>
            </div>
            <div class="flex items-center gap-2">
                <button type="button" @click="muatDataDashboard"
                    class="p-2 bg-white border border-slate-200 text-slate-600 rounded-xl shadow-sm hover:bg-slate-50 transition-colors">
                    <i class="pi pi-refresh" :class="{ 'pi-spin': isLoading }"></i>
                </button>
                <div
                    class="px-4 py-2 bg-white border border-slate-200 text-slate-600 text-xs font-bold rounded-xl shadow-sm flex items-center gap-2">
                    <i class="pi pi-calendar text-indigo-500"></i> {{ tanggalHariIni }}
                </div>
            </div>
        </div>

        <!-- Notifikasi Error (Jika API Gagal) -->
        <div v-if="pesanError"
            class="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 font-medium flex items-start gap-3">
            <i class="pi pi-exclamation-triangle mt-0.5"></i>
            <span>{{ pesanError }}</span>
        </div>

        <!-- KPI / Quick Stats Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
            <!-- Card 1: CRM / Leads -->
            <div
                class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col relative overflow-hidden group">
                <div
                    class="absolute -right-4 -top-4 w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                    <i class="pi pi-users text-blue-500 text-xl"></i>
                </div>
                <span class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Prospek Aktif (CRM)</span>
                <span class="text-3xl font-black text-slate-800">
                    <i v-if="isLoading" class="pi pi-spinner pi-spin text-xl text-slate-300"></i>
                    <span v-else>{{ kpi.prospek_aktif }}</span>
                </span>
                <div class="text-xs font-medium mt-3 flex items-center gap-1 text-emerald-600">
                    <i class="pi pi-arrow-up text-[10px]"></i> {{ kpi.pertumbuhan_prospek }}% dari bulan lalu
                </div>
            </div>

            <!-- Card 2: Sales Order -->
            <div
                class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col relative overflow-hidden group">
                <div
                    class="absolute -right-4 -top-4 w-16 h-16 bg-emerald-50 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                    <i class="pi pi-shopping-cart text-emerald-500 text-xl"></i>
                </div>
                <span class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Sales Order (Bulan
                    Ini)</span>
                <span class="text-2xl font-black text-slate-800 truncate">
                    <i v-if="isLoading" class="pi pi-spinner pi-spin text-xl text-slate-300"></i>
                    <span v-else>{{ formatSingkat(kpi.sales_order_bulan_ini) }}</span>
                </span>
                <div class="text-xs font-medium mt-3 flex items-center gap-1 text-slate-500">
                    <i class="pi pi-check-circle text-[10px]"></i> {{ kpi.so_disetujui }} SO Disetujui
                </div>
            </div>

            <!-- Card 3: Gudang / DO -->
            <div
                class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col relative overflow-hidden group">
                <div
                    class="absolute -right-4 -top-4 w-16 h-16 bg-amber-50 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                    <i class="pi pi-box text-amber-500 text-xl"></i>
                </div>
                <span class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Antrean Pengiriman</span>
                <span class="text-3xl font-black text-slate-800">
                    <i v-if="isLoading" class="pi pi-spinner pi-spin text-xl text-slate-300"></i>
                    <span v-else>{{ kpi.antrean_pengiriman }} <span class="text-sm font-bold text-slate-400">Surat
                            Jalan</span></span>
                </span>
                <div class="text-xs font-medium mt-3 flex items-center gap-1 text-amber-600">
                    <i class="pi pi-exclamation-circle text-[10px]"></i> Perlu segera dikirim
                </div>
            </div>

            <!-- Card 4: Keuangan / AR -->
            <div
                class="bg-white p-5 rounded-2xl border border-red-100 shadow-sm flex flex-col relative overflow-hidden group">
                <div
                    class="absolute -right-4 -top-4 w-16 h-16 bg-red-50 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                    <i class="pi pi-wallet text-red-500 text-xl"></i>
                </div>
                <span class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Piutang Jatuh Tempo</span>
                <span class="text-2xl font-black text-red-600 truncate">
                    <i v-if="isLoading" class="pi pi-spinner pi-spin text-xl text-red-300"></i>
                    <span v-else>{{ formatSingkat(kpi.piutang_jatuh_tempo) }}</span>
                </span>
                <div class="text-xs font-medium mt-3 flex items-center gap-1 text-red-500">
                    <i class="pi pi-info-circle text-[10px]"></i> Dari {{ kpi.jumlah_invoice_tunggak }} Invoice
                    tertunggak
                </div>
            </div>
        </div>

        <!-- Bawah: 2 Kolom (Notifikasi & Aktivitas) -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-2">

            <!-- Kolom Kiri: Piutang Kritis -->
            <div class="bg-white border border-slate-200 rounded-2xl shadow-sm flex flex-col h-full">
                <div class="p-5 border-b border-slate-100 flex justify-between items-center">
                    <h3 class="font-bold text-slate-800 flex items-center gap-2">
                        <i class="pi pi-exclamation-triangle text-red-500"></i> Perhatian Keuangan
                    </h3>
                    <router-link to="/accounting/invoice"
                        class="text-xs font-bold text-indigo-600 hover:text-indigo-700">Lihat Semua AR</router-link>
                </div>
                <div class="p-5 flex flex-col gap-4">

                    <div v-if="isLoading" class="flex justify-center py-6">
                        <i class="pi pi-spinner pi-spin text-2xl text-slate-300"></i>
                    </div>

                    <template v-else>
                        <div v-for="inv in invoiceKritis" :key="inv.id"
                            class="p-4 rounded-xl border border-red-100 bg-red-50/30 flex justify-between items-center hover:bg-red-50 transition-colors">
                            <div>
                                <span class="text-sm font-bold text-slate-800 block">{{ inv.pelanggan_nama }}</span>
                                <span class="text-xs text-slate-500">{{ inv.nomor_invoice }} • Telat {{ inv.hari_telat
                                    }} hari</span>
                            </div>
                            <div class="text-right">
                                <span class="text-sm font-black text-red-600 block">{{ formatRupiah(inv.grand_total)
                                    }}</span>
                                <button class="text-[10px] font-bold text-indigo-600 hover:underline mt-1">Kirim
                                    Reminder</button>
                            </div>
                        </div>
                        <div v-if="invoiceKritis.length === 0" class="text-center text-slate-400 py-6 text-sm">
                            <i class="pi pi-check-circle text-2xl text-emerald-400 mb-2 block"></i>
                            Tidak ada tagihan jatuh tempo.
                        </div>
                    </template>
                </div>
            </div>

            <!-- Kolom Kanan: Aktivitas Gudang Terkini -->
            <div class="bg-white border border-slate-200 rounded-2xl shadow-sm flex flex-col h-full">
                <div class="p-5 border-b border-slate-100 flex justify-between items-center">
                    <h3 class="font-bold text-slate-800 flex items-center gap-2">
                        <i class="pi pi-history text-amber-500"></i> Logistik Terakhir
                    </h3>
                    <router-link to="/warehouse/do/log"
                        class="text-xs font-bold text-amber-600 hover:text-amber-700">Log
                        Packing</router-link>
                </div>
                <div class="p-5">

                    <div v-if="isLoading" class="flex justify-center py-6">
                        <i class="pi pi-spinner pi-spin text-2xl text-slate-300"></i>
                    </div>

                    <div v-else class="relative border-l-2 border-slate-100 ml-3 py-2 flex flex-col gap-6">
                        <div v-for="(log, idx) in aktivitasGudang" :key="idx" class="relative pl-6">
                            <div
                                class="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-white border-2 border-amber-400">
                            </div>
                            <div class="flex justify-between items-start">
                                <div>
                                    <p class="text-sm font-bold text-slate-700">{{ log.pesan_aktivitas }}</p>
                                    <p class="text-xs text-slate-500 mt-0.5">Pengemudi: {{ log.pengemudi }} ({{
                                        log.plat_nomor }})
                                    </p>
                                </div>
                                <span class="text-[10px] font-bold text-slate-400">{{ log.waktu_relatif }}</span>
                            </div>
                        </div>

                        <div v-if="aktivitasGudang.length === 0" class="text-center text-slate-400 py-4 text-sm">
                            Belum ada aktivitas pengiriman terbaru.
                        </div>
                    </div>
                </div>
            </div>

        </div>
    </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useDashboard } from '@/composables/useDashboard'

const { isLoading, pesanError, kpi, invoiceKritis, aktivitasGudang, muatDataDashboard } = useDashboard()

onMounted(() => {
    // Tarik data asli dari backend begitu halaman dirender
    muatDataDashboard()
})

const tanggalHariIni = computed(() => {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }
    return new Date().toLocaleDateString('id-ID', options)
})

const formatRupiah = (angka) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(angka || 0)
}

// Fungsi untuk meringkas angka besar (Contoh: Rp 128.000.000 menjadi Rp 128 Jt)
const formatSingkat = (angka) => {
    if (!angka) return 'Rp 0'
    if (angka >= 1000000000) return `Rp ${(angka / 1000000000).toFixed(1)} M`
    if (angka >= 1000000) return `Rp ${(angka / 1000000).toFixed(1)} Jt`
    if (angka >= 1000) return `Rp ${(angka / 1000).toFixed(1)} Rb`
    return formatRupiah(angka)
}
</script>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.4s ease-out forwards;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(15px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>