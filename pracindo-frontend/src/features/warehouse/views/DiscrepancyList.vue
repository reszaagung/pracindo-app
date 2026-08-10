<!--
  features/warehouse/views/DiscrepancyList.vue
  ==============================================
  Daftar laporan selisih dengan desain Tailwind CSS modern.
-->
<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- Header -->
        <div class="mb-4 md:mb-6 flex justify-between items-end">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <span class="hover:text-slate-700 transition-colors">Warehouse</span> /
                    <span class="hover:text-slate-700 transition-colors font-semibold">Laporan Selisih</span>
                </p>
                <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Laporan Selisih</h2>
                <p class="text-xs md:text-sm text-slate-500 mt-1">Selisih berat, kekurangan kirim, dan barang ditolak
                </p>
            </div>
        </div>

        <!-- Notifikasi Error -->
        <div v-if="galat"
            class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 font-medium flex items-start gap-3 shadow-sm">
            <i class="pi pi-exclamation-triangle mt-0.5"></i>
            <span>{{ galat }}</span>
        </div>

        <!-- Area Filter & Tabel -->
        <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full min-h-[400px]">

            <!-- Header Kartu & Tab Filter -->
            <div
                class="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4 mb-6 pb-4 border-b border-slate-100">
                <div>
                    <h3 class="text-sm font-bold text-slate-800">Daftar Klaim</h3>
                    <p class="text-xs text-slate-500">Filter berdasarkan status</p>
                </div>

                <!-- Filter Status (Chips) -->
                <div class="flex bg-slate-50 p-1 rounded-xl w-full md:w-auto overflow-x-auto custom-scrollbar">
                    <button v-for="opt in SARINGAN" :key="opt.nilai" @click="saring = opt.nilai"
                        :class="saring === opt.nilai ? 'bg-white text-slate-800 shadow-[0_2px_8px_rgba(0,0,0,0.04)] font-bold' : 'text-slate-500 hover:text-slate-700'"
                        class="px-4 py-2 text-xs rounded-lg transition-all whitespace-nowrap capitalize flex-1 text-center md:flex-none">
                        {{ opt.label }}
                    </button>
                </div>
            </div>

            <!-- Loading State -->
            <div v-if="sedangProses" class="flex flex-col items-center justify-center py-12 text-center">
                <i class="pi pi-spin pi-spinner text-slate-300 text-2xl mb-3"></i>
                <p class="text-xs text-slate-500">Memproses data...</p>
            </div>

            <!-- Empty State -->
            <div v-else-if="tampil.length === 0" class="flex flex-col items-center justify-center py-12 text-center">
                <div
                    class="w-12 h-12 bg-slate-50 rounded-full flex items-center justify-center mb-3 border border-slate-100">
                    <i class="pi pi-check-circle text-emerald-400 text-xl"></i>
                </div>
                <h4 class="text-sm font-bold text-slate-800 mb-1">Tidak ada laporan selisih</h4>
                <p class="text-xs text-slate-500">Gudang aman. Kriteria yang Anda cari tidak ditemukan.</p>
            </div>

            <!-- Tampilan Tabel (Desktop) -->
            <div v-else class="hidden md:block overflow-x-auto custom-scrollbar">
                <table class="w-full text-left text-sm table-fixed">
                    <thead class="text-slate-500 bg-slate-50/50">
                        <tr>
                            <th class="py-3 px-4 font-semibold rounded-tl-xl w-[20%]">Nomor Selisih</th>
                            <th class="py-3 px-4 font-semibold w-[25%]">Jenis Laporan</th>
                            <th class="py-3 px-4 font-semibold w-[20%] text-right">Qty Selisih</th>
                            <th class="py-3 px-4 font-semibold w-[20%] text-center">Status</th>
                            <th class="py-3 px-4 font-semibold w-[15%] text-center rounded-tr-xl">Aksi</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="s in tampil" :key="s.id"
                            class="border-b border-slate-100 hover:bg-slate-50/50 transition-colors">
                            <td class="py-3 px-4 font-bold text-slate-800">{{ s.nomor }}</td>
                            <td class="py-3 px-4 text-slate-600">{{ s.jenis }}</td>
                            <td class="py-3 px-4 text-rose-600 font-semibold text-right">{{ angka(s.qty_selisih, 3) }}
                            </td>
                            <td class="py-3 px-4 text-center">
                                <span :class="badgeColor(s.status)"
                                    class="px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wide uppercase inline-flex items-center gap-1 border">
                                    {{ s.status }}
                                </span>
                            </td>
                            <td class="py-3 px-4 text-center">
                                <button v-if="s.status === 'DIBUKA'" :disabled="sedangProses" @click="ajukanKlaim(s)"
                                    class="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-[10px] font-bold rounded-lg transition-colors disabled:opacity-50 flex items-center gap-1 mx-auto">
                                    <i class="pi pi-send text-[10px]"></i> Ajukan
                                </button>
                                <span v-else class="text-[10px] text-slate-400 font-medium">-</span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Tampilan Card (Mobile) -->
            <div v-if="!sedangProses && tampil.length > 0" class="md:hidden flex flex-col gap-3">
                <div v-for="s in tampil" :key="s.id"
                    class="bg-white border border-slate-100 rounded-xl p-4 shadow-sm relative">
                    <div class="flex justify-between items-start mb-2 border-b border-slate-50 pb-2">
                        <div class="font-bold text-slate-800 text-sm">{{ s.nomor }}</div>
                        <span :class="badgeColor(s.status)"
                            class="px-2 py-0.5 rounded text-[9px] font-bold uppercase border">
                            {{ s.status }}
                        </span>
                    </div>
                    <div class="text-xs text-slate-600 flex flex-col gap-1.5 mb-3">
                        <div class="flex justify-between items-center">
                            <span class="text-slate-400 font-semibold">Jenis Laporan</span>
                            <span class="font-medium text-slate-700">{{ s.jenis }}</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-slate-400 font-semibold">Qty Selisih</span>
                            <span class="font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded">{{ angka(s.qty_selisih,
                                3) }}</span>
                        </div>
                    </div>
                    <button v-if="s.status === 'DIBUKA'" :disabled="sedangProses" @click="ajukanKlaim(s)"
                        class="w-full py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
                        <i class="pi pi-send text-[10px]"></i> Ajukan ke Suplier
                    </button>
                </div>
            </div>

        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useDiscrepancy } from '../composables/useDiscrepancy'
import { useToast } from '@/composables/useToast'
import { angka } from '@/utils/format'

const SARINGAN = [
    { nilai: 'semua', label: 'Semua' },
    { nilai: 'DIBUKA', label: 'Dibuka' },
    { nilai: 'DIAJUKAN', label: 'Diajukan' },
    { nilai: 'DISELESAIKAN', label: 'Diselesaikan' },
    { nilai: 'DITUTUP', label: 'Ditutup' },
]

const { daftarSelisih, sedangProses, galat, muatSelisih, ajukan } = useDiscrepancy()
const toast = useToast()
const saring = ref('semua')

const tampil = computed(() => saring.value === 'semua'
    ? daftarSelisih.value
    : daftarSelisih.value.filter(s => s.status === saring.value)
)

const badgeColor = (status) => {
    const st = String(status).toUpperCase()
    if (st === 'DIBUKA') return 'bg-amber-50 text-amber-600 border-amber-200'
    if (st === 'DIAJUKAN' || st === 'DISEPAKATI') return 'bg-blue-50 text-blue-600 border-blue-200'
    if (st === 'DISELESAIKAN') return 'bg-emerald-50 text-emerald-600 border-emerald-200'
    return 'bg-slate-50 text-slate-500 border-slate-200' // Ditutup / Default
}

const ajukanKlaim = async (s) => {
    const hasil = await ajukan(s.id)
    if (hasil.success) {
        toast.success('Klaim diajukan ke suplier.')
        muatSelisih()
    } else {
        toast.error(hasil.message)
    }
}

onMounted(() => muatSelisih())
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