<script setup>
import { onMounted } from 'vue'
import { useAkuntansi } from '../composables/useAkuntansi'

const { akunList, fetchAkun, isLoading } = useAkuntansi()

onMounted(() => {
    fetchAkun()
})
</script>

<template>
    <div class="p-6 max-w-7xl mx-auto space-y-6">
        <header class="flex justify-between items-end border-b border-slate-200 pb-4">
            <div>
                <p class="text-sm text-slate-500 mb-1">Akuntansi</p>
                <h1 class="text-2xl font-bold text-slate-800">Daftar Akun Buku Besar</h1>
            </div>
        </header>

        <div class="bg-white rounded-[20px] shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 overflow-hidden">
            <table class="min-w-full divide-y divide-slate-200">
                <thead class="bg-slate-50">
                    <tr>
                        <th class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Kode</th>
                        <th class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Nama Akun</th>
                        <th class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Kategori</th>
                        <th class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Saldo Normal</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                    <tr v-if="isLoading" class="bg-white">
                        <td colspan="4" class="px-6 py-8 text-center text-slate-400">Memuat data...</td>
                    </tr>
                    <tr v-else-if="akunList.length === 0" class="bg-white">
                        <td colspan="4" class="px-6 py-8 text-center text-slate-400">Belum ada akun yang didaftarkan untuk cabang ini.</td>
                    </tr>
                    <tr v-for="akun in akunList" :key="akun.id" class="hover:bg-slate-50 transition-colors">
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-bold text-slate-800">{{ akun.kode }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-700">{{ akun.nama }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600">{{ akun.kategori_nama }}</td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <span :class="akun.tipe_saldo === 'DEBIT' ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'" class="px-3 py-1 rounded-md text-xs font-bold">
                                {{ akun.tipe_saldo }}
                            </span>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>
