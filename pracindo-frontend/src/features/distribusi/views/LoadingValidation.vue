<!-- src/features/distribusi/views/LoadingValidation.vue -->
<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <div class="mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <span class="hover:text-slate-700 transition-colors">Distribution</span> /
                    <span class="text-slate-600 font-semibold">Validasi Muat (Loading)</span>
                </p>
                <h1 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Validasi Muat Barang</h1>
                <p class="text-xs md:text-sm text-slate-500 mt-1">Pindai atau centang barang yang naik ke armada agar sesuai dengan DO.</p>
            </div>

            <!-- Fitur Pencarian Dinamis -->
            <div class="flex gap-2 w-full md:w-auto">
                <input v-model="idCari" @keyup.enter="cariData" type="text" placeholder="Masukkan ID Pengiriman..."
                    class="px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-full md:w-48 shadow-sm" />
                <button @click="cariData" :disabled="!idCari || memuat" class="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-400 text-white text-sm font-bold rounded-xl transition-colors shadow-md">
                    Cari
                </button>
                <button class="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold rounded-xl transition-colors shadow-md flex items-center gap-2">
                    <i class="pi pi-qrcode text-xs"></i>
                    <span class="hidden md:inline">Scan</span>
                </button>
            </div>
        </div>

        <!-- State Memuat -->
        <div v-if="memuat" class="py-12 flex justify-center bg-white border border-slate-200 rounded-[24px] shadow-sm">
            <i class="pi pi-spin pi-spinner text-3xl text-blue-500"></i>
        </div>

        <!-- State Galat -->
        <div v-else-if="galat" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 font-medium flex items-start gap-3 shadow-sm">
            <i class="pi pi-exclamation-triangle mt-0.5"></i>
            <span>{{ galat }}</span>
        </div>

        <!-- State Awal (Belum Ada Pencarian) -->
        <div v-else-if="!pengiriman" class="bg-white border border-slate-200 rounded-[24px] p-12 text-center shadow-sm w-full mb-6">
            <div class="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4 border border-slate-100">
                <i class="pi pi-search text-slate-300 text-2xl"></i>
            </div>
            <h3 class="text-slate-700 font-bold mb-1">Cari Dokumen Pengiriman</h3>
            <p class="text-slate-500 text-sm">Masukkan ID Pengiriman di atas untuk memulai validasi loading barang ke armada.</p>
        </div>

        <!-- Tabel Data Pengiriman Asli -->
        <div v-else class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full mb-6">
            <div class="flex flex-col md:flex-row justify-between md:items-center border-b border-slate-100 pb-4 mb-4">
                <div>
                    <h2 class="text-lg font-black text-slate-800">{{ pengiriman.nomor || `DO-${pengiriman.id}` }}</h2>
                    <p class="text-sm text-slate-500 font-medium">Tujuan: {{ pengiriman.tujuan_nama || pengiriman.pelanggan_nama || 'Multi Tujuan' }}</p>
                </div>
                <div class="mt-3 md:mt-0 text-left md:text-right">
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Armada</span>
                    <span class="px-3 py-1 bg-slate-100 text-slate-700 rounded-lg text-sm font-bold border border-slate-200 inline-block">
                        <i class="pi pi-truck mr-1 text-slate-400"></i>
                        {{ pengiriman.kendaraan_plat || (pengiriman.kendaraan && pengiriman.kendaraan.plat_nomor) || 'Truk Reguler' }}
                        ({{ pengiriman.kurir_nama || (pengiriman.kurir && pengiriman.kurir.nama) || 'Kurir' }})
                    </span>
                </div>
            </div>

            <div class="overflow-x-auto custom-scrollbar">
                <table class="w-full text-left text-sm table-auto min-w-[50rem]">
                    <thead class="text-slate-500 bg-slate-50/50">
                        <tr>
                            <th class="py-3 px-4 font-semibold rounded-tl-xl w-[40%]">Nama Produk / Varian</th>
                            <th class="py-3 px-4 font-semibold text-right w-[15%]">Qty DO</th>
                            <th class="py-3 px-4 font-semibold text-right w-[15%]">Qty Muat</th>
                            <th class="py-3 px-4 font-semibold text-center w-[15%]">Status</th>
                            <th class="py-3 px-4 font-semibold text-center rounded-tr-xl w-[15%]">Aksi</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        <!-- Kondisi jika tabel muatan kosong dari backend -->
                        <tr v-if="!pengiriman.items || pengiriman.items.length === 0">
                            <td colspan="5" class="py-8 text-center text-slate-400 italic">Data muatan tidak ditemukan dalam dokumen ini.</td>
                        </tr>

                        <!-- Looping Item/Barang Nyata -->
                        <tr v-for="(item, idx) in (pengiriman.items || [])" :key="item.id || idx" class="hover:bg-slate-50/50 transition-colors">
                            <td class="py-4 px-4">
                                <div class="font-bold text-slate-800">{{ item.produk_nama || item.nama_produk || 'Produk ID ' + (item.produk_id || idx) }}</div>
                                <div class="text-[11px] text-slate-500 mt-0.5">{{ item.kemasan || 'Kemasan Standard' }}</div>
                            </td>
                            <td class="py-4 px-4 text-right font-medium text-slate-500">{{ item.qty_do || item.qty_kg || 0 }}</td>
                            <td class="py-4 px-4 text-right font-black text-base" :class="(item.qty_muat >= (item.qty_do || item.qty_kg)) ? 'text-emerald-600' : 'text-amber-500'">
                                {{ item.qty_muat || 0 }}
                            </td>
                            <td class="py-4 px-4 text-center">
                                <span v-if="(item.qty_muat || 0) >= (item.qty_do || item.qty_kg || 0)" class="px-2.5 py-1 bg-emerald-50 text-emerald-600 border border-emerald-200 rounded-md text-[10px] font-bold tracking-wide uppercase">Sesuai</span>
                                <span v-else class="px-2.5 py-1 bg-amber-50 text-amber-600 border border-amber-200 rounded-md text-[10px] font-bold tracking-wide uppercase">Kurang</span>
                            </td>
                            <td class="py-4 px-4 text-center">
                                <button v-if="(item.qty_muat || 0) >= (item.qty_do || item.qty_kg || 0)" class="w-8 h-8 bg-slate-100 text-slate-400 rounded-lg cursor-not-allowed mx-auto flex items-center justify-center">
                                    <i class="pi pi-check"></i>
                                </button>
                                <button v-else @click="simulasiTambahMuat(item)" class="w-8 h-8 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-600 hover:text-white transition-colors mx-auto flex items-center justify-center shadow-sm">
                                    <i class="pi pi-plus"></i>
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="mt-6 pt-4 border-t border-slate-100 flex justify-end">
                <button class="px-8 py-3 bg-slate-900 hover:bg-slate-800 text-white text-sm font-bold rounded-xl transition-all shadow-md flex items-center gap-2 transform hover:-translate-y-0.5">
                    <i class="pi pi-verified text-xs"></i>
                    <span>Selesaikan Loading & Kunci DO</span>
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { apiDistribusi } from '../api'

const route = useRoute()
const pengiriman = ref(null)
const memuat = ref(false)
const galat = ref('')
const idCari = ref('')

// Fungsi menarik data pengiriman dari Django Backend
const cariData = async () => {
    if (!idCari.value) return
    memuat.value = true
    galat.value = ''
    pengiriman.value = null
    try {
        const data = await apiDistribusi.getDetailPengiriman(idCari.value)
        pengiriman.value = data
    } catch (error) {
        galat.value = 'Dokumen pengiriman tidak ditemukan atau terjadi kesalahan server.'
        console.error(error)
    } finally {
        memuat.value = false
    }
}

// Simulasi fungsi tombol "Plus (+)" di tabel untuk update kuantitas naik truk
const simulasiTambahMuat = (item) => {
    if (!item.qty_muat) item.qty_muat = 0
    item.qty_muat += 1
    // Nanti bisa Anda kembangkan untuk memanggil endpoint PATCH ke server
}

onMounted(() => {
    // Memungkinkan fitur klik rute dari halaman lain (contoh: /distribusi/loading?id=12)
    if (route.query.id) {
        idCari.value = route.query.id
        cariData()
    }
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
