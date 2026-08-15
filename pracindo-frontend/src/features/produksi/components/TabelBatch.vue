<script setup>
import { formatKg } from '@/utils/uang'
import { STATUS_BATCH, WARNA_STATUS } from '../constants'

defineProps({
    baris: { type: Array, required: true },
    memuat: { type: Boolean, default: false }
})

defineEmits(['detail', 'posting', 'hapus'])

// Fungsi sederhana format tanggal
const formatWaktu = (iso) => {
    if (!iso) return '-'
    return new Date(iso).toLocaleString('id-ID', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    })
}
</script>

<template>
    <div class="bg-white border rounded-lg shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
            <table class="w-full text-sm text-left text-gray-600">
                <thead class="text-xs text-gray-700 uppercase bg-gray-50 border-b">
                    <tr>
                        <th class="px-4 py-3">Waktu</th>
                        <th class="px-4 py-3">Nomor Batch</th>
                        <th class="px-4 py-3">Tangki Tujuan</th>
                        <th class="px-4 py-3">Hasil</th>
                        <th class="px-4 py-3 text-right">Qty (Kg)</th>
                        <th class="px-4 py-3 text-center">Status</th>
                        <th class="px-4 py-3 text-right">Aksi</th>
                    </tr>
                </thead>
                <tbody v-if="memuat">
                    <tr>
                        <td colspan="7" class="px-4 py-8 text-center text-gray-400">
                            <span class="animate-pulse">Memuat data riwayat...</span>
                        </td>
                    </tr>
                </tbody>
                <tbody v-else-if="baris.length === 0">
                    <tr>
                        <td colspan="7" class="px-4 py-8 text-center text-gray-400 italic">
                            Tidak ada riwayat batch yang sesuai dengan filter.
                        </td>
                    </tr>
                </tbody>
                <tbody v-else>
                    <tr v-for="b in baris" :key="b.id" class="border-b hover:bg-gray-50">
                        <td class="px-4 py-3">{{ formatWaktu(b.waktu) }}</td>
                        <td class="px-4 py-3 font-medium text-gray-900">
                            {{ b.nomor || 'DRAFT' }}
                            <div class="text-[10px] text-gray-500 font-bold uppercase">{{ b.jenis }}</div>
                        </td>
                        <td class="px-4 py-3">{{ b.tangki_kode }}</td>
                        <td class="px-4 py-3 text-gray-800">{{ b.nama_hasil }}</td>
                        <td class="px-4 py-3 text-right font-medium">{{ formatKg(b.qty_hasil) }}</td>
                        <td class="px-4 py-3 text-center">
                            <span class="px-2.5 py-1 text-[10px] font-bold uppercase rounded-md shadow-sm border"
                                :class="WARNA_STATUS[b.status]">
                                {{ b.status }}
                            </span>
                        </td>
                        <td class="px-4 py-3 text-right space-x-2">

                            <!-- Aksi untuk DRAFT -->
                            <template v-if="b.status === STATUS_BATCH.DRAFT">
                                <button @click="$emit('hapus', b.id)"
                                    class="text-red-600 hover:text-red-800 font-medium text-xs border border-red-200 px-2 py-1 rounded">
                                    Hapus
                                </button>
                                <button @click="$emit('posting', b.id)"
                                    class="text-blue-600 hover:text-blue-800 font-medium text-xs border border-blue-200 bg-blue-50 px-2 py-1 rounded">
                                    Posting
                                </button>
                            </template>

                            <!-- Aksi untuk POSTED / VOID -->
                            <template v-else>
                                <button @click="$emit('detail', b.id)"
                                    class="text-gray-600 hover:text-gray-900 font-medium text-xs border bg-gray-100 px-2 py-1 rounded">
                                    Rincian
                                </button>
                            </template>

                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>