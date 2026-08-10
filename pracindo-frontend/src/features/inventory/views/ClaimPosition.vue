<!--
  features/inventory/views/ClaimPosition.vue
  ============================================
  Posisi klaim tiap entitas atas satu grup pool dengan desain Tailwind CSS.
-->
<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- Header Halaman -->
        <div class="mb-6 flex justify-between items-end">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <router-link to="/inventory" class="hover:text-slate-700 transition-colors">Stok</router-link>
                    <span class="mx-1">/</span>
                    <span class="text-slate-600 font-semibold">Posisi Klaim</span>
                </p>
                <h1 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Posisi Klaim — Grup {{ grup
                }}</h1>
                <p class="text-xs md:text-sm text-slate-500 mt-1">Status kepemilikan dan hutang/piutang entitas pada
                    pool produksi.</p>
            </div>
        </div>

        <!-- Notifikasi Galat -->
        <div v-if="galat"
            class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 font-medium flex items-start gap-3 shadow-sm">
            <i class="pi pi-exclamation-triangle mt-0.5"></i>
            <span>{{ galat }}</span>
        </div>

        <!-- Peringatan Ketidakseimbangan (Invariant Sistem) -->
        <div v-if="tidakSeimbang"
            class="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-700 font-medium flex items-start gap-3 shadow-sm">
            <i class="pi pi-shield mt-0.5 text-amber-500"></i>
            <div>
                <strong>Peringatan Sistem:</strong> Total posisi bersih ({{ angka(totalBersih, 3) }}) tidak sama dengan
                sisa nilai pool ({{ angka(totalNilaiPool, 3) }}).
                <span class="block mt-1 text-xs opacity-90">Ini indikasi masalah data di backend — bukan pembulatan,
                    jangan ditambal di sini.</span>
            </div>
        </div>

        <!-- Tabel Posisi Klaim -->
        <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full min-h-[300px]">
            <h3 class="text-sm font-bold text-slate-800 mb-4 pb-3 border-b border-slate-100 flex items-center gap-2">
                <i class="pi pi-chart-pie text-blue-600"></i> Detail Posisi Klaim Entitas
            </h3>

            <div class="overflow-x-auto custom-scrollbar">
                <table class="w-full text-left text-sm table-auto min-w-[40rem]">
                    <thead class="text-slate-500 bg-slate-50/50">
                        <tr>
                            <th class="py-3 px-4 font-semibold rounded-tl-xl w-[25%]">Entitas</th>
                            <th class="py-3 px-4 font-semibold text-right w-[15%]">Setor</th>
                            <th class="py-3 px-4 font-semibold text-right w-[15%]">Ambil</th>
                            <th class="py-3 px-4 font-semibold text-right w-[20%]">Bersih</th>
                            <th class="py-3 px-4 font-semibold text-center rounded-tr-xl w-[25%]">Posisi</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        <tr v-for="p in posisiKlaim" :key="p.entitas" class="hover:bg-slate-50/50 transition-colors">
                            <td class="py-3.5 px-4 font-bold text-slate-800">{{ p.entitas }}</td>
                            <td class="py-3.5 px-4 text-right text-emerald-600 font-medium">{{ angka(p.setor, 3)
                            }}</td>
                            <td class="py-3.5 px-4 text-right text-amber-600 font-medium">{{ angka(p.ambil, 3) }}:
                                6]</td>
                            <td class="py-3.5 px-4 text-right font-bold"
                                :class="{ 'text-rose-600': p.berhutang, 'text-slate-700': !p.berhutang }">
                                {{ angka(p.bersih, 3) }}
                            </td>
                            <td class="py-3.5 px-4 text-center">
                                <span
                                    class="px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wide uppercase border inline-flex items-center gap-1"
                                    :class="p.berhutang ? 'bg-rose-50 text-rose-600 border-rose-200' : 'bg-slate-50 text-slate-500 border-slate-200'">:
                                    6]
                                    <i class="pi" :class="p.berhutang ? 'pi-arrow-down-right' : 'pi-minus'"></i>
                                    {{ p.berhutang ? 'Berhutang' : 'Berpiutang' }}
                                </span>
                            </td>
                        </tr>
                    </tbody>
                    <tfoot v-if="posisiKlaim.length">
                        <tr class="bg-slate-50/50 border-t-2 border-slate-200">
                            <td class="py-3 px-4 font-black text-slate-800">Total</td>
                            <td class="py-3 px-4"></td>
                            <td class="py-3 px-4"></td>
                            <td class="py-3 px-4 text-right font-black text-slate-800">{{ angka(totalBersih, 3) }}:
                                6]</td>
                            <td class="py-3 px-4"></td>
                        </tr>
                    </tfoot>
                </table>
            </div>

            <!-- State Kosong -->
            <div v-if="!sedangProses && posisiKlaim.length === 0" class="py-12 text-center">
                <div
                    class="w-12 h-12 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-3 border border-slate-100">
                    <i class="pi pi-folder-open text-slate-300 text-xl"></i>
                </div>
                <p class="text-sm text-slate-500 font-medium">Belum ada posisi klaim di grup ini.</p>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useClaim } from '../composables/useClaim'
import { angka } from '@/utils/format'

const props = defineProps({ grup: { type: [String, Number], required: true } })

const { posisiKlaim, isiPool, sedangProses, galat, muatPosisiKlaim, muatIsiPool } = useClaim()

const totalBersih = computed(() =>
    posisiKlaim.value.reduce((s, p) => s + Number(p.bersih || 0), 0))
const totalNilaiPool = computed(() => Number(isiPool.value?.total_nilai || 0))

const tidakSeimbang = computed(() =>
    posisiKlaim.value.length > 0 && Math.abs(totalBersih.value - totalNilaiPool.value) > 0.01)

onMounted(() => {
    muatPosisiKlaim(props.grup)
    muatIsiPool(props.grup)
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