<script setup>
import {
    ref,
    reactive,
    computed,
    watch,
    onMounted,
    onBeforeUnmount
} from 'vue'
import Dropdown from 'primevue/dropdown'

import { usePacking } from '../composables/usePacking'
import { angka } from '@/utils/format'

const emit = defineEmits(['tutup'])

const {
    daftarEntitas,
    daftarKemasan,
    daftarBatch,
    daftarProduk,
    pratinjau,
    sedangProses,
    galat,
    muatMasterData,
    cekPratinjau,
    simpanPacking,
    ambilId
} = usePacking()

const initialFormState = () => ({
    entitas_id: '',
    jenis_sumber: 'MIXING',
    batch_id: '',
    produk_id: '',
    kemasan_id: '',
    total_unit: null,
    isi_per_unit: null,
    qty_kg: 0
})

const form = reactive(initialFormState())

const hasilEksekusi = ref(null)

const batchDifilter = computed(() => {
    if (!form.jenis_sumber) {
        return daftarBatch.value
    }

    return daftarBatch.value.filter(
        (b) => b.jenis === form.jenis_sumber
    )
})

const kemasanTerpilih = computed(() => {
    const kemasanId = ambilId(form.kemasan_id)

    return daftarKemasan.value.find(
        (k) => Number(k.id) === Number(kemasanId)
    )
})

const totalNilaiKemasan = computed(() => {
    const qtyUnit = Number(form.total_unit) || 0

    const hargaSatuan =
        Number(
            kemasanTerpilih.value?.harga_satuan_calculated ??
            kemasanTerpilih.value?.harga_satuan ??
            0
        ) || 0

    return qtyUnit * hargaSatuan
})

const nilaiHppWip = computed(() => {
    return Number(
        pratinjau.value?.nilai_tagihan
    ) || 0
})

const totalNilaiAbsorpsi = computed(() => {
    return (
        nilaiHppWip.value +
        totalNilaiKemasan.value
    )
})


watch(
    () => form.jenis_sumber,
    () => {
        form.batch_id = ''

        pratinjau.value = {
            valid: false,
            qty_kg: 0,
            harga_per_kg: 0,
            nilai_tagihan: 0,
            sisa_qty_batch: 0,
            menghabiskan: false,
            peringatan: [],
            pesan: ''
        }
    }
)

// ========================================
// CHANGE KEMASAN
// ========================================
watch(
    () => form.kemasan_id,
    (kId) => {
        const id = ambilId(kId)

        if (!id) {
            form.isi_per_unit = null
            return
        }

        const kemasan = daftarKemasan.value.find(
            (k) =>
                Number(k.id) === Number(id)
        )

        if (!kemasan) {
            return
        }

        const bobot =
            kemasan.bobot_kg ??
            kemasan.kapasitas_kg

        if (Number(bobot) > 0) {
            form.isi_per_unit = Number(bobot)
        }
    }
)

// ========================================
// HITUNG QTY KG
// ========================================
watch(
    [
        () => form.total_unit,
        () => form.isi_per_unit
    ],
    ([unit, isi]) => {
        const totalUnit = Number(unit) || 0
        const isiPerUnit = Number(isi) || 0

        if (
            totalUnit > 0 &&
            isiPerUnit > 0
        ) {
            form.qty_kg = Number(
                (
                    totalUnit *
                    isiPerUnit
                ).toFixed(3)
            )

            return
        }

        form.qty_kg = 0
    }
)

// ========================================
// PREVIEW DEBOUNCE
// ========================================
let debounceTimer = null

watch(
    [
        () => form.batch_id,
        () => form.qty_kg
    ],
    ([batchValue, qtyKg]) => {
        clearTimeout(debounceTimer)

        const batchId = ambilId(batchValue)
        const qty = Number(qtyKg) || 0

        if (!batchId || qty <= 0) {
            pratinjau.value.valid = false
            return
        }

        debounceTimer = setTimeout(() => {
            cekPratinjau(
                batchId,
                qty
            )
        }, 500)
    }
)

// ========================================
// PREVIEW HARUS SAMA DENGAN FORM
// ========================================
const previewSinkronDenganForm = computed(() => {
    const qtyPreview =
        Number(
            pratinjau.value?.qty_kg
        ) || 0

    const qtyForm =
        Number(form.qty_kg) || 0

    return (
        Math.abs(
            qtyPreview - qtyForm
        ) < 0.001
    )
})

// ========================================
// FORM VALID
// ========================================
const isFormValid = computed(() => {
    const entitasId =
        ambilId(form.entitas_id)

    const batchId =
        ambilId(form.batch_id)

    const produkId =
        ambilId(form.produk_id)

    const kemasanId =
        ambilId(form.kemasan_id)

    const totalUnit =
        Number(form.total_unit) || 0

    const qtyKg =
        Number(form.qty_kg) || 0

    return Boolean(
        entitasId &&
        batchId &&
        produkId &&
        kemasanId &&
        totalUnit > 0 &&
        qtyKg > 0 &&
        pratinjau.value.valid &&
        previewSinkronDenganForm.value
    )
})

// ========================================
// RESET PREVIEW
// ========================================
const resetPreview = () => {
    pratinjau.value = {
        valid: false,
        qty_kg: 0,
        harga_per_kg: 0,
        nilai_tagihan: 0,
        sisa_qty_batch: 0,
        menghabiskan: false,
        peringatan: [],
        pesan: ''
    }
}

// ========================================
// RESET FORM
// ========================================
const resetFormState = () => {
    Object.assign(
        form,
        initialFormState()
    )

    resetPreview()
}

// ========================================
// SUBMIT
// ========================================
const submit = async () => {
    if (!isFormValid.value) {
        return
    }

    const payload = {
        entitas: ambilId(form.entitas_id),
        batch: ambilId(form.batch_id),
        produk: ambilId(form.produk_id),
        // --- BARIS YANG DIPERBAIKI ---
        // Menarik ID string asli dari Master Kemasan, bukan dari Pool Kemasan
        kemasan: typeof form.kemasan_id === 'object' && form.kemasan_id !== null
            ? (form.kemasan_id.kemasan_id || form.kemasan_id.produk || form.kemasan_id.id || form.kemasan_id.kode)
            : form.kemasan_id,
        // -----------------------------
        total_unit: Number(form.total_unit),
        qty_kg: Number(form.qty_kg)
    }

    // Debug FINAL sebelum POST
    console.log(
        '[PACKING] Form:',
        {
            entitas: form.entitas_id,
            batch: form.batch_id,
            produk: form.produk_id,
            kemasan: form.kemasan_id,
            total_unit: form.total_unit,
            qty_kg: form.qty_kg
        }
    )

    console.log(
        '[PACKING] Payload FINAL:',
        payload
    )

    const res =
        await simpanPacking(payload)

    if (!res.success) {
        return
    }

    // Simpan hasil posting untuk ditampilkan
    hasilEksekusi.value = res.data

    // Bersihkan form
    resetFormState()

    // Refresh master data supaya stok / batch terbaru
    await muatMasterData()
}

// ========================================
// RESET FORM UTAMA
// ========================================
const resetForm = async () => {
    hasilEksekusi.value = null

    resetFormState()

    await muatMasterData()
}

// ========================================
// MOUNT
// ========================================
onMounted(() => {
    muatMasterData()
})

// ========================================
// CLEANUP TIMER
// ========================================
onBeforeUnmount(() => {
    clearTimeout(debounceTimer)
})
</script>

<template>
    <div class="flex flex-col w-full animate-fade-in relative">
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
                            <p class="text-sm font-bold text-emerald-600">Rp {{ angka(hasilEksekusi.cost_nom) }}</p>
                        </div>
                    </div>
                </div>

                <div class="flex flex-col sm:flex-row gap-3 ml-0 md:ml-13">
                    <button type="button" @click="resetForm" class="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-bold rounded-xl transition-colors shadow-md text-center">
                        Input Packing Lain
                    </button>
                    <button type="button" @click="$emit('tutup')" class="px-6 py-2.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-bold rounded-xl transition-colors text-center">
                        Tutup
                    </button>
                </div>
            </section>
        </template>

        <form v-else @submit.prevent="submit" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="lg:col-span-2 space-y-6">
                <div v-if="galat" class="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 font-medium flex items-start gap-3 shadow-sm">
                    <i class="pi pi-exclamation-triangle mt-0.5"></i>
                    <span>{{ galat }}</span>
                </div>

                <section class="bg-white border border-slate-200 rounded-[24px] p-5 md:p-6 shadow-sm">
                    <h3 class="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 border-b border-slate-100 pb-2">1. Identifikasi Sumber WIP</h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div class="flex flex-col gap-2">
                            <label class="text-xs font-bold text-slate-500 uppercase">Target Legal Entity</label>
                            <select v-model="form.entitas_id" required class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-slate-800 text-slate-800">
                                <option value="" disabled>Pilih Entitas...</option>
                                <option v-for="ent in daftarEntitas" :key="ent.id" :value="ent.id">{{ ent.nama }}</option>
                            </select>
                        </div>
                        <div class="flex flex-col gap-2">
                            <label class="text-xs font-bold text-slate-500 uppercase">Sumber Tangki</label>
                            <select v-model="form.jenis_sumber" required class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-slate-800 text-slate-800 font-bold text-blue-700">
                                <option value="MIXING">Proses MIXING</option>
                                <option value="BLENDING">Proses BLENDING</option>
                            </select>
                        </div>
                        <div class="flex flex-col gap-2">
                            <label class="text-xs font-bold text-slate-500 uppercase">Pilih Tangki / Batch</label>
                            <select v-model="form.batch_id" required class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-slate-800 text-slate-800">
                                <option value="" disabled>Pilih Tangki Tersedia...</option>
                                <option v-for="b in batchDifilter" :key="b.id" :value="b.id">
                                    {{ b.label_dropdown }}
                                </option>
                            </select>
                        </div>
                    </div>
                </section>

                <section class="bg-white border border-slate-200 rounded-[24px] p-5 md:p-6 shadow-sm">
                    <h3 class="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 border-b border-slate-100 pb-2">2. Konversi Produk & Aset Kemasan</h3>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
                        <div class="flex flex-col gap-2">
                            <label class="text-xs font-bold text-slate-500 uppercase">Produk Jadi (Finished Goods)</label>
                            <Dropdown 
                                v-model="form.produk_id" 
                                :options="daftarProduk" 
                                filter 
                                optionLabel="label_display" 
                                placeholder="Pilih Produk..." 
                                class="w-full"
                                scrollHeight="160px"
                                appendTo="body"
                            /> 
                        </div>

                        <div class="flex flex-col gap-2">
                            <label class="text-xs font-bold text-slate-500 uppercase">Aset Kemasan Utama</label>
                                <Dropdown 
                                    v-model="form.kemasan_id" 
                                    :options="daftarKemasan" 
                                    filter 
                                    optionLabel="label_dropdown" 
                                    optionValue="id" 
                                    placeholder="Pilih Kemasan..." 
                                    class="w-full"
                                    scrollHeight="160px"
                                    appendTo="body"
                                />
                        </div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
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

                    <div class="p-4 bg-blue-50 border border-blue-100 rounded-xl mt-5">
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

            <div class="space-y-6">
                <div class="bg-slate-900 border border-slate-800 rounded-[24px] p-6 shadow-xl relative overflow-hidden h-full flex flex-col">
                    <div class="absolute -right-6 -bottom-6 text-slate-800 opacity-50 pointer-events-none">
                        <i class="pi pi-receipt" style="font-size: 8rem;"></i>
                    </div>

                    <h3 class="text-xs font-bold text-amber-500 uppercase tracking-widest mb-6 border-b border-slate-700 pb-2 relative z-10">COST Valuasi</h3>

                    <div class="space-y-4 relative z-10 flex-1">
                        <div v-if="pratinjau.pesan && !pratinjau.valid" class="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-400 font-medium">
                            <i class="pi pi-times-circle mr-1"></i> {{ pratinjau.pesan }}
                        </div>
                        <div v-else-if="pratinjau.menghabiskan" class="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-xs text-amber-400 font-medium">
                            <i class="pi pi-info-circle mr-1"></i> Penarikan ini menghabiskan sisa batch.
                        </div>

                        <div class="flex justify-between items-center border-b border-slate-700 pb-3 mt-4">
                            <span class="text-xs text-slate-400">Status Kalkulasi</span>
                            <span v-if="pratinjau.valid" class="text-xs font-bold text-emerald-400 flex items-center gap-1"><i class="pi pi-check-circle"></i> Valid</span>
                            <span v-else class="text-xs font-bold text-slate-500">Menunggu Input</span>
                        </div>

                        <div class="flex justify-between items-center border-b border-slate-700 pb-3 mt-4">
                            <span class="text-xs text-slate-400">COST WIP (dari Batch)</span>
                            <span class="text-sm font-mono text-slate-200">{{ pratinjau.valid ? `Rp ${angka(nilaiHppWip)}` : '—' }}</span>
                        </div>

                        <div class="flex justify-between items-center border-b border-slate-700 pb-3 mt-4">
                            <span class="text-xs text-slate-400">Cost Packaging</span>
                            <span class="text-sm font-mono text-slate-200">Rp {{ angka(totalNilaiKemasan) }}</span>
                        </div>

                        <div class="pt-4">
                            <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">
                                Total Cost
                                <span v-if="!pratinjau.valid" class="text-amber-500 normal-case font-medium tracking-normal ml-1">(menunggu kalkulasi)</span>
                            </span>
                            <span class="text-3xl font-black text-white block">{{ pratinjau.valid ? `Rp ${angka(totalNilaiAbsorpsi)}` : '—' }}</span>
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