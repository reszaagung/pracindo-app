<script setup>
import { formatKg, formatRp } from '@/utils/uang'

defineProps({
    data: {
        type: Object,
        required: true
    }
})
</script>

<template>
    <div class="bg-white border rounded-lg shadow-sm overflow-hidden flex flex-col h-full">
        <div class="bg-gray-50 border-b p-4 flex justify-between items-start">
            <div>
                <h2 class="text-xl font-bold text-gray-800">{{ data.tangki }}</h2>
            </div>
            <div v-if="data.harga_beragam"
                class="bg-amber-100 text-amber-800 text-xs font-bold px-2.5 py-1 rounded-md border border-amber-200 flex items-center gap-1 cursor-help"
                title="Tagihan packing akan bervariasi bergantung pada batch mana yang ditarik operator.">
                <span>⚠️ Harga Beragam</span>
            </div>
        </div>

        <div class="p-4 grid grid-cols-2 gap-4 border-b bg-white">
            <div>
                <p class="text-xs text-gray-500 font-medium uppercase tracking-wider">Total Isi Fisik</p>
                <p class="text-lg font-semibold text-gray-900">{{ formatKg(data.qty) }}</p>
            </div>
            <div>
                <p class="text-xs text-gray-500 font-medium uppercase tracking-wider">Rata-rata HPP</p>
                <p class="text-lg font-semibold text-gray-900">{{ formatRp(data.harga_rata) }}<span
                        class="text-sm font-normal text-gray-500">/Kg</span></p>
            </div>
        </div>

        <div class="p-4 flex-1 bg-gray-50">
            <h3 class="text-sm font-semibold text-gray-700 mb-3 border-b pb-1">
                Rincian Batch ({{ data.batches.length }})
            </h3>

            <div v-if="data.batches.length === 0" class="text-sm text-gray-400 italic text-center py-4">
                Tangki kosong.
            </div>

            <ul v-else class="space-y-3">
                <li v-for="b in data.batches" :key="b.id"
                    class="bg-white p-3 rounded border text-sm shadow-sm relative">
                    <div class="flex justify-between items-start mb-1">
                        <span class="font-bold text-blue-800">{{ b.nomor }}</span>
                        <span class="text-xs font-medium text-gray-500">{{ b.jenis }}</span>
                    </div>
                    <p class="text-gray-700 font-medium truncate" :title="b.nama_hasil">{{ b.nama_hasil }}</p>
                    <div class="mt-2 flex justify-between text-gray-600">
                        <span>Sisa: <strong>{{ formatKg(b.sisa_qty) }}</strong></span>
                        <span>HPP: <strong>{{ formatRp(b.harga_per_kg) }}</strong></span>
                    </div>
                    <div v-if="b.kelebihan"
                        class="absolute -top-2 -right-2 bg-red-500 text-white text-[10px] px-1.5 py-0.5 rounded shadow">
                        KELEBIHAN
                    </div>
                </li>
            </ul>
        </div>
    </div>
</template>
