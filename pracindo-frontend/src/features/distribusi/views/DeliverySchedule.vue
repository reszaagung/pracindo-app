<!-- src/features/distribusi/views/DeliverySchedule.vue -->
<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- Header Halaman -->
        <div class="mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <span class="hover:text-slate-700 transition-colors">Distribution</span> /
                    <span class="text-slate-600 font-semibold">Jadwal Pengiriman</span>
                </p>
                <h1 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Jadwal Pengiriman</h1>
                <p class="text-xs md:text-sm text-slate-500 mt-1">Pantau rencana muat dan rute pengiriman ke retail atau kustomer.</p>
            </div>
            <button @click="$router.push('/distribusi/buat')"
                class="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-bold rounded-xl transition-colors shadow-md flex items-center gap-2 w-full md:w-auto justify-center">
                <i class="pi pi-plus text-xs"></i>
                <span>Buat Jadwal Baru</span>
            </button>
        </div>

        <!-- Panel Filter & Pencarian -->
        <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full mb-6">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div class="flex flex-col gap-1.5 md:col-span-2">
                    <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Cari Dokumen</label>
                    <div class="relative">
                        <i class="pi pi-search absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"></i>
                        <input type="text" placeholder="Ketik No. Pengiriman atau Tujuan..."
                            class="w-full pl-11 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-slate-800 text-slate-800 font-medium transition-colors" />
                    </div>
                </div>
                <div class="flex flex-col gap-1.5">
                    <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Tanggal Pengiriman</label>
                    <input type="date"
                        class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-slate-800 text-slate-800 font-medium transition-colors" />
                </div>
                <div class="flex flex-col gap-1.5">
                    <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Status</label>
                    <select
                        class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-slate-800 text-slate-800 font-medium appearance-none cursor-pointer transition-colors">
                        <option value="">Semua Status</option>
                        <option value="TERJADWAL">Terjadwal</option>
                        <option value="LOADING">Proses Loading</option>
                        <option value="DIKIRIM">Sedang Dikirim</option>
                        <option value="SELESAI">Selesai</option>
                    </select>
                </div>
            </div>
        </div>

        <!-- Tabel Jadwal Pengiriman -->
        <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full min-h-[400px]">

            <!-- State Loading -->
            <div v-if="sedangMemuat" class="flex flex-col items-center justify-center py-16 text-center">
                <i class="pi pi-spin pi-spinner text-blue-500 text-4xl mb-4"></i>
                <p class="text-sm font-medium text-slate-500">Memuat jadwal pengiriman...</p>
            </div>

            <!-- Tampilan Desktop -->
            <div v-else-if="daftarJadwal.length > 0" class="hidden md:block overflow-x-auto custom-scrollbar">
                <table class="w-full text-left text-sm table-auto min-w-[60rem]">
                    <thead class="text-slate-500 bg-slate-50/50">
                        <tr>
                            <th class="py-3 px-4 font-semibold rounded-tl-xl">No. Pengiriman / Tanggal</th>
                            <th class="py-3 px-4 font-semibold">Tujuan (Retail/Customer)</th>
                            <th class="py-3 px-4 font-semibold">Armada & Supir</th>
                            <th class="py-3 px-4 font-semibold text-center">Status</th>
                            <th class="py-3 px-4 font-semibold text-right rounded-tr-xl">Aksi</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        <tr v-for="item in daftarJadwal" :key="item.id"
                            class="hover:bg-slate-50/50 transition-colors group">
                            <td class="py-3 px-4 align-top">
                                <div class="font-bold text-slate-800">{{ item.nomor || `DO-${item.id}` }}</div>
                                <div class="text-xs text-slate-500 mt-0.5">{{ item.tanggal }}</div>
                            </td>
                            <td class="py-3 px-4 align-top">
                                <div class="font-bold text-slate-700">{{ item.tujuan_nama || item.pelanggan_nama || 'Sesuai Rute Muatan' }}</div>
                                <div class="text-[11px] text-slate-500 mt-0.5 flex items-center gap-1">
                                    <i class="pi pi-map-marker text-[10px]"></i> {{ item.tujuan_alamat || item.alamat || 'Lihat detail rute di dalam' }}
                                </div>
                            </td>
                            <td class="py-3 px-4 align-top">
                                <div class="font-semibold text-slate-700">{{ item.kendaraan_plat || (item.kendaraan && item.kendaraan.plat_nomor) || 'Truk Reguler' }}</div>
                                <div class="text-xs text-slate-500 mt-0.5">{{ item.kurir_nama || (item.kurir && item.kurir.nama) || 'Menunggu Kurir' }}</div>
                            </td>
                            <td class="py-3 px-4 align-top text-center pt-4">
                                <span
                                    class="px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wide uppercase border"
                                    :class="badgeWarna(item.status || 'TERJADWAL')">
                                    {{ item.status || 'TERJADWAL' }}
                                </span>
                            </td>
                            <td class="py-3 px-4 align-top text-right pt-3">
                                <button
                                    class="w-8 h-8 bg-slate-50 text-slate-500 rounded-lg hover:bg-slate-900 hover:text-white transition-colors flex items-center justify-center ml-auto"
                                    title="Detail Pengiriman">
                                    <i class="pi pi-chevron-right text-xs"></i>
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Tampilan Mobile (Card) -->
            <div v-else-if="daftarJadwal.length > 0" class="md:hidden flex flex-col gap-4">
                <div v-for="item in daftarJadwal" :key="'mob-' + item.id"
                    class="border border-slate-200 rounded-xl p-4 bg-slate-50/30 active:scale-[0.98] transition-transform cursor-pointer">
                    <div class="flex justify-between items-start mb-3 border-b border-slate-100 pb-3">
                        <div>
                            <div class="font-bold text-slate-800 text-sm">{{ item.nomor || `DO-${item.id}` }}</div>
                            <div class="text-xs text-slate-500">{{ item.tanggal }}</div>
                        </div>
                        <span class="px-2 py-1 rounded-md text-[9px] font-bold tracking-wide uppercase border"
                            :class="badgeWarna(item.status || 'TERJADWAL')">
                            {{ item.status || 'TERJADWAL' }}
                        </span>
                    </div>
                    <div class="flex flex-col gap-2 mb-3">
                        <div>
                            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Tujuan</span>
                            <div class="font-semibold text-slate-700 text-sm">{{ item.tujuan_nama || item.pelanggan_nama || 'Sesuai Rute Muatan' }}</div>
                            <div class="text-[11px] text-slate-500 line-clamp-1">{{ item.tujuan_alamat || item.alamat || 'Lihat detail rute di dalam' }}</div>
                        </div>
                        <div>
                            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Armada</span>
                            <div class="text-sm font-medium text-slate-700">
                                {{ item.kendaraan_plat || (item.kendaraan && item.kendaraan.plat_nomor) || 'Truk Reguler' }} &bull; {{ item.kurir_nama || (item.kurir && item.kurir.nama) || 'Menunggu Kurir' }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- State Kosong -->
            <div v-else class="flex flex-col items-center justify-center py-12 text-center">
                <div class="w-12 h-12 bg-slate-50 rounded-full flex items-center justify-center mb-3 border border-slate-100">
                    <i class="pi pi-calendar-times text-slate-300 text-xl"></i>
                </div>
                <h4 class="text-sm font-bold text-slate-800 mb-1">Belum Ada Jadwal</h4>
                <p class="text-xs text-slate-500">Tidak ada pengiriman yang dijadwalkan pada filter saat ini.</p>
            </div>
        </div>
    </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useDistribusi } from '../composables/useDistribusi'

const { daftarJadwal, sedangMemuat, muatJadwal } = useDistribusi()

const badgeWarna = (status) => {
    switch (status.toUpperCase()) {
        case 'DRAFT': return 'bg-slate-100 text-slate-600 border-slate-200'
        case 'TERJADWAL': return 'bg-amber-50 text-amber-600 border-amber-200'
        case 'LOADING': return 'bg-blue-50 text-blue-600 border-blue-200'
        case 'DIKIRIM': return 'bg-purple-50 text-purple-600 border-purple-200'
        case 'SELESAI': return 'bg-emerald-50 text-emerald-600 border-emerald-200'
        default: return 'bg-slate-50 text-slate-500 border-slate-200'
    }
}

onMounted(() => {
    // Memanggil API getSemuaPengiriman() saat halaman dibuka
    muatJadwal()
})
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

.custom-scrollbar::-webkit-scrollbar {
    height: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}
</style>
