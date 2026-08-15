<script setup>
import { formatKg } from '@/utils/uang'

defineProps({
    komposisi: {
        type: Object,
        required: true
    }
})
</script>

<template>
    <div class="bg-white border rounded-lg shadow-sm overflow-hidden">
        <div class="bg-blue-50 border-b p-4">
            <h3 class="font-bold text-blue-900 text-lg">Komposisi Akar (Raw Material)</h3>
            <p class="text-sm text-blue-800 mt-2 bg-blue-100 p-2 rounded border border-blue-200">
                <strong>Catatan:</strong> {{ formatKg(komposisi.qty_hasil) }} hasil ini pada awalnya ditarik dari {{
                    formatKg(komposisi.total_raw_kg) }} raw material.
                Selisihnya adalah penyusutan/tekor dari batch-batch induk yang menguap secara sah di proses sebelumnya.
                Ini <strong>bukan anomali</strong> atau data ganda.
            </p>
        </div>

        <table class="w-full text-sm text-left text-gray-600">
            <thead class="text-xs text-gray-700 uppercase bg-gray-50 border-b">
                <tr>
                    <th class="px-4 py-3">Material (RAW)</th>
                    <th class="px-4 py-3 text-right">Qty Terserap (Kg)</th>
                </tr>
            </thead>
            <tbody>
                <tr v-if="!komposisi.raw || komposisi.raw.length === 0">
                    <td colspan="2" class="px-4 py-8 text-center text-gray-400 italic">
                        Gagal mengurai komposisi raw material.
                    </td>
                </tr>
                <tr v-for="r in komposisi.raw" :key="r.id" class="border-b hover:bg-gray-50">
                    <td class="px-4 py-3 font-medium text-gray-900">{{ r.nama }}</td>
                    <td class="px-4 py-3 text-right font-bold text-gray-700">{{ formatKg(r.qty_kg) }}</td>
                </tr>
            </tbody>
        </table>
    </div>
</template>