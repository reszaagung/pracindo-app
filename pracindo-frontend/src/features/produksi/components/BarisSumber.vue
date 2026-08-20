<!-- src/features/produksi/components/BarisSumber.vue -->

<script setup>
import { computed } from 'vue'
import { formatRp, formatHarga, formatKg } from '@/utils/uang'
import { SUMBER } from '../constants'

const props = defineProps({
    modelValue: Object,
    opsiRaw: Array,
    opsiBatch: Array,
    valuasi: Object,
    galat: String,
    bisaHapus: Boolean
})

const emit = defineEmits(['update:modelValue', 'hapus'])

const baris = computed({
    get: () => props.modelValue,
    set: (val) => emit('update:modelValue', val)
})

function gantiSumber(jenis) {
    baris.value.sumber = jenis
    baris.value.raw = null
    baris.value.batch_sumber = null
}
</script>

<template>
    <div class="relative bg-white border p-3 md:p-4 rounded-lg shadow-sm mb-3 transition-colors hover:border-blue-300"
        :class="galat ? 'border-red-400 bg-red-50/30' : 'border-slate-200'">
        <button type="button" v-if="bisaHapus"
            class="md:hidden absolute top-3 right-3 p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
            @click="$emit('hapus')">
            <i class="pi pi-trash text-sm"></i>
        </button>

        <div class="flex flex-col md:flex-row items-start md:items-center gap-3 md:gap-4">
            <div class="w-full md:w-32 shrink-0">
                <label class="text-xs font-semibold text-slate-600 mb-1 block md:hidden">Jenis Sumber</label>
                <select :value="baris.sumber" @change="gantiSumber($event.target.value)"
                    class="w-full border-slate-300 rounded-md shadow-sm text-sm py-1.5 px-3 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 bg-white transition-colors">
                    <option :value="SUMBER.RAW">RAW (Bahan)</option>
                    <option :value="SUMBER.WIP">WIP (Batch)</option>
                </select>
            </div>

            <div class="w-full flex-1">
                <label class="text-xs font-semibold text-slate-600 mb-1 block md:hidden">Pilih Komponen</label>
                <select v-if="baris.sumber === SUMBER.RAW" v-model="baris.raw"
                    class="w-full border-slate-300 rounded-md shadow-sm text-sm py-1.5 px-3 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 bg-white transition-colors"
                    :class="{ 'border-red-500 focus:border-red-500 focus:ring-red-500 bg-red-50': galat }">
                    <option :value="null">-- Pilih Material RAW --</option>
                    <option v-for="r in opsiRaw" :key="r.produk_id" :value="r.produk_id">
                        {{ r.produk_nama }} (Sisa: {{ formatKg(r.qty_kg) }})
                    </option>
                </select>
                <select v-else v-model="baris.batch_sumber"
                    class="w-full border-slate-300 rounded-md shadow-sm text-sm py-1.5 px-3 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 bg-white transition-colors"
                    :class="{ 'border-red-500 focus:border-red-500 focus:ring-red-500 bg-red-50': galat }">
                    <option :value="null">-- Pilih Batch WIP --</option>
                    <option v-for="b in opsiBatch" :key="b.id" :value="b.id">
                        [{{ b.tangki_kode }}] {{ b.nomor }} - {{ b.nama_hasil }} (Sisa: {{ formatKg(b.sisa_qty) }})
                    </option>
                </select>
            </div>

            <div class="w-full md:w-36 shrink-0">
                <label class="text-xs font-semibold text-slate-600 mb-1 block md:hidden">Kuantitas (Kg)</label>
                <div class="relative">
                    <input v-model="baris.qty_kg" type="text" inputmode="decimal" pattern="[0-9]*[.,]?[0-9]*" placeholder="0.000"
                        class="w-full border-slate-300 rounded-md shadow-sm text-sm py-1.5 pr-8 pl-3 text-right focus:border-blue-500 focus:ring-1 focus:ring-blue-500 bg-white transition-all placeholder:text-slate-300"
                        :class="{ 'border-red-500 focus:border-red-500 focus:ring-red-500': galat }" />
                    <div class="absolute inset-y-0 right-0 flex items-center pr-2.5 pointer-events-none">
                        <span class="text-xs font-medium text-slate-400">Kg</span>
                    </div>
                </div>
            </div>

            <button type="button" v-if="bisaHapus"
                class="hidden md:flex shrink-0 items-center justify-center w-8 h-8 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded border border-transparent hover:border-red-100 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                @click="$emit('hapus')">
                <i class="pi pi-trash"></i>
            </button>
            <div v-else class="hidden md:block w-8 shrink-0"></div>
        </div>

        <div class="mt-3 pt-2 border-t border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-1.5 md:pl-[144px]">
            <div v-if="galat" class="text-red-600 font-medium text-xs flex items-center gap-1.5">
                <i class="pi pi-exclamation-circle text-red-500"></i> {{ galat }}
            </div>
            <div v-else-if="valuasi" class="flex flex-wrap gap-x-3 gap-y-1 items-center text-slate-600">
                <span class="text-xs">Nilai: <strong class="text-slate-900 text-sm tracking-tight">{{ formatRp(valuasi.nilai) }}</strong></span>
                <span class="text-[11px] text-slate-500">({{ formatHarga(valuasi.harga_per_kg) }})</span>
                <span v-if="valuasi.menghabiskan"
                    class="bg-amber-100 text-amber-800 border border-amber-200 px-1.5 py-0.5 rounded text-[10px] font-bold shadow-sm animate-pulse">
                    AKAN HABIS
                </span>
            </div>
            <div v-else class="text-slate-400 text-xs italic flex items-center gap-1.5">
                <i class="pi pi-pencil text-[10px]"></i> Menunggu input...
            </div>
        </div>
    </div>
</template>
