<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- Header Halaman -->
        <div class="mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <span class="hover:text-slate-700 transition-colors">Distribution</span> /
                    <span class="text-slate-600 font-semibold">Status Armada</span>
                </p>
                <h1 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Pantau Armada</h1>
                <p class="text-xs md:text-sm text-slate-500 mt-1">Ketersediaan truk dan posisi supir saat ini.</p>
            </div>
            
            <button class="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-bold rounded-xl transition-colors shadow-md flex items-center gap-2 w-full md:w-auto justify-center">
                <i class="pi pi-plus text-xs"></i>
                <span>Registrasi Armada</span>
            </button>
        </div>

        <!-- Grid Kartu Armada -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            <div v-for="armada in armadaDummy" :key="armada.id" 
                class="bg-white border border-slate-200 rounded-[24px] p-5 shadow-sm transition-all hover:shadow-md flex flex-col justify-between"
                :class="{ 'opacity-70 bg-slate-50': armada.status === 'PERBAIKAN' }">
                
                <div>
                    <div class="flex justify-between items-center mb-4">
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center border border-slate-200">
                                <i class="pi pi-truck text-slate-500 text-lg"></i>
                            </div>
                            <div>
                                <span class="font-black text-slate-800 text-lg block">{{ armada.nopol }}</span>
                                <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{{ armada.jenis }}</span>
                            </div>
                        </div>
                        <span class="px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wide uppercase border" :class="badgeWarna(armada.status)">
                            {{ armada.status }}
                        </span>
                    </div>

                    <div class="p-3 bg-slate-50 border border-slate-100 rounded-xl mb-4 flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center">
                            <i class="pi pi-user text-slate-500 text-sm"></i>
                        </div>
                        <div>
                            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Supir Utama</span>
                            <p class="text-sm font-bold text-slate-800 m-0">{{ armada.supir ?? 'Belum Ditugaskan' }}</p>
                        </div>
                    </div>
                </div>

                <div class="flex justify-between items-center pt-3 border-t border-slate-100">
                    <div class="flex flex-col">
                        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Kapasitas Maks</span>
                        <span class="text-sm font-black text-slate-700">{{ armada.kapasitas }} Ton</span>
                    </div>
                    <button class="text-blue-600 hover:text-blue-800 text-sm font-bold transition-colors">
                        Detail <i class="pi pi-arrow-right text-xs ml-1"></i>
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'

const armadaDummy = ref([
    { id: 1, nopol: 'L 8821 XA', jenis: 'Fuso Engkel', supir: 'Ahmad M.', kapasitas: 8, status: 'DALAM PENGIRIMAN' },
    { id: 2, nopol: 'B 9182 TXY', jenis: 'Truk Tronton', supir: 'Budi Santoso', kapasitas: 20, status: 'TERSEDIA' },
    { id: 3, nopol: 'D 1234 CD', jenis: 'Truk CDD', supir: 'Jajang', kapasitas: 4, status: 'DALAM PENGIRIMAN' },
    { id: 4, nopol: 'N 4321 XY', jenis: 'Truk Box', supir: null, kapasitas: 5, status: 'PERBAIKAN' }
])

const badgeWarna = (status) => {
    switch(status) {
        case 'TERSEDIA': return 'bg-emerald-50 text-emerald-600 border-emerald-200'
        case 'DALAM PENGIRIMAN': return 'bg-purple-50 text-purple-600 border-purple-200'
        case 'PERBAIKAN': return 'bg-rose-50 text-rose-600 border-rose-200'
        default: return 'bg-slate-50 text-slate-500 border-slate-200'
    }
}
</script>

<style scoped>
.animate-fade-in { animation: fadeIn 0.3s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>
