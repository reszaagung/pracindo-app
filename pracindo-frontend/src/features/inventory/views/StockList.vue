<!--
  features/inventory/views/StockList.vue
  ========================================
  Tab per lapis: RAW, POOL, JADI dengan desain Tailwind CSS Modern.
-->
<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- Header Halaman -->
        <div class="mb-4 md:mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <span class="hover:text-slate-700 transition-colors">Inventory</span> /
                    <span class="hover:text-slate-700 transition-colors font-semibold">Stok Gudang</span>
                </p>
                <h1 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Posisi Stok</h1>
                <p class="text-xs md:text-sm text-slate-500 mt-1">Pantau persediaan bahan mentah, pool produksi, dan
                    barang jadi</p>
            </div>
        </div>

        <!-- Notifikasi Galat -->
        <div v-if="galat"
            class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 font-medium flex items-start gap-3 shadow-sm">
            <i class="pi pi-exclamation-triangle mt-0.5"></i>
            <span>{{ galat }}</span>
        </div>

        <!-- Area Konten Utama -->
        <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full min-h-[400px]">

            <!-- Header Kartu & Tab Filter Lapis -->
            <div
                class="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4 mb-6 pb-4 border-b border-slate-100">
                <div>
                    <h3 class="text-sm font-bold text-slate-800">Daftar Persediaan</h3>
                    <p class="text-xs text-slate-500">Pilih lapisan stok di bawah ini</p>
                </div>

                <!-- Tab Lapis Stok -->
                <div class="flex bg-slate-50 p-1 rounded-xl w-full xl:w-auto overflow-x-auto custom-scrollbar">
                    <button v-for="l in LAPIS" :key="l.nilai" @click="pilihLapis(l.nilai)"
                        :class="lapis === l.nilai ? 'bg-white text-slate-800 shadow-[0_2px_8px_rgba(0,0,0,0.04)] font-bold' : 'text-slate-500 hover:text-slate-700'"
                        class="px-6 py-2 text-xs md:text-sm rounded-lg transition-all whitespace-nowrap capitalize flex-1 text-center xl:flex-none">
                        {{ l.label }}
                    </button>
                </div>
            </div>

            <!-- State Loading -->
            <div v-if="sedangProses" class="flex flex-col items-center justify-center py-12 text-center">
                <i class="pi pi-spin pi-spinner text-slate-300 text-2xl mb-3"></i>
                <p class="text-xs text-slate-500">Memuat data stok...</p>
            </div>

            <!-- State Kosong -->
            <div v-else-if="daftarStok.length === 0"
                class="flex flex-col items-center justify-center py-12 text-center">
                <div
                    class="w-12 h-12 bg-slate-50 rounded-full flex items-center justify-center mb-3 border border-slate-100">
                    <i class="pi pi-box text-slate-300 text-xl"></i>
                </div>
                <h4 class="text-sm font-bold text-slate-800 mb-1">Stok Kosong</h4>
                <p class="text-xs text-slate-500">Tidak ada stok di lapis {{ lapis }} saat ini.</p>
            </div>

            <!-- Tabel Data (Desktop) -->
            <div v-else class="hidden md:block overflow-x-auto custom-scrollbar">
                <table class="w-full text-left text-sm table-fixed">
                    <thead class="text-slate-500 bg-slate-50/50">
                        <tr>
                            <th class="py-3 px-4 font-semibold rounded-tl-xl w-[35%]">Produk</th>
                            <th class="py-3 px-4 font-semibold w-[25%]">Grup Bahan</th>
                            <th class="py-3 px-4 font-semibold w-[20%]">Tangki</th>
                            <th class="py-3 px-4 font-semibold text-right rounded-tr-xl w-[20%]">Qty</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="s in daftarStok" :key="s.id" @click="bukaDetail(s.id)"
                            class="border-b border-slate-100 hover:bg-slate-50/50 transition-colors cursor-pointer group">
                            <td
                                class="py-3.5 px-4 font-bold text-slate-800 group-hover:text-blue-600 transition-colors">
                                {{ s.produk_kode }}
                            </td>
                            <td class="py-3.5 px-4 text-slate-600">
                                <span
                                    class="bg-slate-100 text-slate-600 px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wide uppercase">
                                    {{ s.grup_bahan_kode }}
                                </span>
                            </td>
                            <td class="py-3.5 px-4 text-slate-500 font-medium">
                                <template v-if="s.tangki_kode">
                                    <i class="pi pi-database text-[10px] mr-1 text-slate-400"></i> {{ s.tangki_kode
                                    }}
                                </template>
                                <span v-else>—</span>
                            </td>
                            <td class="py-3.5 px-4 text-right font-black text-slate-800 text-base">
                                {{ angka(s.qty, 3) }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Tampilan Card (Mobile) -->
            <div v-if="!sedangProses && daftarStok.length > 0" class="md:hidden flex flex-col gap-3">
                <div v-for="s in daftarStok" :key="s.id" @click="bukaDetail(s.id)"
                    class="bg-white border border-slate-100 rounded-xl p-4 shadow-sm active:scale-[0.98] transition-transform cursor-pointer">
                    <div class="flex justify-between items-start mb-3 border-b border-slate-50 pb-3">
                        <div class="font-bold text-slate-800 text-sm">{{ s.produk_kode }}</div>
                        <div class="text-right">
                            <div class="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-0.5">Total Qty
                            </div>
                            <div class="font-black text-slate-800 text-sm">{{ angka(s.qty, 3) }}</div>
                        </div>
                    </div>
                    <div class="text-xs text-slate-600 flex justify-between items-center">
                        <span class="bg-slate-50 px-2 py-1 rounded font-medium">{{ s.grup_bahan_kode }}</span>
                        <span class="text-slate-400 flex items-center gap-1">
                            <i class="pi pi-database text-[10px]"></i>
                            {{ s.tangki_kode ?? 'Tanpa Tangki' }}
                        </span>
                    </div>
                </div>
            </div>

        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStock } from '../composables/useStock'
import { angka } from '@/utils/format'

const LAPIS = [
    { nilai: 'RAW', label: 'Bahan Mentah (RAW)' },
    { nilai: 'POOL', label: 'Pool Produksi (POOL)' },
    { nilai: 'JADI', label: 'Barang Jadi (JADI)' },
]

const router = useRouter()
const { daftarStok, sedangProses, galat, muatStok } = useStock()

const lapis = ref('RAW')

const pilihLapis = (l) => {
    lapis.value = l
    muatStok({ lapis: l })
}

const bukaDetail = (id) => {
    router.push(`/inventory/stok/${id}`)
}

onMounted(() => {
    muatStok({ lapis: lapis.value })
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