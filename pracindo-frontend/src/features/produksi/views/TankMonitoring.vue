<template>
    <div class="animate-fade-in">
        <header class="mb-6 flex justify-between items-end">
            <div>
                <h1 class="text-2xl font-black text-slate-800">Monitor Tangki WIP</h1>
                <p class="text-sm text-slate-500 mt-1">Pantau kapasitas dan isi fisik tangki secara *real-time*.</p>
            </div>
            <button @click="muatDataTangki"
                class="px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-600 hover:bg-slate-50 shadow-sm flex items-center gap-2">
                <i class="pi pi-refresh" :class="{ 'pi-spin': memuat }"></i> Segarkan
            </button>
        </header>

        <!-- Penanganan Galat API -->
        <div v-if="galatServer" class="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r">
            <strong>Gagal memuat data:</strong> {{ galatServer.message || galatServer }}
        </div>

        <div v-if="memuat" class="py-12 flex justify-center text-slate-400">
            <i class="pi pi-spin pi-spinner text-3xl"></i>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            <div v-for="t in listTangki" :key="t.id"
                class="bg-white rounded-[24px] border border-slate-200 p-6 shadow-sm flex gap-6">
                <!-- Visual Silinder -->
                <div class="w-16 h-40 bg-slate-100 rounded-full border-4 border-slate-200 relative overflow-hidden flex-shrink-0 flex flex-col justify-end">
                    <div class="w-full bg-blue-500 transition-all duration-1000 ease-out relative"
                        :style="{ height: `${hitungPersentase(t.terisi_kg, t.kapasitas_kg)}%` }">
                        <div class="absolute top-0 left-0 right-0 h-1 bg-white/30"></div>
                    </div>
                </div>

                <!-- Informasi -->
                <div class="flex-1 flex flex-col justify-between">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="px-2 py-0.5 bg-indigo-50 text-indigo-700 font-black text-[10px] rounded uppercase tracking-wider border border-indigo-100">
                                {{ t.kode }}
                            </span>
                            <span v-if="t.aktif" class="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
                        </div>
                        <h3 class="font-bold text-slate-800 text-lg leading-tight">{{ t.nama }}</h3>
                        <p class="text-[10px] text-slate-400 mt-1 uppercase font-semibold">Pool: {{ t.grup_bahan_kode || 'TIDAK ADA' }}</p>
                    </div>

                    <div class="mt-4">
                        <div class="flex justify-between text-xs font-bold mb-1">
                            <span class="text-slate-500">Volume Cairan</span>
                            <span class="text-blue-600">{{ tampil(t.terisi_kg) }} / {{ tampil(t.kapasitas_kg) }} KG</span>
                        </div>
                        <div class="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                            <div class="bg-blue-500 h-full rounded-full transition-all"
                                :style="{ width: `${hitungPersentase(t.terisi_kg, t.kapasitas_kg)}%` }">
                            </div>
                        </div>
                        <p class="text-[10px] text-slate-400 mt-1.5 text-right">
                            Sisa Ruang: <b>{{ tampil(t.ruang_kosong_kg) }} KG</b>
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- Kondisi Kosong -->
            <div v-if="listTangki.length === 0" class="col-span-full py-12 text-center text-slate-500 bg-slate-50 rounded-2xl border border-dashed border-slate-300">
                Belum ada data tangki WIP yang terdaftar atau aktif.
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiGetList } from '@/utils/apiClient' // Gunakan API Client kita

const memuat = ref(false)
const listTangki = ref([])
const galatServer = ref(null)

const angka = (v) => Number(v) || 0
const tampil = (n) => angka(n).toLocaleString('id-ID', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
const hitungPersentase = (terisi, kapasitas) => {
    if (kapasitas <= 0) return 0
    return Math.min((terisi / kapasitas) * 100, 100)
}

const muatDataTangki = async () => {
    memuat.value = true
    galatServer.value = null
    try {
        // Panggilan API Asli ke endpoint backend!
        listTangki.value = await apiGetList('/api/v1/inventory/tangki/')
    } catch (error) {
        console.error("Gagal memuat tangki:", error)
        galatServer.value = error
    } finally {
        memuat.value = false
    }
}

onMounted(() => muatDataTangki())
</script>

<style scoped>
.animate-fade-in { animation: fadeIn 0.3s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>