<template>
    <div class="p-6 h-screen overflow-y-auto bg-gray-50">
        <h1 class="text-2xl font-bold mb-6 text-gray-800">Riwayat Penjualan</h1>
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div class="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
                <input type="text" placeholder="Cari Nomor Struk..."
                    class="border border-gray-300 rounded-lg px-4 py-2 w-1/3 focus:ring-blue-500 focus:border-blue-500">
            </div>
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-100">
                    <tr>
                        <th class="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase">Waktu</th>
                        <th class="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase">No. Struk</th>
                        <th class="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase">Total</th>
                        <th class="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase">Metode</th>
                        <th class="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase">Status</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-if="riwayat.length === 0">
                        <td colspan="5" class="px-6 py-8 text-center text-gray-500">Belum ada riwayat transaksi.</td>
                    </tr>
                    <tr v-for="trx in riwayat" :key="trx.nomor_struk" class="hover:bg-gray-50">
                        <td class="px-6 py-4 text-sm text-gray-600">{{ trx.waktu }}</td>
                        <td class="px-6 py-4 text-sm font-semibold text-gray-800">{{ trx.nomor_struk }}</td>
                        <td class="px-6 py-4 text-sm font-bold text-green-600">Rp {{ trx.grand_total }}</td>
                        <td class="px-6 py-4 text-sm text-gray-600">{{ trx.metode_bayar }}</td>
                        <td class="px-6 py-4 text-sm">
                            <span class="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                                {{ trx.status }}
                            </span>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRetail } from '../composables/useRetail'

const { riwayat, fetchRiwayat } = useRetail()

onMounted(() => {
    fetchRiwayat()
})
</script>