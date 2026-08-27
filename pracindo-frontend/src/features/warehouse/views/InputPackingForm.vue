<!-- src/features/warehouse/views/InputPackingForm.vue -->
<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- STATE 1: BERHASIL -->
        <template v-if="hasilEksekusi">
            <section class="bg-white border border-emerald-200 rounded-[24px] p-6 md:p-8 shadow-sm w-full">
                <div class="flex items-center gap-3 mb-2">
                    <div class="w-10 h-10 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center">
                        <i class="pi pi-check text-xl"></i>
                    </div>
                    <h1 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Klaim WIP Berhasil</h1>
                </div>
                <p class="text-sm text-slate-600 mb-6 ml-13">Finished Goods berhasil diklaim dan nilai COGS telah diabsorpsi.</p>

                <div class="bg-slate-50 border border-slate-100 rounded-xl p-4 mb-6 ml-0 md:ml-13 flex flex-col gap-2">
                    <div>
                        <p class="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">Nomor Packing</p>
                        <p class="text-lg font-black text-slate-800">{{ hasilEksekusi.nomor }}</p>
                    </div>
                    <div class="grid grid-cols-2 gap-4 mt-2 border-t border-slate-200 pt-3">
                        <div>
                            <p class="text-[10px] text-slate-400 font-bold uppercase mb-1">Total Volume</p>
                            <p class="text-sm font-bold text-blue-600">{{ angka(hasilEksekusi.qty_kg, 3) }} Kg</p>
                        </div>
                        <div>
                            <p class="text-[10px] text-slate-400 font-bold uppercase mb-1">Absorbed COGS</p>
                            <p class="text-sm font-bold text-emerald-600">Rp {{ angka(hasilEksekusi.nilai_hpp) }}</p>
                        </div>
                    </div>
                </div>

                <div class="flex flex-col sm:flex-row gap-3 ml-0 md:ml-13">
                    <button type="button" @click="resetForm"
                        class="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-bold rounded-xl transition-colors shadow-md text-center">
                        Input Packing Lain
                    </button>
                    <button type="button" @click="$emit('tutup')"
                        class="px-6 py-2.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-bold rounded-xl transition-colors text-center">
                        Tutup
                    </button>
                </div>
            </section>
        </template>

        <!-- STATE 2: FORM INPUT -->
        <form v-else @submit.prevent="submit" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Panel Kiri: Form Input -->
            <div class="lg:col-span-2 space-y-6">
                <!-- Notifikasi Error Global -->
                <div v-if="galat" class="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 font-medium flex items-start gap-3 shadow-sm">
                    <i class="pi pi-exclamation-triangle mt-0.5"></i>
                    <span>{{ galat }}</span>
                </div>

                <!-- Bagian 1: Identifikasi Sumber -->
                <section class="bg-white border border-slate-200 rounded-[24px] p-5 md:p-6 shadow-sm">
                    <h3 class="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 border-b border-slate-100 pb-2">1. Identifikasi WIP</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="flex flex-col gap-2">
                            <label class="text-xs font-bold text-slate-500 uppercase">Target Legal Entity</label>
                            <select v-model="form.entitas_id" required class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-slate-800 text-slate-800">
                                <option value="" disabled>Pilih Entitas Tujuan...</option>
                                <option v-for="ent in daftarEntitas" :key="ent.id" :value="ent.id">{{ ent.nama }}</option>
                            </select>
                        </div>
                        <div class="flex flex-col gap-2">
                            <label class="text-xs font-bold text-slate-500 uppercase">WIP Batch ID</label>
                            <select v-model="form.batch_id" required class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-slate-800 text-slate-800">
                                <option value="" disabled>Pilih Batch Tersedia...</option>
                                <option v-for="b in daftarBatch" :key="b.id" :value="b.id">
                                    {{ b.nomor }} - {{ b.nama_hasil }} (Sisa: {{ angka(b.sisa_qty, 3) }} Kg)
                                </option>
                            </select>
                        </div>
                    </div>
                </section>

                <!-- Bagian 2: Aset Kemasan & Volume -->
                <section class="bg-white border border-slate-200 rounded-[24px] p-5 md:p-6 shadow-sm">
                    <h3 class="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 border-b border-slate-100 pb-2">2. Penggunaan Aset Kemasan</h3>

                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <div class="flex flex-col gap-2">
                            <label class="text-xs font-bold text-slate-500 uppercase">Aset Kemasan Utama</label>
                            <select v-model="form.kemasan_id" required class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-slate-800 text-slate-800">
                                <option value="" disabled>Pilih Kemasan...</option>
                                <option v-for="k in daftarKemasan" :key="k.id" :value="k.id">
                                    {{ k.nama }} ({{ angka(k.bobot_kg, 2) }} Kg/Unit)
                                </option>
                            </select>
                        </div>
                        <div class="flex flex-col gap-2">
                            <label class="text-xs font-bold text-slate-500 uppercase">Total Unit</label>
                            <div class="relative">
                                <input v-model.number="form.total_unit" type="number" min="1" step="1" required placeholder="0" class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-right font-bold focus:ring-2 focus:ring-slate-800 text-slate-800" />
                                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-xs">Pcs/Koli</span>
                            </div>
                        </div>
                        <div class="flex flex-col gap-2">
                            <label class="text-xs font-bold text-slate-500 uppercase">Isi per Unit (Kg)</label>
                            <div class="relative">
                                <input v-model.number="form.isi_per_unit" type="number" min="0" step="0.001" required placeholder="0.000" class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-right font-bold focus:ring-2 focus:ring-slate-800 text-slate-800" />
                                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-xs">Kg</span>
                            </div>
                        </div>
                    </div>

                    <!-- Input Total Qty (Hybrid: Auto + Editable) -->
                    <div class="p-4 bg-blue-50 border border-blue-100 rounded-xl mt-4">
                        <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
                            <div>
                                <span class="text-xs font-bold text-blue-800 uppercase tracking-wider block mb-1">Total Volume Yield (Kg)</span>
                                <span class="text-[10px] text-blue-600 block">Dihitung otomatis. Edit jika timbangan aktual berbeda.</span>
                            </div>
                            <div class="relative w-full md:w-48">
                                <input v-model.number="form.qty_kg" type="number" min="0" step="0.001" required placeholder="0.000"
                                    class="w-full px-4 py-2.5 bg-white border border-blue-200 rounded-xl text-lg text-right font-black focus:ring-2 focus:ring-blue-500 text-blue-700 transition-colors" />
                                <span class="absolute left-3 top-1/2 -translate-y-1/2 text-blue-300 text-sm"><i class="pi pi-pencil"></i></span>
                            </div>
                        </div>
                    </div>
                </section>
            </div>

            <!-- Panel Kanan: Telemetri & Valuasi -->
            <div class="space-y-6">
                <div class="bg-slate-900 border border-slate-800 rounded-[24px] p-6 shadow-xl relative overflow-hidden h-full flex flex-col">
                    <!-- Icon Latar Belakang -->
                    <div class="absolute -right-6 -bottom-6 text-slate-800 opacity-50 pointer-events-none">
                        <i class="pi pi-receipt" style="font-size: 8rem;"></i>
                    </div>

                    <h3 class="text-xs font-bold text-amber-500 uppercase tracking-widest mb-6 border-b border-slate-700 pb-2 relative z-10">Valuasi HPP / COGS</h3>

                    <div class="space-y-4 relative z-10 flex-1">
                        <!-- Peringatan Kapasitas / Error Pratinjau -->
                        <div v-if="pratinjau.pesan && !pratinjau.valid" class="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-400 font-medium">
                            <i class="pi pi-times-circle mr-1"></i> {{ pratinjau.pesan }}
                        </div>
                        <div v-else-if="pratinjau.menghabiskan" class="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-xs text-amber-400 font-medium">
                            <i class="pi pi-info-circle mr-1"></i> Penarikan ini menghabiskan sisa batch.
                        </div>

                        <!-- Baris Data Evaluasi -->
                        <div class="flex justify-between items-center border-b border-slate-700 pb-3 mt-4">
                            <span class="text-xs text-slate-400">Status Kalkulasi</span>
                            <span v-if="pratinjau.valid" class="text-xs font-bold text-emerald-400 flex items-center gap-1"><i class="pi pi-check-circle"></i> Valid</span>
                            <span v-else class="text-xs font-bold text-slate-500">Menunggu Input</span>
                        </div>

                        <div class="flex justify-between items-center border-b border-slate-700 pb-3 mt-4">
                            <span class="text-xs text-slate-400">Estimasi HPP / Kg</span>
                            <span class="text-sm font-mono text-slate-200">Rp {{ angka(pratinjau.harga_per_kg) || '0' }}</span>
                        </div>

                        <div class="pt-4">
                            <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Total Nilai Absorpsi</span>
                            <span class="text-3xl font-black text-white block">Rp {{ pratinjau.valid ? angka(pratinjau.nilai_tagihan) : '0' }}</span>
                        </div>
                    </div>

                    <div class="mt-8 relative z-10">
                        <button type="submit" :disabled="!isFormValid || sedangProses"
                            class="w-full px-6 py-3.5 bg-amber-500 hover:bg-amber-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-900 text-sm font-black rounded-xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed transform hover:-translate-y-0.5">
                            <i v-if="sedangProses" class="pi pi-spin pi-spinner"></i>
                            <i v-else class="pi pi-bolt"></i>
                            {{ sedangProses ? 'Mengeksekusi...' : 'Klaim & Eksekusi HPP' }}
                        </button>
                        <button type="button" @click="$emit('tutup')" class="w-full mt-3 text-xs text-slate-400 hover:text-white font-medium transition-colors">
                            Batal & Kembali
                        </button>
                    </div>
                </div>
            </div>
        </form>
    </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { usePacking } from '../composables/usePacking'
import { angka } from '@/utils/format'

const emit = defineEmits(['tutup'])
const {
    daftarEntitas, daftarKemasan, daftarBatch, pratinjau, sedangProses, galat,
    muatMasterData, cekPratinjau, simpanPacking
} = usePacking()

// State Data Form
const form = reactive({
    entitas_id: '',
    batch_id: '',
    kemasan_id: '',
    total_unit: null,
    isi_per_unit: null,
    qty_kg: 0
})

const hasilEksekusi = ref(null)

// 1. WATCHER KEMASAN: Ambil default berat kemasan dari database untuk sugesti 'Isi per Unit'
watch(() => form.kemasan_id, (kId) => {
    if (kId) {
        const kemasanTerpilih = daftarKemasan.value.find(k => k.id === kId)
        if (kemasanTerpilih && kemasanTerpilih.bobot_kg) {
            form.isi_per_unit = Number(kemasanTerpilih.bobot_kg)
        }
    }
})

// 2. WATCHER HYBRID: Kalkulasi otomatis Qty(Kg)
watch([() => form.total_unit, () => form.isi_per_unit], ([unit, isi]) => {
    if (unit > 0 && isi > 0) {
        form.qty_kg = Number((unit * isi).toFixed(3))
    }
})

// 3. WATCHER PRATINJAU: Panggil API Backend saat Batch atau Qty(Kg) berubah
let debounceTimer
watch([() => form.batch_id, () => form.qty_kg], ([batchId, qtyKg]) => {
    clearTimeout(debounceTimer)
    if (!batchId || qtyKg <= 0) {
        pratinjau.value.valid = false
        return
    }
    // Tunda hit API 500ms agar tidak spam server saat user mengetik
    debounceTimer = setTimeout(() => {
        cekPratinjau(batchId, qtyKg)
    }, 500)
})

const isFormValid = computed(() => {
    return form.entitas_id && form.batch_id && form.kemasan_id && form.qty_kg > 0 && pratinjau.value.valid
})

const submit = async () => {
    if (!isFormValid.value) return
    const res = await simpanPacking({
        entitas: form.entitas_id,
        batch: form.batch_id,
        kemasan: form.kemasan_id,
        total_unit: form.total_unit,
        qty_kg: form.qty_kg
    })

    if (res.success) {
        hasilEksekusi.value = res.data
    }
}

const resetForm = () => {
    form.batch_id = ''
    form.kemasan_id = ''
    form.total_unit = null
    form.isi_per_unit = null
    form.qty_kg = 0
    hasilEksekusi.value = null
    // Refresh master data untuk memperbarui sisa qty batch yang baru saja disedot
    muatMasterData()
}

onMounted(() => {
    muatMasterData()
})
</script>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.3s ease-out forwards;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
