<!--
  features/inventory/views/TankMonitor.vue
  ==========================================
  Monitor tangki dengan desain kartu grid responsif berbasis Tailwind CSS.
-->
<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <div class="mb-6 flex justify-between items-end">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <span class="hover:text-slate-700 transition-colors">Inventory</span> /
                    <span class="hover:text-slate-700 transition-colors font-semibold">Monitor Tangki</span>
                </p>
                <h1 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Monitor Tangki</h1>
                <p class="text-xs md:text-sm text-slate-500 mt-1">Isi, kapasitas, dan produk yang sedang mengisi tiap
                    tangki</p>
            </div>
        </div>

        <!-- Notifikasi Galat -->
        <div v-if="galat"
            class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 font-medium flex items-start gap-3 shadow-sm">
            <i class="pi pi-exclamation-triangle mt-0.5"></i>
            <span>{{ galat }}</span>
        </div>

        <!-- Grid Kartu Tangki -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            <div v-for="t in daftarTangki" :key="t.id"
                class="bg-white border border-slate-200 rounded-[24px] p-5 shadow-sm transition-all hover:shadow-md flex flex-col justify-between"
                :class="{ 'opacity-60 bg-slate-50': !t.aktif }">

                <div>
                    <div class="flex justify-between items-center mb-2">
                        <span class="font-black text-slate-800 text-base">{{ t.kode }}</span>
                        <span
                            class="text-[10px] font-bold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-md uppercase tracking-wider">{{
                                t.grup_bahan_kode }}</span>
                    </div>
                    <p class="text-xs text-slate-400 font-medium mb-3">{{ t.nama }}</p>

                    <div class="p-3 bg-slate-50 border border-slate-100 rounded-xl mb-4">
                        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Produk
                            Terisi</span>
                        <p class="text-sm font-bold text-slate-800 m-0">{{ t.produk_terisi_kode ?? 'Kosong' }}
                        </p>
                    </div>
                </div>

                <div>
                    <div class="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden mb-2">
                        <div class="h-full transition-all duration-500 rounded-full"
                            :style="{ width: `${Math.min(100, t.persen_terisi)}%` }"
                            :class="t.persen_terisi >= 90 ? 'bg-amber-500' : 'bg-emerald-500'"></div>
                    </div>

                    <div class="flex justify-between items-center text-xs text-slate-600 mb-1">
                        <span class="font-medium">{{ angka(t.isi_kg, 1) }} / {{ angka(t.kapasitas_kg, 1) }} kg</span>
                        <span class="font-black text-slate-800">{{ angka(t.persen_terisi, 1) }}%</span>
                    </div>
                    <p class="text-[11px] text-slate-400 mt-1 m-0">Ruang kosong: {{ angka(t.ruang_kosong_kg, 1) }}
                        kg</p>
                </div>
            </div>
        </div>

        <!-- State Kosong -->
        <div v-if="!sedangProses && daftarTangki.length === 0"
            class="flex flex-col items-center justify-center py-16 text-center bg-white border border-slate-200 rounded-[24px]">
            <div
                class="w-12 h-12 bg-slate-50 rounded-full flex items-center justify-center mb-3 border border-slate-100">
                <i class="pi pi-database text-slate-300 text-xl"></i>
            </div>
            <h4 class="text-sm font-bold text-slate-800 mb-1">Tidak ada data tangki</h4>
            <p class="text-xs text-slate-500">Sistem belum mencatat konfigurasi tangki aktif.</p>
        </div>
    </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useTank } from '../composables/useTank'
import { angka } from '@/utils/format'

const { daftarTangki, sedangProses, galat, muatTangki } = useTank()

onMounted(() => muatTangki())
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
</style>