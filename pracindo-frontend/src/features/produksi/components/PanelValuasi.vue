<script setup>
import { formatHarga, formatKg, formatRp } from '@/utils/uang'

defineProps({
    pratinjau: Object,
    memuat: Boolean,
    galatUmum: Array
})
</script>

<template>
    <section class="panel-valuasi bg-white border rounded-md p-4 shadow-sm" :class="{ 'opacity-70': memuat }">
        <div v-if="!pratinjau" class="kosong text-gray-500 italic text-center py-4">
            Tambahkan sumber untuk melihat perhitungan nilai dan peringatan.
        </div>

        <template v-else-if="pratinjau.valid">
            <dl class="space-y-2 text-sm">
                <div class="flex justify-between">
                    <dt class="text-gray-600">Total Input</dt>
                    <dd class="font-medium text-right">
                        {{ formatKg(pratinjau.total_qty_input) }} · {{ formatRp(pratinjau.total_nilai_input) }}
                    </dd>
                </div>

                <div class="flex justify-between border-b pb-2">
                    <dt class="text-gray-600">Tekor</dt>
                    <dd class="text-right">{{ formatKg(pratinjau.tekor_kg) }}</dd>
                </div>

                <div v-if="pratinjau.nilai_susut !== '0.00'" class="flex justify-between text-amber-700">
                    <dt>Susut diakui</dt>
                    <dd class="text-right">{{ formatRp(pratinjau.nilai_susut) }}</dd>
                </div>

                <div class="flex justify-between pt-2 font-semibold text-base">
                    <dt>Hasil Masuk Tangki</dt>
                    <dd class="text-right text-blue-700">
                        {{ formatKg(pratinjau.qty_hasil) }} · {{ formatRp(pratinjau.nilai_hasil) }}
                    </dd>
                </div>

                <div class="flex justify-between font-bold text-lg mt-1">
                    <dt>HPP Baru</dt>
                    <dd class="text-right">{{ formatHarga(pratinjau.harga_hasil_per_kg) }}</dd>
                </div>
            </dl>

            <ul v-if="pratinjau.peringatan?.length" class="mt-4 space-y-1">
                <li v-for="(p, i) in pratinjau.peringatan" :key="i"
                    class="text-amber-600 bg-amber-50 p-2 text-xs rounded border border-amber-200">
                    ⚠️ {{ p }}
                </li>
            </ul>

            <p class="mt-4 text-xs text-gray-400 text-center border-t pt-3">
                Nilai hanya berpindah ke dalam tangki. Tidak ada hutang atau piutang pihak manapun yang tersentuh.
            </p>
        </template>

        <ul v-else class="galat mt-2 space-y-1">
            <li v-for="(g, i) in galatUmum" :key="i"
                class="text-red-600 bg-red-50 p-2 text-sm rounded border border-red-200">
                🛑 {{ g }}
            </li>
        </ul>
    </section>
</template>