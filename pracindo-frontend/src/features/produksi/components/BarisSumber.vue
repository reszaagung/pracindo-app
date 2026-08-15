<script setup>
import { computed } from 'vue'
import { formatRp, formatHarga, formatKg } from '@/utils/uang'
import { SUMBER } from '../constants'

const props = defineProps({
    modelValue: Object,
    opsiRaw: Array,
    opsiBatch: Array,
    valuasi: Object,   // Datang dari pratinjau
    galat: String,     // Pesan galat spesifik untuk baris ini
    bisaHapus: Boolean
})

const emit = defineEmits(['update:modelValue', 'hapus'])

// Proxy untuk v-model dua arah
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
    <div class="baris-sumber bg-white border p-3 rounded-md mb-3 transition-colors"
        :class="galat ? 'border-red-400 bg-red-50' : 'border-gray-200'">
        <div class="flex flex-wrap items-start gap-3">

            <!-- Toggle RAW / WIP -->
            <div class="w-24">
                <select :value="baris.sumber" @change="gantiSumber($event.target.value)"
                    class="w-full border-gray-300 rounded shadow-sm text-sm">
                    <option :value="SUMBER.RAW">RAW</option>
                    <option :value="SUMBER.WIP">WIP</option>
                </select>
            </div>

            <!-- Selector Material/Batch -->
            <div class="flex-1 min-w-[200px]">
                <select v-if="baris.sumber === SUMBER.RAW" v-model="baris.raw"
                    class="w-full border-gray-300 rounded shadow-sm text-sm" :class="{ 'border-red-500': galat }">
                    <option :value="null">— Pilih Material RAW —</option>
                    <option v-for="r in opsiRaw" :key="r.id" :value="r.id">
                        {{ r.nama }} (Sisa: {{ formatKg(r.saldo_qty) }})
                    </option>
                </select>

                <select v-else v-model="baris.batch_sumber" class="w-full border-gray-300 rounded shadow-sm text-sm"
                    :class="{ 'border-red-500': galat }">
                    <option :value="null">— Pilih Batch WIP —</option>
                    <option v-for="b in opsiBatch" :key="b.id" :value="b.id">
                        [{{ b.tangki_kode }}] {{ b.nomor }} - {{ b.nama_hasil }} (Sisa: {{ formatKg(b.sisa_qty) }})
                    </option>
                </select>
            </div>

            <!-- Input Qty -->
            <div class="w-40 relative">
                <input v-model="baris.qty_kg" type="text" inputmode="decimal" placeholder="0.000"
                    class="w-full border-gray-300 rounded shadow-sm text-sm pr-10 text-right"
                    :class="{ 'border-red-500': galat }" />
                <span class="absolute right-3 top-2 text-xs text-gray-500 font-medium">Kg</span>
            </div>

            <!-- Tombol Hapus -->
            <button type="button"
                class="text-red-500 hover:text-red-700 disabled:opacity-30 disabled:cursor-not-allowed p-2"
                :disabled="!bisaHapus" @click="$emit('hapus')" title="Hapus baris">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
            </button>
        </div>

        <!-- Feedback Area: Menampilkan Valuasi atau Galat -->
        <div class="mt-2 text-sm flex items-center justify-between">

            <div v-if="galat" class="text-red-600 font-medium text-xs">
                {{ galat }}
            </div>

            <div v-else-if="valuasi" class="flex gap-4 items-center text-gray-600 pl-28">
                <span>Nilai: <strong class="text-gray-800">{{ formatRp(valuasi.nilai) }}</strong></span>
                <span class="text-xs">({{ formatHarga(valuasi.harga_per_kg) }})</span>

                <span v-if="valuasi.menghabiskan"
                    class="ml-2 bg-amber-500 text-white px-2 py-0.5 rounded text-xs font-bold tracking-wide shadow-sm animate-pulse">
                    AKAN HABIS
                </span>
            </div>

            <div v-else class="text-gray-400 text-xs italic pl-28">
                Menunggu input...
            </div>
        </div>
    </div>
</template>